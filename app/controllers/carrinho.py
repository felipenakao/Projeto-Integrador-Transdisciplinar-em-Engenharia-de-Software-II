"""Controller do carrinho (Pedido Eletrônico — parte 1)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services import carrinho as svc
from app.services.erros import NegocioError
from app.services.pedido_service import calcular_frete
from app.models.pedido import ENTREGA

bp = Blueprint("carrinho", __name__, url_prefix="/carrinho")


def _voltar():
    return redirect(request.referrer or url_for("carrinho.ver"))


@bp.get("/")
def ver():
    itens = svc.linhas()
    subtotal = svc.subtotal(itens)
    return render_template("carrinho/ver.html", itens=itens, subtotal=subtotal,
                           frete=calcular_frete(subtotal, ENTREGA) if itens else 0)


@bp.post("/adicionar/<int:cupcake_id>")
def adicionar(cupcake_id: int):
    try:
        svc.adicionar(cupcake_id, request.form.get("quantidade", 1))
        flash("Adicionado ao carrinho 🧁", "sucesso")
    except NegocioError as e:
        flash(e.mensagem, "erro")
    return _voltar()


@bp.post("/alterar/<int:cupcake_id>")
def alterar(cupcake_id: int):
    try:
        svc.alterar(cupcake_id, request.form.get("quantidade"))
    except NegocioError as e:
        flash(e.mensagem, "erro")
    return redirect(url_for("carrinho.ver"))


@bp.post("/remover/<int:cupcake_id>")
def remover(cupcake_id: int):
    svc.remover(cupcake_id)
    flash("Item removido.", "sucesso")
    return redirect(url_for("carrinho.ver"))
