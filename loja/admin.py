from django.contrib import admin
from django.utils.html import format_html

from .models import Categoria, Contato, Produto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "slug", "qtd_produtos")
    list_display_links = ("id", "nome")
    search_fields = ("nome", "descricao")
    prepopulated_fields = {"slug": ("nome",)}

    @admin.display(description="produtos")
    def qtd_produtos(self, obj):
        return obj.produtos.count()


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "categoria", "preco", "miniatura")
    list_display_links = ("id", "nome")
    list_filter = ("categoria",)
    search_fields = ("nome", "descricao")
    autocomplete_fields = ("categoria",)
    readonly_fields = ("criado_em", "atualizado_em")

    @admin.display(description="imagem")
    def miniatura(self, obj):
        if obj.imagem:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;">', obj.imagem.url)
        return "-"


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "email", "cidade", "criado_em")
    list_display_links = ("id", "nome")
    search_fields = ("nome", "email", "cidade", "mensagem")
    list_filter = ("criado_em",)
    readonly_fields = ("criado_em",)
