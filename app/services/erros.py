from __future__ import annotations

class NegocioError(Exception):
    """Erro de regra de negócio com mensagem pronta para exibir ao usuário."""

    def __init__(self, mensagem: str, erros: list[str] | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.erros = erros or [mensagem]


class PagamentoRecusado(NegocioError):
    pass
