"""Carrinho de compras guardado na sessão do usuário: {"<cupcake_id>": quantidade}."""

from __future__ import annotations
from decimal import Decimal

from flask import current_app, session

from app.extensions import db
from app.models import Cupcake
from app.services.erros import NegocioError

CHAVE = "carrinho"


def _dados() -> dict:
    return session.setdefault(CHAVE, {})


def _validar_quantidade(qtd) -> int:
    try:
        qtd = int(qtd)
    except (TypeError, ValueError):
        raise NegocioError("Quantidade inválida.")
    limite = current_app.config["QUANTIDADE_MAXIMA_POR_ITEM"]
    if qtd < 1 or qtd > limite:
        raise NegocioError(f"A quantidade deve estar entre 1 e {limite}.")
    return qtd


def _buscar_disponivel(cupcake_id: int) -> Cupcake:
    cupcake = db.session.get(Cupcake, cupcake_id)
    if cupcake is None:
        raise NegocioError("Cupcake não encontrado.")
    if not cupcake.disponivel:
        raise NegocioError(f"“{cupcake.nome}” está indisponível no momento.")
    return cupcake


def adicionar(cupcake_id: int, qtd=1) -> None:
    qtd = _validar_quantidade(qtd)
    _buscar_disponivel(cupcake_id)
    dados = _dados()
    chave = str(cupcake_id)
    nova = dados.get(chave, 0) + qtd
    limite = current_app.config["QUANTIDADE_MAXIMA_POR_ITEM"]
    if nova > limite:
        raise NegocioError(f"Limite de {limite} unidades por item.")
    dados[chave] = nova
    session.modified = True


def alterar(cupcake_id: int, qtd) -> None:
    qtd = _validar_quantidade(qtd)
    dados = _dados()
    if str(cupcake_id) not in dados:
        raise NegocioError("Este item não está no carrinho.")
    dados[str(cupcake_id)] = qtd
    session.modified = True


def remover(cupcake_id: int) -> None:
    _dados().pop(str(cupcake_id), None)
    session.modified = True


def limpar() -> None:
    session[CHAVE] = {}
    session.modified = True


def linhas() -> list[dict]:
    """Retorna itens do carrinho já com dados do cupcake, descartando os que sumiram/indisponíveis."""
    resultado = []
    dados = _dados()
    for chave, qtd in list(dados.items()):
        cupcake = db.session.get(Cupcake, int(chave))
        if cupcake is None or not cupcake.disponivel:
            dados.pop(chave)
            session.modified = True
            continue
        resultado.append({"cupcake": cupcake, "quantidade": qtd,
                          "total": cupcake.preco * qtd})
    return resultado


def subtotal(itens: list[dict] | None = None) -> Decimal:
    itens = linhas() if itens is None else itens
    return sum((i["total"] for i in itens), Decimal("0.00"))


def quantidade_total() -> int:
    return sum(_dados().values())
