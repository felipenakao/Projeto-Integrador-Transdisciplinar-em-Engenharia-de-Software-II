# Arquitetura

## Padrão MVC com camada de serviços

| Camada | Pasta | Responsabilidade |
|---|---|---|
| Model | `app/models/` | Entidades e regras de domínio (máquina de estados do pedido, validação do cupcake) |
| View | `app/templates/`, `app/static/` | Templates Jinja2, CSS, JS e PWA |
| Controller | `app/controllers/` | Recebe a requisição, chama os serviços e escolhe a view |
| Services | `app/services/` | Regras de negócio: carrinho, frete, pedido, pagamento, validadores |

```
Navegador → Controller → Service → Model → Banco
               ↑                      
               └──── View (Jinja2) ←──┘
```

Os serviços mantêm os controllers enxutos e permitem testar as regras sem HTTP.

## Estrutura

```
wsgi.py                  ponto de entrada
app/__init__.py          factory do app (banco, login, blueprints, CSRF, handlers de erro, comandos CLI)
app/config.py            configurações (banco, chave secreta, taxa de entrega, frete grátis, limite por item)
app/models/              usuario.py, cupcake.py, pedido.py
app/controllers/         vitrine.py, auth.py, carrinho.py, pedidos.py, admin.py
app/services/            carrinho.py, pedido_service.py, pagamento_service.py, validadores.py, erros.py
app/templates/           base.html e uma pasta por área
app/static/              css, js, sw.js, manifest.json
app/seed.py              dados de exemplo e usuário admin
database/schema.sql      DDL (PostgreSQL)
tests/                   pytest
```

## Rotas

| Rota | Acesso | Função |
|---|---|---|
| `GET /` | todos | Vitrine com busca e filtro |
| `GET /cupcake/<id>` | todos | Detalhe do cupcake |
| `/cadastro`, `/login`, `POST /logout` | visitante/cliente | Autenticação |
| `GET /carrinho/`, `POST /carrinho/adicionar\|alterar\|remover/<id>` | todos | Carrinho |
| `/checkout` | cliente | Criar pedido |
| `/pedidos/<id>/pagar` | cliente | Pagamento |
| `GET /pedidos`, `GET /pedidos/<id>` | cliente | Lista e detalhe |
| `POST /pedidos/<id>/cancelar` | cliente | Cancelar pedido não pago |
| `GET /admin/`, `POST /admin/pedidos/<id>/status` | admin | Pedidos e mudança de status |
| `/admin/cupcakes`, `/novo`, `/<id>/editar` | admin | Gestão de cupcakes |

## Decisões de implementação

- **Carrinho na sessão:** dicionário `{cupcake_id: quantidade}` em cookie assinado; só vira dado persistente quando o pedido é criado.
- **Pedido:** criado com status `AGUARDANDO_PAGAMENTO`; o preço de cada item é copiado para `item_pedido`.
- **Frete:** R$ 8,00; grátis a partir de R$ 120,00 e na retirada.
- **Pagamento simulado:** Pix sempre aprova; cartão valida Luhn, validade e CVV; final `0002` é recusado. Só os 4 últimos dígitos são gravados.
- **Status:** transições definidas em `TRANSICOES` (`models/pedido.py`); o admin só vê as próximas etapas válidas.
- **Cupcakes:** "indisponível" oculta o item da vitrine sem remover o histórico.
- **PWA:** o service worker faz cache apenas de CSS, JS e ícone; páginas de pedido e pagamento nunca são cacheadas.

## Tratamento de erros

| Camada | Estratégia |
|---|---|
| Serviços | Lançam `NegocioError` com mensagens amigáveis |
| Controllers | Capturam `NegocioError`, usam `flash()` e preservam os dados do formulário |
| Aplicação | Handlers globais 400/403/404/500; `rollback` no 500 |
| Banco | `CHECK`, `UNIQUE` e `FK` como segunda linha de defesa |

## Segurança

- Hash de senha (PBKDF2 via Werkzeug)
- Token CSRF em todo POST
- Cabeçalhos `X-Frame-Options`, `nosniff` e `Referrer-Policy`
- Pedidos acessíveis apenas pelo dono (404 para outros) e painel restrito ao admin (403)
- Mensagem genérica no login e proteção contra open redirect
- `SECRET_KEY` por variável de ambiente

## Limitações

- Pagamento simulado, sem cobrança real
- Sem upload de fotos
- Sem recuperação de senha
- Carrinho some ao limpar os cookies
- Sem rate limit de login
