"""
Throttle (limite de envios) do formulário de contato.

O endpoint /contatos/ usa um token DRF compartilhado pelo site cliente. Se o
limite fosse por usuário do token (ScopedRateThrottle), todos os visitantes
dividiriam um único balde global - um visitante esgotaria o limite de todos.
Aqui o limite é por **IP de origem**: cada visitante tem seu próprio balde.

A taxa vem de DEFAULT_THROTTLE_RATES["contato"] (configurável no .env via
THROTTLE_CONTATO). Atrás de proxy/CDN, configure NUM_PROXIES para que o IP
considerado seja o do cliente real (cabeçalho X-Forwarded-For), não o do proxy.
"""
from rest_framework.throttling import SimpleRateThrottle


class ContatoIPThrottle(SimpleRateThrottle):
    scope = "contato"

    def get_cache_key(self, request, view):
        # Chaveia o balde pelo IP de origem (get_ident respeita NUM_PROXIES).
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
