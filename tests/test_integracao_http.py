"""Testes de integração: fluxos completos via HTTP (controllers + serviços + banco + templates)."""
from app.extensions import db
from app.models import Cupcake, Pedido, Usuario
from tests.conftest import ENDERECO, criar_pedido_via_http, ids, login


def texto(resp):
    return resp.get_data(as_text=True)


# ---------- Vitrine ----------
def test_vitrine_lista_apenas_disponiveis(client):
    html = texto(client.get("/"))
    assert "Baunilha" in html and "Chocolate" in html and "Esgotado" not in html


def test_vitrine_busca_e_filtro(client):
    html = texto(client.get("/?q=cacau"))
    assert "Chocolate" in html and "Baunilha" not in html
    assert "Nenhum cupcake encontrado" in texto(client.get("/?q=inexistente"))


def test_detalhe_e_404(client, app):
    assert client.get(f"/cupcake/{ids(app)['Baunilha']}").status_code == 200
    assert client.get("/cupcake/9999").status_code == 404
    assert client.get(f"/cupcake/{ids(app)['Esgotado']}").status_code == 404  # indisponível some


def test_pagina_404_amigavel(client):
    r = client.get("/rota-que-nao-existe")
    assert r.status_code == 404 and "Página não encontrada" in texto(r)


def test_manifest_e_service_worker(client):
    assert client.get("/sw.js").status_code == 200
    assert client.get("/static/manifest.json").status_code == 200


# ---------- Cadastro / login ----------
def test_cadastro_sucesso_e_login_automatico(client):
    r = client.post("/cadastro", data={"nome": "Maria Silva", "email": "MARIA@x.com",
                                       "telefone": "(11) 97777-6666", "senha": "Segura123",
                                       "confirmar_senha": "Segura123"}, follow_redirects=True)
    assert "Conta criada com sucesso" in texto(r)
    assert "Meus pedidos" in texto(r)


def test_cadastro_erros_mostrados_juntos(client):
    r = client.post("/cadastro", data={"nome": "A", "email": "ruim", "telefone": "1",
                                       "senha": "123", "confirmar_senha": "456"})
    html = texto(r)
    for trecho in ("nome completo", "E-mail inválido", "Telefone inválido",
                   "8+ caracteres", "confirmação de senha"):
        assert trecho in html


def test_cadastro_email_duplicado(client):
    r = client.post("/cadastro", data={"nome": "Outro Nome", "email": "cliente@teste.com",
                                       "telefone": "11999998888", "senha": "Segura123",
                                       "confirmar_senha": "Segura123"})
    assert "Já existe uma conta" in texto(r)


def test_login_invalido_mensagem_generica(client):
    r = client.post("/login", data={"email": "cliente@teste.com", "senha": "errada"})
    assert "E-mail ou senha incorretos" in texto(r)
    r = client.post("/login", data={"email": "nao@existe.com", "senha": "qualquer"})
    assert "E-mail ou senha incorretos" in texto(r)  # mesma mensagem: não revela se o e-mail existe


def test_login_nao_redireciona_para_site_externo(client):
    r = client.post("/login?next=https://malicioso.com", data={"email": "cliente@teste.com",
                                                               "senha": "Senha1234"})
    assert r.headers["Location"] == "/"


def test_logout(cliente_logado):
    r = cliente_logado.post("/logout", follow_redirects=True)
    assert "Você saiu" in texto(r)
    assert cliente_logado.get("/pedidos").status_code == 302  # volta a exigir login


# ---------- Carrinho ----------
def test_fluxo_carrinho(client, app):
    cid = ids(app)["Chocolate"]
    client.post(f"/carrinho/adicionar/{cid}", data={"quantidade": 2})
    html = texto(client.get("/carrinho/"))
    assert "Chocolate" in html and "R$ 25,00" in html
    client.post(f"/carrinho/alterar/{cid}", data={"quantidade": 4})
    assert "R$ 50,00" in texto(client.get("/carrinho/"))
    client.post(f"/carrinho/remover/{cid}")
    assert "carrinho está vazio" in texto(client.get("/carrinho/"))


def test_carrinho_quantidade_invalida_mostra_erro(client, app):
    cid = ids(app)["Baunilha"]
    r = client.post(f"/carrinho/adicionar/{cid}", data={"quantidade": 999}, follow_redirects=True)
    assert "quantidade deve estar entre" in texto(r)


# ---------- Checkout ----------
def test_checkout_exige_login(client):
    r = client.get("/checkout")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_checkout_carrinho_vazio_redireciona(cliente_logado):
    r = cliente_logado.get("/checkout", follow_redirects=True)
    assert "carrinho está vazio" in texto(r)


def test_checkout_endereco_invalido_mantem_dados_digitados(cliente_logado, app):
    cid = ids(app)["Baunilha"]
    cliente_logado.post(f"/carrinho/adicionar/{cid}", data={"quantidade": 1})
    r = cliente_logado.post("/checkout", data={**ENDERECO, "cep": "123", "cidade": ""})
    html = texto(r)
    assert "CEP inválido" in html and "Cidade é obrigatório" in html
    assert "Av. Paulista" in html  # não perdeu o que já tinha digitado


