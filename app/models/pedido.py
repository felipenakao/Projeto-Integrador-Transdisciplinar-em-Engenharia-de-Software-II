from decimal import Decimal

from app.extensions import db
from app.models.usuario import agora

# Estados do pedido e transições permitidas (máquina de estados)
AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
PAGO = "PAGO"
EM_PREPARO = "EM_PREPARO"
SAIU_PARA_ENTREGA = "SAIU_PARA_ENTREGA"
PRONTO_PARA_RETIRADA = "PRONTO_PARA_RETIRADA"
ENTREGUE = "ENTREGUE"
CANCELADO = "CANCELADO"

ROTULOS_STATUS = {
    AGUARDANDO_PAGAMENTO: "Aguardando pagamento",
    PAGO: "Pago",
    EM_PREPARO: "Em preparo",
    SAIU_PARA_ENTREGA: "Saiu para entrega",
    PRONTO_PARA_RETIRADA: "Pronto para retirada",
    ENTREGUE: "Entregue",
    CANCELADO: "Cancelado",
}

TRANSICOES = {
    AGUARDANDO_PAGAMENTO: {PAGO, CANCELADO},
    PAGO: {EM_PREPARO, CANCELADO},
    EM_PREPARO: {SAIU_PARA_ENTREGA, PRONTO_PARA_RETIRADA, CANCELADO},
    SAIU_PARA_ENTREGA: {ENTREGUE},
    PRONTO_PARA_RETIRADA: {ENTREGUE},
    ENTREGUE: set(),
    CANCELADO: set(),
}

ENTREGA = "ENTREGA"
RETIRADA = "RETIRADA"


class Pedido(db.Model):
    __tablename__ = "pedido"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False, index=True)
    endereco_id = db.Column(db.Integer, db.ForeignKey("endereco.id"))
    tipo_entrega = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(25), nullable=False, default=AGUARDANDO_PAGAMENTO)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    taxa_entrega = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    observacoes = db.Column(db.String(300))
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    itens = db.relationship("ItemPedido", backref="pedido", cascade="all, delete-orphan")
    endereco = db.relationship("Endereco")
    pagamentos = db.relationship("Pagamento", backref="pedido", order_by="Pagamento.id",
                                 cascade="all, delete-orphan")

    __table_args__ = (
        db.CheckConstraint("tipo_entrega IN ('ENTREGA','RETIRADA')", name="ck_pedido_tipo"),
        db.CheckConstraint("total >= 0", name="ck_pedido_total"),
    )

    @property
    def pagamento_aprovado(self):
        return next((p for p in self.pagamentos if p.status == "APROVADO"), None)

    @property
    def rotulo_status(self) -> str:
        return ROTULOS_STATUS.get(self.status, self.status)

    def pode_ir_para(self, novo_status: str) -> bool:
        return novo_status in TRANSICOES.get(self.status, set())

    def mudar_status(self, novo_status: str) -> None:
        if not self.pode_ir_para(novo_status):
            raise ValueError(
                f"Transição inválida: {self.rotulo_status} → "
                f"{ROTULOS_STATUS.get(novo_status, novo_status)}."
            )
        self.status = novo_status

    def proximos_status(self) -> list[str]:
        ordem = list(ROTULOS_STATUS)
        permitidos = TRANSICOES.get(self.status, set())
        # Nunca oferecer o destino errado conforme o tipo de entrega
        if self.tipo_entrega == ENTREGA:
            permitidos = permitidos - {PRONTO_PARA_RETIRADA}
        else:
            permitidos = permitidos - {SAIU_PARA_ENTREGA}
        return [s for s in ordem if s in permitidos]


class ItemPedido(db.Model):
    __tablename__ = "item_pedido"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id"), nullable=False, index=True)
    cupcake_id = db.Column(db.Integer, db.ForeignKey("cupcake.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)  # preço no momento da compra

    cupcake = db.relationship("Cupcake")

    __table_args__ = (db.CheckConstraint("quantidade > 0", name="ck_item_quantidade"),)

    @property
    def total(self) -> Decimal:
        return self.preco_unitario * self.quantidade


class Pagamento(db.Model):
    __tablename__ = "pagamento"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id"), nullable=False, index=True)
    metodo = db.Column(db.String(10), nullable=False)  # PIX | CARTAO
    status = db.Column(db.String(12), nullable=False)  # APROVADO | RECUSADO
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    transacao_id = db.Column(db.String(40), nullable=False, unique=True)
    cartao_final = db.Column(db.String(4))  # só os 4 últimos dígitos; nunca o número completo
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    __table_args__ = (
        db.CheckConstraint("metodo IN ('PIX','CARTAO')", name="ck_pagamento_metodo"),
        db.CheckConstraint("status IN ('APROVADO','RECUSADO')", name="ck_pagamento_status"),
    )
