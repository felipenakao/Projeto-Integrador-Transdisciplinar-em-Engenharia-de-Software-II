from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


def agora():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False, unique=True, index=True)
    telefone = db.Column(db.String(20), nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    enderecos = db.relationship("Endereco", backref="usuario", cascade="all, delete-orphan")
    pedidos = db.relationship("Pedido", backref="usuario", order_by="Pedido.id.desc()")

    def definir_senha(self, senha: str) -> None:
        self.senha_hash = generate_password_hash(senha, method="pbkdf2:sha256")

    def conferir_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)


class Endereco(db.Model):
    __tablename__ = "endereco"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False, index=True)
    cep = db.Column(db.String(9), nullable=False)
    logradouro = db.Column(db.String(160), nullable=False)
    numero = db.Column(db.String(10), nullable=False)
    complemento = db.Column(db.String(80))
    bairro = db.Column(db.String(80), nullable=False)
    cidade = db.Column(db.String(80), nullable=False)
    uf = db.Column(db.String(2), nullable=False)

    def __str__(self):
        comp = f" - {self.complemento}" if self.complemento else ""
        return (f"{self.logradouro}, {self.numero}{comp}, {self.bairro}, "
                f"{self.cidade}/{self.uf} - CEP {self.cep}")


@login_manager.user_loader
def carregar_usuario(user_id):
    return db.session.get(Usuario, int(user_id))
