"""
Garante variáveis de ambiente mínimas para os testes carregarem o settings
(modo desenvolvimento + chave de teste), antes do pytest-django configurar o Django.
"""
import os

os.environ.setdefault("DJANGO_DEBUG", "1")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-inseguro-para-os-testes")
