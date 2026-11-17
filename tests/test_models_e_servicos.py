"""Testes unitários/de serviço: modelos, carrinho, frete, pedido e pagamento."""
from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Cupcake, Pedido, Usuario
from app.models.pedido import (AGUARDANDO_PAGAMENTO, CANCELADO, ENTREGA, ENTREGUE, EM_PREPARO,
                               PAGO, RETIRADA, SAIU_PARA_ENTREGA)
from app.services import carrinho, pagamento_service, pedido_service
from app.services.erros import NegocioError, PagamentoRecusado
from tests.conftest import ENDERECO, ids


@pytest.fixture(autouse=True)
def contexto(app):
    """Estes testes chamam serviços/banco diretamente, então precisam de um app_context."""
    with app.app_context():
        yield


# ---------- Modelo Cupcake ----------
def test_validar_cupcake_ok():
    preco, erros = Cupcake.validar("Brigadeiro", "Cupcake de brigadeiro cremoso", "12,50")
    assert erros == [] and preco == Decimal("12.50")


@pytest.mark.parametrize("nome,desc,preco", [
    ("ab", "descrição válida aqui", "10"), ("Nome ok", "curta", "10"),
    ("Nome ok", "descrição válida aqui", "0"), ("Nome ok", "descrição válida aqui", "-3"),
    ("Nome ok", "descrição válida aqui", "abc"),
])
def test_validar_cupcake_erros(nome, desc, preco):
    _, erros = Cupcake.validar(nome, desc, preco)
    assert erros


def test_senha_nunca_guardada_em_texto_puro(app):
    u = db.session.scalar(db.select(Usuario).where(Usuario.email == "cliente@teste.com"))
    assert u.senha_hash != "Senha1234"
    assert u.conferir_senha("Senha1234") and not u.conferir_senha("errada")


# ---------- Carrinho ----------
def test_carrinho_adicionar_alterar_remover(app):
    cid = ids(app)["Baunilha"]
    with app.test_request_context():
        carrinho.adicionar(cid, 2)
        carrinho.adicionar(cid, 1)
        assert carrinho.quantidade_total() == 3
        carrinho.alterar(cid, 5)
        assert carrinho.subtotal() == Decimal("50.00")
        carrinho.remover(cid)
        assert carrinho.linhas() == []


@pytest.mark.parametrize("qtd", [0, -1, 51, "abc", None])
def test_carrinho_quantidade_invalida(app, qtd):
    cid = ids(app)["Baunilha"]
    with app.test_request_context(), pytest.raises(NegocioError):
        carrinho.adicionar(cid, qtd)


def test_carrinho_item_indisponivel_ou_inexistente(app):
    with app.test_request_context():
        with pytest.raises(NegocioError):
            carrinho.adicionar(ids(app)["Esgotado"], 1)
        with pytest.raises(NegocioError):
            carrinho.adicionar(99999, 1)


def test_carrinho_limite_acumulado(app):
    cid = ids(app)["Baunilha"]
    with app.test_request_context():
        carrinho.adicionar(cid, 40)
        with pytest.raises(NegocioError):
            carrinho.adicionar(cid, 11)


# ---------- Frete ----------
def test_frete(app):
    with app.app_context():
        assert pedido_service.calcular_frete(Decimal("50"), ENTREGA) == Decimal("8.00")
        assert pedido_service.calcular_frete(Decimal("120"), ENTREGA) == Decimal("0.00")
        assert pedido_service.calcular_frete(Decimal("50"), RETIRADA) == Decimal("0.00")


# ---------- Pedido ----------
def _itens(app, qtd=2):
    cup = db.session.get(Cupcake, ids(app)["Baunilha"])
    return [{"cupcake": cup, "quantidade": qtd, "total": cup.preco * qtd}]


def _cliente():
    return db.session.scalar(db.select(Usuario).where(Usuario.email == "cliente@teste.com"))


def test_criar_pedido_entrega_calcula_total(app):
    p = pedido_service.criar_pedido(_cliente(), _itens(app), ENTREGA, ENDERECO)
    assert p.subtotal == Decimal("20.00") and p.taxa_entrega == Decimal("8.00")
    assert p.total == Decimal("28.00") and p.status == AGUARDANDO_PAGAMENTO
    assert p.endereco.cep == "01310-100"


def test_criar_pedido_retirada_dispensa_endereco(app):
    p = pedido_service.criar_pedido(_cliente(), _itens(app), RETIRADA, None)
    assert p.endereco is None and p.total == Decimal("20.00")


def test_pedido_guarda_preco_do_momento(app):
    p = pedido_service.criar_pedido(_cliente(), _itens(app), RETIRADA, None)
    cup = db.session.get(Cupcake, ids(app)["Baunilha"])
    cup.preco = Decimal("99.00")
    db.session.commit()
    assert p.itens[0].preco_unitario == Decimal("10.00")


