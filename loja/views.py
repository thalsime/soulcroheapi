from django.db.models import Count
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response

from .models import Categoria, Contato, Produto
from .serializers import CategoriaSerializer, ContatoSerializer, ProdutoSerializer
from .throttling import ContatoIPThrottle


class CategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Categorias - somente leitura e pública. CRUD é feito no admin.
    Busca:    ?search=<texto>   (nome, descrição)
    Filtro:   ?slug=<slug>
    Ordenar:  ?ordering=nome
    """

    # annotate calcula a contagem de produtos numa única query (sem N+1).
    queryset = Categoria.objects.annotate(produtos_count=Count("produtos"))
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ["slug"]
    search_fields = ["nome", "descricao"]
    ordering_fields = ["nome", "id"]
    ordering = ["nome"]


class ProdutoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Catálogo - somente leitura e público (GET sem token).
    Busca:    ?search=<texto>           (nome, descrição, nome da categoria)
    Filtro:   ?categoria=<id>  ou  ?categoria__slug=<slug>
    Ordenar:  ?ordering=preco   (ou -preco, nome, id)
    O cadastro/edição de produtos é feito pelo admin do Django.
    """

    queryset = Produto.objects.select_related("categoria").all()
    serializer_class = ProdutoSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ["categoria", "categoria__slug"]
    search_fields = ["nome", "descricao", "categoria__nome"]
    ordering_fields = ["id", "nome", "preco", "criado_em"]
    ordering = ["id"]


class ContatoViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Recebe o formulário de contato (apenas POST) e exige token.
    O token é gerado no admin do Django e colado no site.
    As mensagens recebidas são lidas no admin (não há listagem pela API).
    O limite de envios (throttle) é por IP, para mitigar spam pelo token público.
    """

    queryset = Contato.objects.all()
    serializer_class = ContatoSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ContatoIPThrottle]

    def create(self, request, *args, **kwargs):
        # Valida e salva, mas devolve um corpo mínimo: não ecoa os dados
        # recebidos (PII: nome, e-mail, telefone, endereço) nem o id do registro.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"detail": "Mensagem recebida."}, status=status.HTTP_201_CREATED)
