# Soul Crochê API

API de exemplo da loja fictícia **Soul Crochê**, criada como projeto educacional. Construída em
**Django + Django REST Framework**, dockerizada, publicada sob um domínio próprio (HTTPS). O
front-end **consome** os produtos e usa o **admin do Django** para o CRUD.

## Endpoints

| Rota | Método | Acesso | Descrição |
|---|---|---|---|
| `/` | GET | - | **403 Forbidden** (não lista endpoints) |
| `/produtos/` | GET | público | Catálogo (paginado) |
| `/produtos/{id}/` | GET | público | Detalhe de um produto |
| `/categorias/` | GET | público | Categorias |
| `/contatos/` | POST | token | Recebe o formulário de contato |
| `/admin/` | - | login | Área administrativa (CRUD) |
| `/healthz/` | GET | público | Verificação de saúde |

- **Busca/filtro/ordenação:** `?search=`, `?categoria__slug=`, `?ordering=preco`.
- **Paginação:** 10 itens por página (`PAGE_SIZE` no `.env`); resposta com `count`/`next`/`results`.
- **Autenticação:** leitura pública; o POST de contato exige `Authorization: Token <chave>` (token
  gerado no admin).
- **Apenas JSON:** a Browsable API (versão web) está desligada; a raiz `/` retorna 403.

## Rodar localmente

```bash
cp .env.example .env          # ajuste DJANGO_DEBUG=1 para desenvolvimento
docker compose up --build     # http://localhost:8000
docker compose exec web python manage.py seed_produtos     # 6 produtos de exemplo
docker compose exec web python manage.py createsuperuser   # acesso ao /admin/
```

## Stack e estrutura

- `config/` - projeto Django (settings, urls, wsgi).
- `loja/` - app com os modelos (`Produto`, `Categoria`, `Contato`), serializers, views e o comando
  `seed_produtos`.
- `Dockerfile`, `docker-compose.yml` (dev), `entrypoint.sh`.
- `deploy/` - `docker-compose.prod.yaml`, `nginx-soulcroheapi.conf` e o **`RUNBOOK.md`** (passo a
  passo de publicação na VPS).
- `.github/workflows/deploy.yml` - CI: build/push no GHCR + deploy por SSH.

## Testes

```bash
pip install -r requirements-dev.txt
pytest                       # ou: python manage.py test
```

## Publicação

Ver `deploy/RUNBOOK.md`. O fluxo é por branch:

- push em **`dev`** -> roda os testes (`.github/workflows/ci.yml`);
- se passam, faz **merge automático em `main`** -> **deploy** na VPS (build + push no GHCR + SSH);
- a cada deploy, uma **tag/release** semver é criada automaticamente.
