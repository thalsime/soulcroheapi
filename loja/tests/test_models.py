from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from loja.models import Categoria, Contato, Produto
from loja.validators import MAX_IMAGEM_BYTES, validar_imagem_produto


class CategoriaModelTests(TestCase):
    def test_slug_gerado_do_nome(self):
        c = Categoria.objects.create(nome="Acessório")
        self.assertEqual(c.slug, "acessorio")

    def test_slug_desambigua_colisao(self):
        Categoria.objects.create(nome="Café")          # slug base "cafe"
        c2 = Categoria.objects.create(nome="Cafe")      # mesmo slug base -> sufixo
        self.assertEqual(c2.slug, "cafe-1")

    def test_str(self):
        self.assertEqual(str(Categoria.objects.create(nome="Vestuário")), "Vestuário")


class ProdutoModelTests(TestCase):
    def test_str(self):
        cat = Categoria.objects.create(nome="Acessório")
        p = Produto.objects.create(nome="Brinco", categoria=cat, preco="9.99")
        self.assertEqual(str(p), "Brinco")


class ContatoModelTests(TestCase):
    def test_str_usa_horario_local(self):
        c = Contato.objects.create(nome="Maria")
        esperado = timezone.localtime(c.criado_em).strftime("%d/%m/%Y %H:%M")
        self.assertIn(esperado, str(c))
        self.assertTrue(str(c).startswith("Maria"))


class ValidadorImagemTests(TestCase):
    """O validador limita o tamanho do arquivo de imagem enviado no admin."""

    class _Arquivo:
        def __init__(self, size):
            self.size = size

    def test_aceita_dentro_do_limite(self):
        # No limite exato não levanta exceção.
        validar_imagem_produto(self._Arquivo(MAX_IMAGEM_BYTES))

    def test_rejeita_acima_do_limite(self):
        with self.assertRaises(ValidationError):
            validar_imagem_produto(self._Arquivo(MAX_IMAGEM_BYTES + 1))
