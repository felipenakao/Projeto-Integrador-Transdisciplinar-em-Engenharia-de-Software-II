"""Controller de Pedido Eletrônico (checkout), Pagamento e acompanhamento da Entrega."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Pedido
from app.models.pedido import AGUARDANDO_PAGAMENTO
from app.services import carrinho as carrinho_svc
from app.services import pagamento_service, pedido_service
from app.services.erros import NegocioError, PagamentoRecusado

bp = Blueprint("pedidos", __name__)


def _pedido_do_usuario(pedido_id: int) -> Pedido:
    pedido = db.session.get(Pedido, pedido_id)
    if pedido is None or (pedido.usuario_id != current_user.id and not current_user.is_admin):
        abort(404)  # 404 (e não 403) para não revelar que o pedido existe
    return pedido


@bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    itens = carrinho_svc.linhas()
    if not itens:
        flash("Seu carrinho está vazio.", "aviso")
        return redirect(url_for("vitrine.index"))
    subtotal = carrinho_svc.subtotal(itens)
    form = request.form if request.method == "POST" else {}
    tipo = form.get("tipo_entrega", "ENTREGA")

    if request.method == "POST":
        try:
            pedido = pedido_service.criar_pedido(
                current_user, itens, tipo, dict(request.form), request.form.get("observacoes", ""))
        except NegocioError as e:
            for msg in e.erros:
                flash(msg, "erro")
        else:
            carrinho_svc.limpar()
            flash("Pedido criado! Agora escolha a forma de pagamento.", "sucesso")
            return redirect(url_for("pedidos.pagar", pedido_id=pedido.id))

    return render_template(
        "pedidos/checkout.html", itens=itens, subtotal=subtotal, form=form, tipo=tipo,
        frete_entrega=pedido_service.calcular_frete(subtotal, "ENTREGA"))


@bp.route("/pedidos/<int:pedido_id>/pagar", methods=["GET", "POST"])
@login_required
def pagar(pedido_id: int):
    pedido = _pedido_do_usuario(pedido_id)
    if pedido.status != AGUARDANDO_PAGAMENTO:
        flash("Este pedido não está aguardando pagamento.", "aviso")
        return redirect(url_for("pedidos.detalhe", pedido_id=pedido.id))
    if request.method == "POST":
        metodo = request.form.get("metodo", "")
        cartao = {k: request.form.get(k, "") for k in ("numero", "validade", "cvv", "titular")}
        try:
            pagamento_service.pagar(pedido, metodo, cartao)
        except PagamentoRecusado as e:
            flash(e.mensagem, "erro")
        except NegocioError as e:
            for msg in e.erros:
                flash(msg, "erro")
        else:
            flash("Pagamento aprovado! Já estamos cuidando do seu pedido.", "sucesso")
            return redirect(url_for("pedidos.detalhe", pedido_id=pedido.id))
    return render_template("pedidos/pagar.html", pedido=pedido)


@bp.get("/pedidos")
@login_required
def meus_pedidos():
    return render_template("pedidos/lista.html", pedidos=current_user.pedidos)


@bp.get("/pedidos/<int:pedido_id>")
@login_required
def detalhe(pedido_id: int):
    return render_template("pedidos/detalhe.html", pedido=_pedido_do_usuario(pedido_id))


@bp.post("/pedidos/<int:pedido_id>/cancelar")
@login_required
def cancelar(pedido_id: int):
    pedido = _pedido_do_usuario(pedido_id)
    try:
        pedido_service.cancelar_pedido(pedido)
        flash("Pedido cancelado.", "sucesso")
    except NegocioError as e:
        flash(e.mensagem, "erro")
    return redirect(url_for("pedidos.detalhe", pedido_id=pedido.id))
