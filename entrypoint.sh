#!/bin/sh
# Prepara o app (migrações + estáticos) e então executa o comando recebido
# (por padrão o Gunicorn, definido no CMD do Dockerfile).
set -e

# Garante os diretórios de banco/mídia/estáticos (em dev o bind mount esconde
# os que foram criados no build da imagem).
mkdir -p data media staticfiles

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
