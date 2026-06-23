# ---- estágio de build: instala as dependências num prefixo isolado ----
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- estágio final: imagem enxuta com o código e as dependências ----
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

# Usuário não-root com UID fixo (10001) - facilita o chown dos volumes na VPS.
RUN addgroup --system --gid 10001 app \
    && adduser --system --uid 10001 --ingroup app app \
    && chmod +x entrypoint.sh \
    && mkdir -p data media staticfiles \
    && chown -R app:app /app

USER app
EXPOSE 8000

# Healthcheck via Python (urllib) - evita instalar o curl na imagem (menos
# superfície de ataque). Falha (exceção -> saída != 0) enquanto a API não sobe.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz/', timeout=4).status == 200 else 1)"]

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
