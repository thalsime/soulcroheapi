"""
Rotas do projeto.

- `/`         -> **403 Forbidden** (não lista endpoints).
- `/produtos/`-> catálogo (leitura pública).
- `/categorias/`-> categorias (leitura pública).
- `/contatos/`-> envio do formulário de contato (exige token).
- `/admin/`   -> área administrativa (CRUD) do Django.
- `/healthz/` -> verificação de saúde (usada pelo healthcheck do container).
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import SimpleRouter

from loja.views import CategoriaViewSet, ContatoViewSet, ProdutoViewSet


def healthz(_request):
    return JsonResponse({"status": "ok"})


def api_root_forbidden(_request):
    # A raiz não revela os endpoints disponíveis (JSON, consistente com a API).
    return JsonResponse({"detail": "Forbidden"}, status=403)


# SimpleRouter não cria a view-raiz que listava os endpoints (a DefaultRouter criava).
router = SimpleRouter()
router.register("produtos", ProdutoViewSet, basename="produto")
router.register("categorias", CategoriaViewSet, basename="categoria")
router.register("contatos", ContatoViewSet, basename="contato")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz),
    path("", api_root_forbidden),
    path("", include(router.urls)),
]

# Em desenvolvimento (DEBUG), o próprio Django serve os arquivos de mídia.
# Em produção quem serve /media/ é o nginx (ver deploy/nginx-soulcroheapi.conf).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
