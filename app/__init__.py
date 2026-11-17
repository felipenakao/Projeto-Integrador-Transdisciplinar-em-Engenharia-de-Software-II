"""Fábrica da aplicação Flask (padrão MVC: models / templates (views) / controllers)."""
import os
import secrets

import click
from flask import Flask, abort, render_template, request, session

from app.config import Config
from app.extensions import db, login_manager
from app.models.pedido import ROTULOS_STATUS


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.controllers import admin, auth, carrinho, pedidos, vitrine
    for modulo in (vitrine, auth, carrinho, pedidos, admin):
        app.register_blueprint(modulo.bp)

    _registrar_seguranca(app)
    _registrar_filtros_e_contexto(app)
    _registrar_erros(app)
    _registrar_comandos(app)

    with app.app_context():
        from app import models  # noqa: F401  (garante o registro dos modelos)
        if app.config.get("TESTING") or app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
            db.create_all()
    return app


def _registrar_seguranca(app: Flask) -> None:
    """Proteção CSRF simples baseada em token de sessão para todo POST."""

    @app.before_request
    def verificar_csrf():
        if app.config.get("TESTING") or request.method != "POST":
            return
        enviado = request.form.get("_csrf", "")
        esperado = session.get("_csrf", "")
        if not esperado or not secrets.compare_digest(enviado, esperado):
            abort(400, description="Sessão expirada ou requisição inválida. Recarregue a página.")

    @app.after_request
    def cabecalhos(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        return resp


def _registrar_filtros_e_contexto(app: Flask) -> None:
    @app.template_filter("brl")
    def brl(valor) -> str:
        texto = f"{float(valor or 0):,.2f}"
        return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")

    @app.context_processor
    def globais():
        from app.services import carrinho as c
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)
        return {"csrf_token": session["_csrf"], "qtd_carrinho": c.quantidade_total(),
                "rotulos": ROTULOS_STATUS}


def _registrar_erros(app: Flask) -> None:
    def pagina(codigo: int, titulo: str, texto: str):
        return render_template("erro.html", codigo=codigo, titulo=titulo, texto=texto), codigo

    @app.errorhandler(400)
    def erro_400(e):
        return pagina(400, "Requisição inválida", getattr(e, "description", "Algo deu errado."))

    @app.errorhandler(403)
    def erro_403(e):
        return pagina(403, "Acesso negado", "Você não tem permissão para acessar esta página.")

    @app.errorhandler(404)
    def erro_404(e):
        return pagina(404, "Página não encontrada", "Não achamos o que você procurava. 🧁")

    @app.errorhandler(500)
    def erro_500(e):
        db.session.rollback()
        return pagina(500, "Erro inesperado", "Algo deu errado do nosso lado. Tente novamente.")


def _registrar_comandos(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db():
        """Cria as tabelas (use database/schema.sql em produção se preferir SQL puro)."""
        db.create_all()
        click.echo("Tabelas criadas.")

    @app.cli.command("seed")
    def seed():
        """Popula categorias, cupcakes de exemplo e um usuário administrador."""
        from app.seed import popular
        db.create_all()  # idempotente: só cria o que ainda não existe
        popular(os.environ.get("ADMIN_EMAIL", "admin@cupcakes.local"),
                os.environ.get("ADMIN_PASSWORD", "Admin1234"))
        click.echo("Dados de exemplo criados.")
