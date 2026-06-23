"""
Validadores de campos do modelo.

O upload de imagem de produto só acontece pelo admin. Este validador limita o
tamanho do arquivo enviado, como defesa contra uploads gigantes (esgotar disco
ou memória). O limite de pixels (bomba de descompressão) é tratado à parte, no
settings, via Pillow (Image.MAX_IMAGE_PIXELS).
"""
from django.core.exceptions import ValidationError

# Tamanho máximo do arquivo de imagem aceito no admin.
MAX_IMAGEM_BYTES = 5 * 1024 * 1024  # 5 MB


def validar_imagem_produto(arquivo):
    tamanho = getattr(arquivo, "size", None)
    if tamanho and tamanho > MAX_IMAGEM_BYTES:
        limite_mb = MAX_IMAGEM_BYTES // (1024 * 1024)
        raise ValidationError(
            "A imagem não pode passar de %(limite)d MB.",
            params={"limite": limite_mb},
        )
