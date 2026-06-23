from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from .validators import validar_imagem_produto


class Categoria(models.Model):
    """Categoria de produto, administrada no banco (CRUD pelo admin)."""

    nome = models.CharField("nome", max_length=80, unique=True)
    slug = models.SlugField("slug", max_length=90, unique=True, blank=True)
    descricao = models.TextField("descrição", blank=True)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nome) or "categoria"
            slug = base
            n = 1
            while Categoria.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Produto(models.Model):
    """Um produto do catálogo da Soul Crochê (modelo principal da API)."""

    nome = models.CharField("nome", max_length=120)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="produtos",
        verbose_name="categoria",
    )
    preco = models.DecimalField("preço", max_digits=10, decimal_places=2)
    descricao = models.TextField("descrição", blank=True)
    imagem = models.ImageField(
        "imagem",
        upload_to="produtos/",
        blank=True,
        null=True,
        validators=[validar_imagem_produto],
    )
    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "produto"
        verbose_name_plural = "produtos"
        ordering = ["id"]

    def __str__(self):
        return self.nome


class Contato(models.Model):
    """Uma mensagem enviada pelo formulário de contato do site."""

    nome = models.CharField("nome", max_length=120)
    telefone = models.CharField("telefone", max_length=40, blank=True)
    email = models.EmailField("e-mail", blank=True)
    cep = models.CharField("CEP", max_length=9, blank=True)
    rua = models.CharField("rua", max_length=200, blank=True)
    bairro = models.CharField("bairro", max_length=120, blank=True)
    cidade = models.CharField("cidade", max_length=120, blank=True)
    uf = models.CharField("UF", max_length=2, blank=True)
    numero = models.CharField("número", max_length=20, blank=True)
    mensagem = models.TextField("mensagem", blank=True)
    criado_em = models.DateTimeField("recebido em", auto_now_add=True)

    class Meta:
        verbose_name = "contato"
        verbose_name_plural = "contatos"
        ordering = ["-criado_em"]

    def __str__(self):
        local = timezone.localtime(self.criado_em)
        return f"{self.nome} ({local:%d/%m/%Y %H:%M})"
