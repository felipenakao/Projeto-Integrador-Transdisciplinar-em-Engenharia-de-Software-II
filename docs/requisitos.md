# Requisitos

## Escopo

Incluído: catálogo com busca e filtro, cadastro e login, carrinho, checkout com entrega ou retirada, pagamento por Pix e cartão (simulados), acompanhamento do pedido e painel administrativo (pedidos e cupcakes).

Fora do escopo: frete por distância, gateway de pagamento real, cupons, avaliações, notificações por e-mail/WhatsApp e upload de fotos (a vitrine usa emojis).

## Atores

| Ator | Descrição |
|---|---|
| Visitante | Navega na vitrine sem login |
| Cliente | Usuário cadastrado que compra e acompanha pedidos |
| Administrador | Gerencia cupcakes e atualiza o status dos pedidos |
| Gateway de pagamento | Sistema externo (simulado) que aprova ou recusa pagamentos |

## Requisitos funcionais

| ID | Requisito | Prioridade |
|---|---|---|
| RF01 | Listar cupcakes disponíveis com preço e categoria | Must |
| RF02 | Buscar por nome/ingrediente e filtrar por categoria | Should |
| RF03 | Exibir detalhes do cupcake | Must |
| RF04 | Cadastro e login | Must |
| RF05 | Carrinho: adicionar, alterar quantidade (1 a 50) e remover | Must |
| RF06 | Checkout com entrega ou retirada | Must |
| RF07 | Pagamento por Pix ou cartão | Must |
| RF08 | Não armazenar dados sensíveis do cartão (só os 4 últimos dígitos) | Must |
| RF09 | Acompanhar o status do pedido | Must |
| RF10 | Frete grátis a partir de R$ 120,00 | Could |
| RF11 | Cancelar pedido ainda não pago | Should |
| RF12 | Admin atualiza o status dos pedidos | Must |
| RF13 | Admin cadastra, edita e oculta cupcakes | Should |

## Requisitos não funcionais

| ID | Categoria | Requisito |
|---|---|---|
| RNF01 | Segurança | Senhas com hash; nenhum dado de cartão armazenado além dos 4 últimos dígitos |
| RNF02 | Segurança | Proteção contra CSRF, open redirect e acesso a pedidos de terceiros |
| RNF03 | Usabilidade | Layout responsivo, campos com `label`, navegação por teclado |
| RNF04 | Confiabilidade | Erros tratados com mensagem clara, sem exibir stack trace |
| RNF05 | Manutenibilidade | MVC com camada de serviços e testes automatizados |
| RNF06 | Portabilidade | PostgreSQL em produção, SQLite em desenvolvimento (`DATABASE_URL`) |
| RNF07 | Desempenho | Sem framework JS pesado; estáticos em cache via service worker |
| RNF08 | Integridade | Regras também no banco (CHECK, FK, UNIQUE) |
