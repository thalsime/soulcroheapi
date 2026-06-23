"""
Cria as categorias e os 6 produtos de exemplo da Soul Crochê, com as imagens reais.

Uso:  python manage.py seed_produtos
É idempotente: se já houver produtos cadastrados, não faz nada.
"""
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from loja.models import Categoria, Produto

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "seed_images"

CATEGORIAS = ["Acessório", "Vestuário", "Artigos de Casa"]

PRODUTOS = [
    {
        "nome": "Cropped Neon",
        "categoria": "Vestuário",
        "preco": "139.99",
        "descricao": "Cropped feito em linha 100% algodão reciclável.",
        "imagem": "blusa_amarela.jpg",
    },
    {
        "nome": "Trilho de mesa",
        "categoria": "Artigos de Casa",
        "preco": "159.99",
        "descricao": "Trilho de mesa feito em linha 100% algodão reciclável.",
        "imagem": "centro_de_mesa.jpg",
    },
    {
        "nome": "Blusa multicollor",
        "categoria": "Vestuário",
        "preco": "349.99",
        "descricao": "Blusa feita em linha 100% algodão reciclável.",
        "imagem": "blusa_colorida.jpg",
    },
    {
        "nome": "Brinco Flor",
        "categoria": "Acessório",
        "preco": "9.99",
        "descricao": "Brincos feito em linha 100% algodão reciclável e anzol em aço inoxidável.",
        "imagem": "brincos.jpg",
    },
    {
        "nome": "Colares",
        "categoria": "Acessório",
        "preco": "39.99",
        "descricao": "Colar feito em linha 100% algodão reciclável e argola em madeira.",
        "imagem": "colares.jpg",
    },
    {
        "nome": "Bolsa",
        "categoria": "Acessório",
        "preco": "129.99",
        "descricao": "Bolsa feita em linha 100% algodão reciclável e alça em couro.",
        "imagem": "bolsa.webp",
    },
]


class Command(BaseCommand):
    help = "Cria as categorias e os 6 produtos de exemplo da Soul Crochê (idempotente)."

    def handle(self, *args, **options):
        if Produto.objects.exists():
            self.stdout.write(
                self.style.WARNING("Já existem produtos cadastrados; nada a fazer.")
            )
            return

        categorias = {
            nome: Categoria.objects.get_or_create(nome=nome)[0] for nome in CATEGORIAS
        }

        criados = 0
        for dados in PRODUTOS:
            produto = Produto(
                nome=dados["nome"],
                categoria=categorias[dados["categoria"]],
                preco=dados["preco"],
                descricao=dados["descricao"],
            )
            imagem = SEED_DIR / dados["imagem"]
            if imagem.exists():
                with imagem.open("rb") as arquivo:
                    produto.imagem.save(dados["imagem"], File(arquivo), save=False)
            else:
                self.stdout.write(self.style.WARNING(f"Imagem não encontrada: {imagem}"))
            produto.save()
            criados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{len(categorias)} categorias e {criados} produtos criados."
            )
        )
