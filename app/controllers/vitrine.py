"""Controller da Vitrine Virtual (catálogo)."""
from flask import Blueprint, abort, current_app, render_template, request, send_from_directory

from app.extensions import db
from app.models import Categoria, Cupcake

bp = Blueprint("vitrine", __name__)


@bp.get("/")
def index():
    busca = (request.args.get("q") or "").strip()
    categoria_id = request.args.get("categoria", type=int)

    consulta = db.select(Cupcake).where(Cupcake.disponivel.is_(True))
    if busca:
        like = f"%{busca}%"
        consulta = consulta.where(Cupcake.nome.ilike(like) | Cupcake.descricao.ilike(like))
    if categoria_id:
        consulta = consulta.where(Cupcake.categoria_id == categoria_id)
    cupcakes = db.session.scalars(consulta.order_by(Cupcake.nome)).all()
    categorias = db.session.scalars(db.select(Categoria).order_by(Categoria.nome)).all()
    return render_template("vitrine/index.html", cupcakes=cupcakes, categorias=categorias,
                           busca=busca, categoria_id=categoria_id)


@bp.get("/cupcake/<int:cupcake_id>")
def detalhe(cupcake_id: int):
    cupcake = db.session.get(Cupcake, cupcake_id)
    if cupcake is None or not cupcake.disponivel:
        abort(404)
    return render_template("vitrine/detalhe.html", cupcake=cupcake)


@bp.get("/sw.js")
def service_worker():
    """O service worker precisa ser servido da raiz para controlar todo o site."""
    resp = send_from_directory(current_app.static_folder, "sw.js", mimetype="application/javascript")
    resp.headers["Cache-Control"] = "no-cache"
    return resp
