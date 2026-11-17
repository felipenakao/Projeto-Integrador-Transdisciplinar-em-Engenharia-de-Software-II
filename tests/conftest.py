from decimal import Decimal

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Categoria, Cupcake, Usuario


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        cat = Categoria(nome="Clássicos")
        db.session.add(cat)
        db.session.flush()
        db.session.add_all([
            Cupcake(categoria_id=cat.id, nome="Baunilha", descricao="Massa fofinha de baunilha.",
                    preco=Decimal("10.00")),
            Cupcake(categoria_id=cat.id, nome="Chocolate", descricao="Massa de cacau com ganache.",
                    preco=Decimal("12.50")),
            Cupcake(categoria_id=cat.id, nome="Esgotado", descricao="Item fora de linha agora.",
                    preco=Decimal("9.00"), disponivel=False),
        ])
        admin = Usuario(nome="Admin", email="admin@teste.com", telefone="11999999999", is_admin=True)
        admin.definir_senha("Admin1234")
        cliente = Usuario(nome="Cliente Teste", email="cliente@teste.com", telefone="11988887777")
        cliente.definir_senha("Senha1234")
        db.session.add_all([admin, cliente])
        db.session.commit()
    # O yield fica FORA do app_context: cada requisição dos clientes de teste ganha o seu próprio
    # contexto, senão o usuário logado "vaza" (via flask.g) entre clientes diferentes.
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()  # fecha a conexão SQLite (evita ResourceWarning)


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email="cliente@teste.com", senha="Senha1234"):
    return client.post("/login", data={"email": email, "senha": senha}, follow_redirects=True)


@pytest.fixture()
def cliente_logado(client):
    login(client)
    return client


@pytest.fixture()
def admin_logado(app):
    c = app.test_client()
    login(c, "admin@teste.com", "Admin1234")
    return c


ENDERECO = {"tipo_entrega": "ENTREGA", "cep": "01310-100", "logradouro": "Av. Paulista",
            "numero": "1000", "bairro": "Bela Vista", "cidade": "São Paulo", "uf": "SP"}


def ids(app):
    with app.app_context():
        return {c.nome: c.id for c in db.session.scalars(db.select(Cupcake))}


def criar_pedido_via_http(client, app, quantidade=2, dados=None):
    """Adiciona Baunilha ao carrinho, faz checkout e devolve o id do pedido."""
    cid = ids(app)["Baunilha"]
    client.post(f"/carrinho/adicionar/{cid}", data={"quantidade": quantidade})
    resp = client.post("/checkout", data=dados or ENDERECO)
    assert resp.status_code == 302, resp.get_data(as_text=True)
    return int(resp.headers["Location"].split("/")[2])
