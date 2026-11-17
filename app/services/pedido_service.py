from __future__ import annotations

from decimal import Decimal

from flask import current_app

from app.extensions import db
from app.models import Endereco, ItemPedido, Pedido
from app.models.pedido import AGUARDANDO_PAGAMENTO, CANCELADO, ENTREGA, RETIRADA
from app.services import validadores as v
from app.services.erros import NegocioError


def calcular_frete(subtotal: Decimal, tipo_entrega: str) -> Decimal:
    if tipo_entrega == RETIRADA:
        return Decimal("0.00")
    if subtotal >= current_app.config["FRETE_GRATIS_ACIMA_DE"]:
        return Decimal("0.00")
    return current_app.config["TAXA_ENTREGA"]


def validar_endereco(dados: dict) -> list[str]:
    erros = []
    if not v.cep_valido(dados.get("cep", "")):
        erros.append("CEP inválido (use 8 dígitos).")
    for campo, rotulo in (("logradouro", "Rua"), ("numero", "Número"),
                          ("bairro", "Bairro"), ("cidade", "Cidade")):
        if not (dados.get(campo) or "").strip():
            erros.append(f"{rotulo} é obrigatório.")
    if (dados.get("uf") or "").strip().upper() not in v.UFS:
        erros.append("UF inválida.")
    return erros


def criar_pedido(usuario, itens: list[dict], tipo_entrega: str,
                 dados_endereco: dict | None, observacoes: str = "") -> Pedido:
    """Cria o pedido a partir das linhas do carrinho. Lança NegocioError se algo estiver inválido."""
    if not itens:
        raise NegocioError("Seu carrinho está vazio.")
    if tipo_entrega not in (ENTREGA, RETIRADA):
        raise NegocioError("Escolha entre entrega e retirada.")
    if len(observacoes or "") > 300:
        raise NegocioError("As observações podem ter no máximo 300 caracteres.")

    endereco = None
    if tipo_entrega == ENTREGA:
        erros = validar_endereco(dados_endereco or {})
        if erros:
            raise NegocioError("Corrija o endereço de entrega.", erros)
        endereco = Endereco(
            usuario_id=usuario.id,
            cep=v.formatar_cep(dados_endereco["cep"]),
            logradouro=dados_endereco["logradouro"].strip(),
            numero=dados_endereco["numero"].strip(),
            complemento=(dados_endereco.get("complemento") or "").strip() or None,
            bairro=dados_endereco["bairro"].strip(),
            cidade=dados_endereco["cidade"].strip(),
            uf=dados_endereco["uf"].strip().upper(),
        )
        db.session.add(endereco)

    subtotal = sum((i["total"] for i in itens), Decimal("0.00"))
    frete = calcular_frete(subtotal, tipo_entrega)
    pedido = Pedido(
        usuario_id=usuario.id,
        endereco=endereco,
        tipo_entrega=tipo_entrega,
        status=AGUARDANDO_PAGAMENTO,
        subtotal=subtotal,
        taxa_entrega=frete,
        total=subtotal + frete,
        observacoes=(observacoes or "").strip() or None,
    )
    for i in itens:
        pedido.itens.append(ItemPedido(cupcake_id=i["cupcake"].id, quantidade=i["quantidade"],
                                       preco_unitario=i["cupcake"].preco))
    db.session.add(pedido)
    db.session.commit()
    return pedido


def cancelar_pedido(pedido: Pedido) -> None:
    """Cliente só pode cancelar enquanto o pedido ainda não foi pago."""
    if pedido.status != AGUARDANDO_PAGAMENTO:
        raise NegocioError("Só é possível cancelar pedidos que ainda não foram pagos.")
    pedido.mudar_status(CANCELADO)
    db.session.commit()


def atualizar_status(pedido: Pedido, novo_status: str) -> None:
    try:
        if novo_status not in pedido.proximos_status():
            raise ValueError(f"Transição inválida para este pedido ({pedido.rotulo_status}).")
        pedido.mudar_status(novo_status)
    except ValueError as exc:
        raise NegocioError(str(exc))
    db.session.commit()
