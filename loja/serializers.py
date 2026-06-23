from rest_framework import serializers

from .models import Categoria, Contato, Produto


class CategoriaSerializer(serializers.ModelSerializer):
    # Lê o campo anotado pela view (Count('produtos')); evita N+1 queries.
    produtos_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Categoria
        fields = ["id", "nome", "slug", "descricao", "produtos_count"]


class ProdutoSerializer(serializers.ModelSerializer):
    """
    Mantém o contrato do antigo produtos.json
    ({id, nome, categoria, preco, descricao, imagem}), com duas evoluções:
    - `categoria` vem com o nome legível da categoria (vinda do banco);
    - `imagem` vem como URL completa (https://.../media/...), pronta para o <img src>.
    """

    categoria = serializers.CharField(source="categoria.nome", read_only=True)
    imagem = serializers.SerializerMethodField()

    class Meta:
        model = Produto
        fields = ["id", "nome", "categoria", "preco", "descricao", "imagem"]

    def get_imagem(self, obj):
        if not obj.imagem:
            return None
        url = obj.imagem.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


class ContatoSerializer(serializers.ModelSerializer):
    """Recebe e valida uma mensagem do formulário de contato."""

    class Meta:
        model = Contato
        fields = [
            "id",
            "nome",
            "telefone",
            "email",
            "cep",
            "rua",
            "bairro",
            "cidade",
            "uf",
            "numero",
            "mensagem",
            "criado_em",
        ]
        read_only_fields = ["id", "criado_em"]
