# Runbook - publicar a API

Passo a passo para publicar esta API num servidor próprio. Padrão de infra: nginx no host, TLS por
certbot (DNS-01), imagem no GHCR, deploy por GitHub Actions. Faça uma vez o provisionamento (seções
1 a 6); depois o fluxo `dev -> main` republica sozinho (seção 7).

> [!NOTA]
> Substitua os placeholders abaixo pelos valores do seu ambiente (nada disso é versionado):
> - `<DOMINIO>` - domínio público da API (ex.: `api.exemplo.com`)
> - `<VPS_HOST>` / `<VPS_PORT>` / `<VPS_USER>` - acesso SSH ao servidor
> - `<APP_DIR>` - diretório da app no servidor (ex.: `/srv/app`)
> - `<DNS_CRED>` - arquivo de credenciais do provedor DNS para o certbot
>
> Porta interna do container: `8000` (exposta só em loopback; o nginx faz o TLS).

## 1. DNS

Criar um registro **A** para `<DOMINIO>` apontando para o IP do servidor. Se usar um proxy/CDN na
frente, configure o modo de SSL como **Full (strict)** e ative o redirecionamento para HTTPS, para o
tráfego CDN -> origem ser sempre criptografado.

## 2. Repositório e imagem (GitHub / GHCR)

- No GitHub do repo, em **Settings > Secrets and variables > Actions**, criar os secrets
  `VPS_HOST`, `VPS_PORT`, `VPS_USER`, `VPS_SSH_KEY` (chave privada de deploy) e a variável
  `DEPLOY_DIR` (o `<APP_DIR>`).
- O workflow publica a imagem em `ghcr.io/<owner>/<repo>`. Após o primeiro build, deixar o pacote
  **público** (assim o servidor puxa sem login no GHCR) ou autenticar o Docker do servidor no GHCR.

## 3. Pasta da app e .env no servidor

```bash
ssh -p <VPS_PORT> <VPS_USER>@<VPS_HOST>
sudo mkdir -p <APP_DIR>
sudo chown <VPS_USER>:<VPS_USER> <APP_DIR>
cd <APP_DIR>

# Criar data/ e media/ e dar dono ao UID do container (10001, definido no Dockerfile).
mkdir -p data media
sudo chown -R 10001:10001 data media
# O nginx (www-data) precisa ler o media/ para servir as imagens.
sudo chmod 755 media

# Criar o .env (use o .env.example do repo como base). DEBUG=0 em produção.
touch .env && chmod 600 .env
# editar .env: DJANGO_SECRET_KEY (longa e aleatória), DJANGO_DEBUG=0,
# DJANGO_ALLOWED_HOSTS=<DOMINIO>,localhost,127.0.0.1
#   (mantenha localhost: o healthcheck do container acessa http://localhost:8000/),
# DJANGO_CSRF_TRUSTED_ORIGINS=https://<DOMINIO>, CORS_ALLOW_ALL_ORIGINS=1,
# DJANGO_TIME_ZONE=<fuso horário do servidor, ex.: America/Sao_Paulo>
```

Copiar o `deploy/docker-compose.prod.yaml` do repo para `<APP_DIR>/docker-compose.yaml`.

## 4. Certificado TLS (certbot DNS-01)

Emitir o certificado (executar sozinho, sem paralelizar - o certbot usa lock):

```bash
sudo certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials <DNS_CRED> \
  -d <DOMINIO> --non-interactive --agree-tos
```

(Use o plugin DNS do seu provedor; `--dns-cloudflare` é só um exemplo.)

## 5. Vhost do nginx

Copiar `deploy/nginx-soulcroheapi.conf` para `/etc/nginx/sites-available/<DOMINIO>.conf` (ajustando
`server_name`, caminhos do cert e o `alias` do `/media/` para `<APP_DIR>/media/`), habilitar e
recarregar:

```bash
sudo ln -sf /etc/nginx/sites-available/<DOMINIO>.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## 6. Primeiro deploy e dados iniciais

Subir o container (ou deixar o GitHub Actions fazer - ver seção 7). Depois, criar o usuário
administrador, semear os produtos e gerar o token:

```bash
cd <APP_DIR>
docker compose pull && docker compose up -d

# Usuário do admin (login em /admin/)
docker compose exec api python manage.py createsuperuser

# Os 6 produtos de exemplo, com imagens
docker compose exec api python manage.py seed_produtos
```

Gerar o **token** que vai no site cliente: em `https://<DOMINIO>/admin/`, seção **Tokens > Add**,
escolher um usuário e salvar. A chave gerada é o token a ser colado no site (cabeçalho
`Authorization: Token <chave>` no POST do formulário de contato).

## 7. Deploys seguintes (fluxo automático dev -> main)

A entrega é por branch (workflows em `.github/workflows/`):

```
push em dev -> ci.yml roda os testes
            -> (se verde) merge fast-forward em main
            -> chama deploy.yml (reutilizável): build -> push GHCR -> SSH no servidor
               (docker compose pull && up -d + healthcheck)
            -> cria tag/release semver
```

As migrações rodam sozinhas no start do container (`entrypoint.sh`).

## 8. Verificação

```bash
curl -sS https://<DOMINIO>/healthz/            # {"status": "ok"}
curl -sS https://<DOMINIO>/produtos/           # lista JSON dos produtos
```

O admin abre em `https://<DOMINIO>/admin/`.

## 9. Fail2ban (endurecimento)

O vhost grava um log dedicado (`/var/log/nginx/soulcroheapi.access.log`). A partir do repositório,
copie o filtro e o jail e recarregue o Fail2ban:

```bash
sudo cp deploy/fail2ban/filter-soulcroheapi.conf /etc/fail2ban/filter.d/soulcroheapi.conf
sudo cp deploy/fail2ban/jail-soulcroheapi.conf   /etc/fail2ban/jail.d/soulcroheapi.conf
sudo systemctl reload fail2ban
sudo fail2ban-client status soulcroheapi
```

O jail bane (via iptables) IPs com muitos 401/403/404 num curto intervalo. Se a API ficar atrás de
um CDN/proxy, mantenha os ranges do proxy no `ignoreip` (para nunca bani-lo); assim o jail protege
contra **abuso direto ao IP de origem**. Abuso vindo pelo proxy deve ser tratado no WAF/rate limiting
do próprio proxy.

## Notas

- **Permissão dos volumes:** o container roda como UID `10001`. Se aparecer erro de permissão ao
  gravar o banco ou as imagens, confira `sudo chown -R 10001:10001 data media`.
- **Imagens dos produtos:** ficam em `<APP_DIR>/media/produtos/` e são servidas pelo nginx em
  `/media/`. A API devolve a URL completa (`https://.../media/...`).
- **CORS aberto:** liberado a qualquer origem por enquanto. Quando o site cliente tiver um domínio
  fixo, dá para restringir trocando `CORS_ALLOW_ALL_ORIGINS` por uma allowlist.
- **Endurecimento opcional do admin:** o `/admin/` fica público. Para reduzir risco de força bruta,
  considere (a) restringir por IP no nginx (`location /admin/ { allow <SEU_IP>; deny all; ... }`),
  ou (b) instalar `django-axes` (bloqueia IP após N tentativas). O formulário de contato já tem
  limite de envios (throttle) configurado na própria API.
- **Branch protection:** o `ci.yml` faz push do merge em `main` com o `GITHUB_TOKEN`. Se você
  habilitar regras de proteção na `main` (exigir PR, restringir push), adicione o
  `github-actions[bot]` como ator com bypass, senão o merge automático falhará com 403.

