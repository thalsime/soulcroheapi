"""Alguns testes em estilo pytest puro (fixtures + asserts), além do django.test."""
import pytest
from rest_framework.test import APIClient

from loja.models import Categoria, Produto


@pytest.mark.django_db
def test_lista_produtos_estilo_pytest():
    cat = Categoria.objects.create(nome="Acessório")
    Produto.objects.create(nome="Colar", categoria=cat, preco="39.99")
    resp = APIClient().get("/produtos/")
    assert resp.status_code == 200
    assert resp.json()["count"] == 1


@pytest.mark.django_db
def test_raiz_403_estilo_pytest():
    assert APIClient().get("/").status_code == 403
