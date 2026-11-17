"""Controller do painel administrativo da loja."""

from __future__ import annotations
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Categoria, Cupcake, Pedido
from app.models.pedido import ROTULOS_STATUS
from app.services import pedido_service
from app.services.erros import NegocioError

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_obrigatorio(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper


@bp.get("/")
@admin_obrigatorio
def painel():
    filtro = request.args.get("status")
    consulta = db.select(Pedido).order_by(Pedido.id.desc())
    if filtro in ROTULOS_STATUS:
        consulta = consulta.where(Pedido.status == filtro)
    pedidos = db.session.scalars(consulta).all()
    return render_template("admin/painel.html", pedidos=pedidos, filtro=filtro,
                           rotulos=ROTULOS_STATUS)


@bp.post("/pedidos/<int:pedido_id>/status")
@admin_obrigatorio
def mudar_status(pedido_id: int):
    pedido = db.session.get(Pedido, pedido_id) or abort(404)
    try:
        pedido_service.atualizar_status(pedido, request.form.get("status", ""))
        flash(f"Pedido #{pedido.id} atualizado para “{pedido.rotulo_status}”.", "sucesso")
    except NegocioError as e:
        flash(e.mensagem, "erro")
    return redirect(request.referrer or url_for("admin.painel"))


@bp.get("/cupcakes")
@admin_obrigatorio
def cupcakes():
    itens = db.session.scalars(db.select(Cupcake).order_by(Cupcake.nome)).all()
    return render_template("admin/cupcakes.html", cupcakes=itens)


@bp.route("/cupcakes/novo", methods=["GET", "POST"])
@bp.route("/cupcakes/<int:cupcake_id>/editar", methods=["GET", "POST"])
@admin_obrigatorio
def cupcake_form(cupcake_id: int | None = None):
    cupcake = db.session.get(Cupcake, cupcake_id) if cupcake_id else None
    if cupcake_id and cupcake is None:
        abort(404)
    categorias = db.session.scalars(db.select(Categoria).order_by(Categoria.nome)).all()
    if request.method == "POST":
        f = request.form
        preco, erros = Cupcake.validar(f.get("nome", ""), f.get("descricao", ""), f.get("preco", ""))
        categoria = db.session.get(Categoria, f.get("categoria_id", type=int) or 0)
        if categoria is None:
            erros.append("Escolha uma categoria.")
        if erros:
            for e in erros:
                flash(e, "erro")
        else:
            if cupcake is None:
                cupcake = Cupcake()
                db.session.add(cupcake)
            cupcake.nome = f["nome"].strip()
            cupcake.descricao = f["descricao"].strip()
            cupcake.preco = preco
            cupcake.categoria_id = categoria.id
            cupcake.emoji = (f.get("emoji") or "🧁").strip()[:8]
            cupcake.disponivel = f.get("disponivel") == "on"
            db.session.commit()
            flash("Cupcake salvo.", "sucesso")
            return redirect(url_for("admin.cupcakes"))
    return render_template("admin/cupcake_form.html", cupcake=cupcake, categorias=categorias,
                           form=request.form if request.method == "POST" else {})
