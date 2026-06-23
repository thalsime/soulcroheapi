import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings

from loja.models import Categoria, Produto
from loja.serializers import ProdutoSerializer


class ProdutoSerializerTests(TestCase):
    def test_categoria_nome_e_imagem_none(self):
        cat = Categoria.objects.create(nome="Acessório")
        p = Produto.objects.create(nome="Brinco", categoria=cat, preco="9.99")
        data = ProdutoSerializer(p, context={"request": RequestFactory().get("/")}).data
        self.assertEqual(data["categoria"], "Acessório")
        self.assertIsNone(data["imagem"])

    def test_imagem_vira_url_absoluta(self):
        cat = Categoria.objects.create(nome="Acessório")
        with tempfile.TemporaryDirectory() as media:
            with override_settings(MEDIA_ROOT=media):
                arq = SimpleUploadedFile("x.jpg", b"\xff\xd8\xff\xe0teste", content_type="image/jpeg")
                p = Produto.objects.create(nome="X", categoria=cat, preco="1.00", imagem=arq)
                data = ProdutoSerializer(p, context={"request": RequestFactory().get("/")}).data
                self.assertTrue(data["imagem"].startswith("http://testserver/media/"))
