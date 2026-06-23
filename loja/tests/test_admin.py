import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from loja.models import Categoria, Produto


class AdminSmokeTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("adm", "a@a.com", "x")
        self.client.force_login(self.admin)

    def test_changelists_abrem(self):
        cat = Categoria.objects.create(nome="Acessório")
        with tempfile.TemporaryDirectory() as media:
            with override_settings(MEDIA_ROOT=media):
                img = SimpleUploadedFile("x.jpg", b"\xff\xd8\xff\xe0teste", content_type="image/jpeg")
                Produto.objects.create(nome="Brinco", categoria=cat, preco="9.99", imagem=img)
                for model in ("categoria", "produto", "contato"):
                    url = reverse(f"admin:loja_{model}_changelist")
                    self.assertEqual(self.client.get(url).status_code, 200)
