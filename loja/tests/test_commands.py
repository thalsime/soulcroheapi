import tempfile

from django.core.management import call_command
from django.test import TestCase, override_settings

from loja.models import Categoria, Produto


class SeedProdutosTests(TestCase):
    def test_cria_categorias_e_produtos_com_imagem(self):
        with tempfile.TemporaryDirectory() as media:
            with override_settings(MEDIA_ROOT=media):
                call_command("seed_produtos")
                self.assertEqual(Categoria.objects.count(), 3)
                self.assertEqual(Produto.objects.count(), 6)
                self.assertEqual(Produto.objects.exclude(imagem="").count(), 6)

    def test_idempotente(self):
        with tempfile.TemporaryDirectory() as media:
            with override_settings(MEDIA_ROOT=media):
                call_command("seed_produtos")
                call_command("seed_produtos")  # segunda vez não duplica
                self.assertEqual(Produto.objects.count(), 6)
