from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from loja.models import Categoria, Produto
from loja.throttling import ContatoIPThrottle


class ApiBaseTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.acessorio = Categoria.objects.create(nome="Acessório")
        cls.vestuario = Categoria.objects.create(nome="Vestuário")
        Produto.objects.create(nome="Brinco Flor", categoria=cls.acessorio, preco="9.99", descricao="brinco")
        Produto.objects.create(nome="Blusa multicor", categoria=cls.vestuario, preco="349.99", descricao="blusa")
        Produto.objects.create(nome="Cropped Neon", categoria=cls.vestuario, preco="139.99", descricao="cropped")
        cls.user = get_user_model().objects.create_user("site", password="x")
        cls.token = Token.objects.create(user=cls.user)

    def setUp(self):
        cache.clear()  # zera o throttle entre os testes


class RaizETests(ApiBaseTests):
    def test_raiz_retorna_403(self):
        self.assertEqual(self.client.get("/").status_code, 403)

    def test_healthz(self):
        r = self.client.get("/healthz/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_browsable_api_desligada(self):
        # Mesmo pedindo HTML, a resposta vem em JSON (sem versão web).
        r = self.client.get("/produtos/", HTTP_ACCEPT="text/html")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r["Content-Type"].startswith("application/json"))


class ProdutosTests(ApiBaseTests):
    def test_lista_paginada_e_contrato(self):
        r = self.client.get("/produtos/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["count"], 3)
        self.assertIn("results", data)
        item = data["results"][0]
        self.assertEqual(set(item), {"id", "nome", "categoria", "preco", "descricao", "imagem"})
        self.assertIn(item["categoria"], {"Acessório", "Vestuário"})
        self.assertIsNone(item["imagem"])

    def test_busca(self):
        r = self.client.get("/produtos/?search=blusa")
        self.assertEqual(r.json()["count"], 1)
        self.assertEqual(r.json()["results"][0]["nome"], "Blusa multicor")

    def test_filtro_por_categoria_slug(self):
        r = self.client.get("/produtos/?categoria__slug=vestuario")
        self.assertEqual(r.json()["count"], 2)

    def test_ordenacao_por_preco(self):
        r = self.client.get("/produtos/?ordering=-preco")
        precos = [float(p["preco"]) for p in r.json()["results"]]
        self.assertEqual(precos, sorted(precos, reverse=True))


class CategoriasTests(ApiBaseTests):
    def test_lista_com_produtos_count(self):
        r = self.client.get("/categorias/")
        self.assertEqual(r.status_code, 200)
        nomes = {c["nome"]: c["produtos_count"] for c in r.json()["results"]}
        self.assertEqual(nomes["Vestuário"], 2)
        self.assertEqual(nomes["Acessório"], 1)


class ContatoTests(ApiBaseTests):
    payload = {"nome": "Cliente", "email": "c@ex.com", "mensagem": "oi"}

    def test_sem_token_nao_autorizado(self):
        r = self.client.post("/contatos/", self.payload, format="json")
        self.assertEqual(r.status_code, 401)

    def test_com_token_cria(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        r = self.client.post("/contatos/", self.payload, format="json")
        self.assertEqual(r.status_code, 201)
        # A resposta é mínima: confirma o recebimento sem ecoar os dados (PII).
        self.assertEqual(r.json(), {"detail": "Mensagem recebida."})
        self.assertNotIn("nome", r.json())

    def test_payload_invalido(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        r = self.client.post("/contatos/", {"email": "x"}, format="json")  # falta nome
        self.assertEqual(r.status_code, 400)

    def test_throttle_limita_envios(self):
        cache.clear()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        # Força a taxa do escopo "contato" para 1/min, independente do .env.
        with patch.object(ContatoIPThrottle, "get_rate", return_value="1/min"):
            r1 = self.client.post("/contatos/", self.payload, format="json")
            r2 = self.client.post("/contatos/", self.payload, format="json")
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 429)
