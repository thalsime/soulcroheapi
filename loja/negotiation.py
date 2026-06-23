from rest_framework.negotiation import BaseContentNegotiation


class JSONOnlyContentNegotiation(BaseContentNegotiation):
    """
    Ignora o cabeçalho Accept do cliente: a API responde SEMPRE em JSON.
    Combinado com o único renderer ser o JSONRenderer, garante que nem o
    navegador recebe a versão web (Browsable API) - só JSON.
    """

    def select_parser(self, request, parsers):
        return parsers[0]

    def select_renderer(self, request, renderers, format_suffix=None):
        return renderers[0], renderers[0].media_type
