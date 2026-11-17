from __future__ import annotations

from decimal import Decimal

from app.extensions import db


class Categoria(db.Model):
    __tablename__ = "categoria"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(60), nullable=False, unique=True)

    cupcakes = db.relationship("Cupcake", backref="categoria")


class Cupcake(db.Model):
    __tablename__ = "cupcake"

    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"), nullable=False, index=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(400), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    emoji = db.Column(db.String(8), nullable=False, default="🧁")
    disponivel = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (db.CheckConstraint("preco > 0", name="ck_cupcake_preco_positivo"),)

    @staticmethod
    def validar(nome: str, descricao: str, preco) -> tuple[Decimal | None, list[str]]:
        """Valida dados vindos de formulário. Retorna (preco_decimal, lista_de_erros)."""
        erros = []
        if not nome or len(nome.strip()) < 3:
            erros.append("O nome deve ter ao menos 3 caracteres.")
        if not descricao or len(descricao.strip()) < 10:
            erros.append("A descrição deve ter ao menos 10 caracteres.")
        valor = None
        try:
            valor = Decimal(str(preco).replace(",", ".")).quantize(Decimal("0.01"))
            if valor <= 0:
                erros.append("O preço deve ser maior que zero.")
        except Exception:
            erros.append("Informe um preço válido (ex.: 12,50).")
        return valor, erros
