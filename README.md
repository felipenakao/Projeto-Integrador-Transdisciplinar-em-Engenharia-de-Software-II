# Cupcakes Gourmet

Sistema web para uma loja de cupcakes: vitrine, carrinho, pedido, pagamento (simulado) e acompanhamento de entrega, com painel administrativo.

## Stack

- Python 3.9+, Flask, Flask-SQLAlchemy, Flask-Login
- PostgreSQL em produção, SQLite em desenvolvimento e testes
- HTML, CSS e JavaScript puro (PWA)
- pytest e pytest-cov
- gunicorn

## Rodando localmente

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export FLASK_APP=wsgi.py                             # PowerShell: $env:FLASK_APP="wsgi.py"
flask seed                                           # cria tabelas, cupcakes e o admin
flask run                                            # http://127.0.0.1:5000
```

Admin de desenvolvimento: `admin@cupcakes.local` / `Admin1234`. Em produção, defina `ADMIN_EMAIL` e `ADMIN_PASSWORD` antes de rodar `flask seed`.

### Com PostgreSQL

```bash
export DATABASE_URL="postgresql://usuario:senha@host:5432/cupcakes"
export SECRET_KEY="chave-longa-e-aleatoria"
psql "$DATABASE_URL" -f database/schema.sql          # ou: flask init-db
flask seed
```

## Testes

```bash
pytest -v
pytest --cov=app --cov-report=term-missing
```

## Deploy (Render)

1. Suba o repositório no GitHub.
2. No Render, crie um Blueprint apontando para o repositório (usa o `render.yaml`).
3. Após o primeiro deploy, rode `flask seed` no shell do serviço.

## Uso

**Cliente:** navegar pela vitrine, adicionar ao carrinho, criar conta (senha com 8+ caracteres, letras e números), finalizar com entrega (R$ 8,00, grátis a partir de R$ 120,00) ou retirada, e pagar por Pix ou cartão. Pedidos não pagos podem ser cancelados em "Meus pedidos".

Cartões de teste: `4111 1111 1111 1111` com validade futura e CVV de 3 dígitos é aprovado; número terminado em `0002` é recusado.

**Administrador:** menu Admin para avançar o status dos pedidos e cadastrar, editar ou ocultar cupcakes.

## Documentação

- [Requisitos](docs/requisitos.md)
- [Modelagem UML](docs/modelagem-uml.md)
- [Banco de dados](docs/banco-de-dados.md)
- [Arquitetura](docs/arquitetura.md)
