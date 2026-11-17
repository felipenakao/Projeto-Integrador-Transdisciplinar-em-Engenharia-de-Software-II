"""Gateway de pagamento SIMULADO (didático).

Regras da simulação — documentadas também em docs/03-testes:
  * PIX: sempre aprovado.
  * Cartão: número precisa passar no algoritmo de Luhn; validade e CVV são checados.
    Cartões terminados em 0002 são recusados (simula "saldo insuficiente").
  * O número completo do cartão e o CVV NUNCA são gravados; só os 4 últimos dígitos.
"""

from __future__ import annotations
import uuid

from app.extensions import db
from app.models import Pagamento, Pedido
from app.models.pedido import AGUARDANDO_PAGAMENTO, PAGO
from app.services import validadores as v
from app.services.erros import NegocioError, PagamentoRecusado

CARTAO_RECUSADO_FINAL = "0002"


def _registrar(pedido: Pedido, metodo: str, status: str, final: str | None) -> Pagamento:
    pgto = Pagamento(pedido_id=pedido.id, metodo=metodo, status=status, valor=pedido.total,
                     transacao_id=uuid.uuid4().hex[:24], cartao_final=final)
    db.session.add(pgto)
    return pgto


def pagar(pedido: Pedido, metodo: str, cartao: dict | None = None) -> Pagamento:
    if pedido.status != AGUARDANDO_PAGAMENTO:
        raise NegocioError("Este pedido não está aguardando pagamento.")
    if metodo not in ("PIX", "CARTAO"):
        raise NegocioError("Escolha uma forma de pagamento.")

    final = None
    if metodo == "CARTAO":
        cartao = cartao or {}
        erros = []
        if not v.cartao_luhn_valido(cartao.get("numero", "")):
            erros.append("Número do cartão inválido.")
        if not v.validade_cartao_ok(cartao.get("validade", "")):
            erros.append("Validade inválida ou vencida (use MM/AA).")
        if not v.cvv_valido(cartao.get("cvv", "")):
            erros.append("CVV inválido.")
        if not (cartao.get("titular") or "").strip():
            erros.append("Informe o nome do titular.")
        if erros:
            raise NegocioError("Corrija os dados do cartão.", erros)
        final = v.somente_digitos(cartao["numero"])[-4:]
        if final == CARTAO_RECUSADO_FINAL:
            _registrar(pedido, metodo, "RECUSADO", final)
            db.session.commit()
            raise PagamentoRecusado("Pagamento recusado pela operadora. Tente outro cartão ou Pix.")

    pgto = _registrar(pedido, metodo, "APROVADO", final)
    pedido.mudar_status(PAGO)
    db.session.commit()
    return pgto