# ---------- Fluxo completo ----------
def test_fluxo_completo_compra_pagamento_e_entrega(cliente_logado, admin_logado, app):
    pid = criar_pedido_via_http(cliente_logado, app, quantidade=3)
    assert "Aguardando pagamento" in texto(cliente_logado.get(f"/pedidos/{pid}"))

    r = cliente_logado.post(f"/pedidos/{pid}/pagar", data={"metodo": "PIX"}, follow_redirects=True)
    assert "Pagamento aprovado" in texto(r)

    for etapa in ("EM_PREPARO", "SAIU_PARA_ENTREGA", "ENTREGUE"):
        admin_logado.post(f"/admin/pedidos/{pid}/status", data={"status": etapa})
    html = texto(cliente_logado.get(f"/pedidos/{pid}"))
    assert "Entregue" in html and "transação" in html
    with app.app_context():
        assert db.session.get(Pedido, pid).status == "ENTREGUE"


def test_pagamento_cartao_recusado_via_http(cliente_logado, app):
    pid = criar_pedido_via_http(cliente_logado, app)
    r = cliente_logado.post(f"/pedidos/{pid}/pagar", data={
        "metodo": "CARTAO", "numero": "4000 0000 0000 0002", "validade": "12/40",
        "cvv": "123", "titular": "Fulano"})
    assert "Pagamento recusado" in texto(r)


def test_pagamento_cartao_invalido_lista_erros(cliente_logado, app):
    pid = criar_pedido_via_http(cliente_logado, app)
    r = cliente_logado.post(f"/pedidos/{pid}/pagar", data={"metodo": "CARTAO", "numero": "1"})
    html = texto(r)
    assert "Número do cartão inválido" in html and "CVV inválido" in html


def test_cancelar_pedido(cliente_logado, app):
    pid = criar_pedido_via_http(cliente_logado, app)
    r = cliente_logado.post(f"/pedidos/{pid}/cancelar", follow_redirects=True)
    assert "Pedido cancelado" in texto(r)


# ---------- Segurança / autorização ----------
def test_cliente_nao_ve_pedido_de_outro(app, cliente_logado):
    pid = criar_pedido_via_http(cliente_logado, app)
    with app.app_context():
        outro = Usuario(nome="Outra Pessoa", email="outra@x.com", telefone="11911112222")
        outro.definir_senha("Outra1234")
        db.session.add(outro)
        db.session.commit()
    c2 = app.test_client()
    login(c2, "outra@x.com", "Outra1234")
    assert c2.get(f"/pedidos/{pid}").status_code == 404
    assert c2.post(f"/pedidos/{pid}/cancelar").status_code == 404
    assert c2.get(f"/pedidos/{pid}/pagar").status_code == 404


def test_admin_protegido(app, cliente_logado, admin_logado):
    anonimo = app.test_client()  # `client` e `cliente_logado` são o mesmo objeto, então criamos outro
    assert anonimo.get("/admin/").status_code == 302         # anônimo → login
    assert cliente_logado.get("/admin/").status_code == 403  # cliente comum → negado
    assert cliente_logado.post("/admin/pedidos/1/status", data={"status": "PAGO"}).status_code == 403
    assert admin_logado.get("/admin/").status_code == 200


def test_csrf_bloqueia_post_sem_token(app):
    app.config["TESTING"] = False  # liga a verificação CSRF
    c = app.test_client()
    r = c.post("/login", data={"email": "cliente@teste.com", "senha": "Senha1234"})
    assert r.status_code == 400


def test_admin_transicao_invalida_mostra_erro(cliente_logado, admin_logado, app):
    pid = criar_pedido_via_http(cliente_logado, app)
    r = admin_logado.post(f"/admin/pedidos/{pid}/status", data={"status": "ENTREGUE"},
                          follow_redirects=True)
    assert "Transição inválida" in texto(r)


# ---------- Admin: cupcakes ----------
def test_admin_cria_e_edita_cupcake(admin_logado, app):
    with app.app_context():
        cat_id = db.session.scalar(db.select(Cupcake.categoria_id))
    r = admin_logado.post("/admin/cupcakes/novo", data={
        "nome": "Brigadeiro", "descricao": "Cupcake de brigadeiro cremoso", "preco": "14,00",
        "categoria_id": cat_id, "disponivel": "on"}, follow_redirects=True)
    assert "Cupcake salvo" in texto(r) and "Brigadeiro" in texto(r)
    with app.app_context():
        novo = db.session.scalar(db.select(Cupcake).where(Cupcake.nome == "Brigadeiro"))
        nid = novo.id
    # desmarcar "disponível" tira da vitrine
    admin_logado.post(f"/admin/cupcakes/{nid}/editar", data={
        "nome": "Brigadeiro", "descricao": "Cupcake de brigadeiro cremoso", "preco": "14,00",
        "categoria_id": cat_id})
    assert "Brigadeiro" not in texto(admin_logado.get("/"))


def test_admin_cupcake_invalido(admin_logado, app):
    r = admin_logado.post("/admin/cupcakes/novo", data={"nome": "x", "descricao": "y", "preco": "-1",
                                                        "categoria_id": 1})
    html = texto(r)
    assert "ao menos 3 caracteres" in html and "maior que zero" in html
