"""Controller de autenticação (cadastro, login, logout)."""

from __future__ import annotations
from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models import Usuario
from app.services import validadores as v

bp = Blueprint("auth", __name__)


def _destino_seguro(destino: str | None) -> str:
    """Evita open redirect: só aceita caminhos relativos do próprio site."""
    if destino:
        p = urlparse(destino)
        if not p.netloc and not p.scheme and destino.startswith("/") and not destino.startswith("//"):
            return destino
    return url_for("vitrine.index")


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for("vitrine.index"))
    form = {}
    if request.method == "POST":
        form = request.form
        nome = form.get("nome", "").strip()
        email = form.get("email", "").strip().lower()
        telefone = form.get("telefone", "")
        senha = form.get("senha", "")
        erros = []
        if len(nome) < 3:
            erros.append("Informe seu nome completo.")
        if not v.email_valido(email):
            erros.append("E-mail inválido.")
        elif db.session.scalar(db.select(Usuario).where(Usuario.email == email)):
            erros.append("Já existe uma conta com este e-mail.")
        if not v.telefone_valido(telefone):
            erros.append("Telefone inválido (DDD + número).")
        if not v.senha_valida(senha):
            erros.append("A senha precisa ter 8+ caracteres, com letras e números.")
        if senha != form.get("confirmar_senha", ""):
            erros.append("A confirmação de senha não confere.")
        if erros:
            for e in erros:
                flash(e, "erro")
        else:
            usuario = Usuario(nome=nome, email=email, telefone=v.somente_digitos(telefone))
            usuario.definir_senha(senha)
            db.session.add(usuario)
            db.session.commit()
            login_user(usuario)
            flash("Conta criada com sucesso! Bem-vindo(a).", "sucesso")
            return redirect(url_for("vitrine.index"))
    return render_template("auth/cadastro.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("vitrine.index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        usuario = db.session.scalar(db.select(Usuario).where(Usuario.email == email))
        if usuario and usuario.conferir_senha(request.form.get("senha", "")):
            login_user(usuario)
            return redirect(_destino_seguro(request.args.get("next")))
        flash("E-mail ou senha incorretos.", "erro")  # mensagem genérica de propósito
    return render_template("auth/login.html")


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("vitrine.index"))