def test_criar_pedido_erros(app):
    c = _cliente()
    with pytest.raises(NegocioError):
        pedido_service.criar_pedido(c, [], ENTREGA, ENDERECO)  # carrinho vazio
    with pytest.raises(NegocioError):
        pedido_service.criar_pedido(c, _itens(app), "DRONE", ENDERECO)  # tipo inválido
    with pytest.raises(NegocioError) as exc:
        pedido_service.criar_pedido(c, _itens(app), ENTREGA, {"cep": "1"})  # endereço ruim
    assert len(exc.value.erros) > 1
    with pytest.raises(NegocioError):
        pedido_service.criar_pedido(c, _itens(app), RETIRADA, None, "x" * 301)


def test_maquina_de_estados(app):
    p = pedido_service.criar_pedido(_cliente(), _itens(app), ENTREGA, ENDERECO)
    with pytest.raises(NegocioError):
        pedido_service.atualizar_status(p, ENTREGUE)  # não pode pular etapas
    pagamento_service.pagar(p, "PIX")
    assert p.status == PAGO
    pedido_service.atualizar_status(p, EM_PREPARO)
    assert SAIU_PARA_ENTREGA in p.proximos_status()
    pedido_service.atualizar_status(p, SAIU_PARA_ENTREGA)
    pedido_service.atualizar_status(p, ENTREGUE)
    with pytest.raises(NegocioError):
        pedido_service.atualizar_status(p, CANCELADO)  # estado final


def test_retirada_nao_oferece_saiu_para_entrega(app):
    p = pedido_service.criar_pedido(_cliente(), _itens(app), RETIRADA, None)
    pagamento_service.pagar(p, "PIX")
    pedido_service.atualizar_status(p, EM_PREPARO)
    assert SAIU_PARA_ENTREGA not in p.proximos_status()


def test_cancelar_so_antes_do_pagamento(app):
    p = pedido_service.criar_pedido(_cliente(), _itens(app), RETIRADA, None)
    pedido_service.cancelar_pedido(p)
    assert p.status == CANCELADO
    p2 = pedido_service.criar_pedido(_cliente(), _itens(app), RETIRADA, None)
    pagamento_service.pagar(p2, "PIX")
    with pytest.raises(NegocioError):
        pedido_service.cancelar_pedido(p2)


# ---------- Pagamento ----------
CARTAO_OK = {"numero": "4111 1111 1111 1111", "validade": "12/40", "cvv": "123", "titular": "FULANO"}


def _pedido_novo(app):
    return pedido_service.criar_pedido(_cliente(), _itens(app), RETIRADA, None)


def test_pagamento_pix_aprovado(app):
    p = _pedido_novo(app)
    pg = pagamento_service.pagar(p, "PIX")
    assert pg.status == "APROVADO" and p.status == PAGO and pg.valor == p.total


def test_pagamento_cartao_guarda_so_final(app):
    p = _pedido_novo(app)
    pg = pagamento_service.pagar(p, "CARTAO", CARTAO_OK)
    assert pg.cartao_final == "1111"
    # Nenhuma coluna guarda o número completo nem o CVV
    assert "4111111111111111" not in str(pg.__dict__) and "123" != pg.cartao_final


@pytest.mark.parametrize("alteracao", [
    {"numero": "4111 1111 1111 1112"}, {"validade": "01/20"}, {"cvv": "1"}, {"titular": ""},
])
def test_pagamento_cartao_dados_invalidos(app, alteracao):
    p = _pedido_novo(app)
    with pytest.raises(NegocioError):
        pagamento_service.pagar(p, "CARTAO", {**CARTAO_OK, **alteracao})
    assert p.status == AGUARDANDO_PAGAMENTO


def test_pagamento_recusado_permite_nova_tentativa(app):
    p = _pedido_novo(app)
    with pytest.raises(PagamentoRecusado):
        pagamento_service.pagar(p, "CARTAO", {**CARTAO_OK, "numero": "4000 0000 0000 0002"})
    assert p.status == AGUARDANDO_PAGAMENTO and p.pagamentos[0].status == "RECUSADO"
    pagamento_service.pagar(p, "PIX")
    assert p.status == PAGO and p.pagamento_aprovado is not None


def test_nao_paga_duas_vezes_nem_metodo_invalido(app):
    p = _pedido_novo(app)
    with pytest.raises(NegocioError):
        pagamento_service.pagar(p, "BOLETO")
    pagamento_service.pagar(p, "PIX")
    with pytest.raises(NegocioError):
        pagamento_service.pagar(p, "PIX")
