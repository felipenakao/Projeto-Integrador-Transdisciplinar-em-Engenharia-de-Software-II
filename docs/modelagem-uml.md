# Modelagem UML

Diagramas em Mermaid (renderizados automaticamente pelo GitHub).

## Casos de uso

```mermaid
flowchart LR
  V([Visitante])
  C([Cliente])
  A([Administrador])
  G([Gateway de pagamento])

  subgraph Sistema[Cupcakes Gourmet]
    UC1((Ver vitrine))
    UC2((Buscar / filtrar))
    UC3((Ver detalhes))
    UC4((Cadastrar-se))
    UC5((Fazer login))
    UC6((Gerenciar carrinho))
    UC7((Finalizar pedido))
    UC8((Pagar pedido))
    UC9((Acompanhar pedido))
    UC10((Cancelar pedido))
    UC11((Gerenciar cupcakes))
    UC12((Atualizar status do pedido))
  end

  V --- UC1 & UC3 & UC4 & UC5
  UC1 -.->|extend| UC2
  C --- UC6 & UC7 & UC8 & UC9 & UC10
  UC7 -.->|include| UC5
  UC8 --- G
  A --- UC11 & UC12
  C -. herda de .-> V
```

## Diagrama de classes

```mermaid
classDiagram
  class Usuario {
    +int id
    +string nome
    +string email
    +string telefone
    +string senha_hash
    +bool is_admin
    +definir_senha(senha)
    +conferir_senha(senha) bool
  }
  class Endereco {
    +int id
    +string cep
    +string logradouro
    +string numero
    +string complemento
    +string bairro
    +string cidade
    +string uf
  }
  class Categoria { +int id +string nome }
  class Cupcake {
    +int id
    +string nome
    +string descricao
    +decimal preco
    +string emoji
    +bool disponivel
    +validar(nome, descricao, preco)$
  }
  class Pedido {
    +int id
    +string tipo_entrega
    +string status
    +decimal subtotal
    +decimal taxa_entrega
    +decimal total
    +string observacoes
    +pode_ir_para(status) bool
    +mudar_status(status)
    +proximos_status() list
  }
  class ItemPedido {
    +int id
    +int quantidade
    +decimal preco_unitario
    +total() decimal
  }
  class Pagamento {
    +int id
    +string metodo
    +string status
    +decimal valor
    +string transacao_id
    +string cartao_final
  }

  Usuario "1" --> "0..*" Endereco
  Usuario "1" --> "0..*" Pedido
  Categoria "1" --> "0..*" Cupcake
  Pedido "1" *-- "1..*" ItemPedido
  ItemPedido "0..*" --> "1" Cupcake
  Pedido "0..*" --> "0..1" Endereco : entrega em
  Pedido "1" *-- "0..*" Pagamento
```

`ItemPedido.preco_unitario` guarda o preço no momento da compra, então alterar o preço do cupcake não afeta pedidos antigos. Um pedido pode ter vários `Pagamento` porque as tentativas recusadas também são registradas.

## Sequência: compra com pagamento

```mermaid
sequenceDiagram
  actor Cl as Cliente
  participant UI as Navegador
  participant Ct as Controller
  participant Sv as Serviços
  participant DB as Banco
  participant Gw as Gateway (simulado)

  Cl->>UI: Preenche checkout
  UI->>Ct: POST /checkout
  Ct->>Sv: criar_pedido(usuario, itens, tipo, endereço)
  Sv->>Sv: valida endereço, calcula frete e total
  Sv->>DB: INSERT pedido, item_pedido, endereco
  Sv-->>Ct: Pedido (AGUARDANDO_PAGAMENTO)
  Ct-->>UI: redireciona para /pedidos/{id}/pagar
  Cl->>UI: Escolhe cartão e confirma
  UI->>Ct: POST /pedidos/{id}/pagar
  Ct->>Sv: pagar(pedido, "CARTAO", dados)
  Sv->>Gw: valida (Luhn, validade, CVV) e autoriza
  alt aprovado
    Gw-->>Sv: APROVADO
    Sv->>DB: INSERT pagamento (4 últimos dígitos), pedido → PAGO
  else recusado
    Gw-->>Sv: RECUSADO
    Sv->>DB: INSERT pagamento (RECUSADO)
  end
  Ct-->>UI: mensagem de resultado
```

## Estados do pedido

```mermaid
stateDiagram-v2
  [*] --> AGUARDANDO_PAGAMENTO
  AGUARDANDO_PAGAMENTO --> PAGO: pagamento aprovado
  AGUARDANDO_PAGAMENTO --> CANCELADO
  PAGO --> EM_PREPARO
  PAGO --> CANCELADO
  EM_PREPARO --> SAIU_PARA_ENTREGA: tipo = ENTREGA
  EM_PREPARO --> PRONTO_PARA_RETIRADA: tipo = RETIRADA
  EM_PREPARO --> CANCELADO
  SAIU_PARA_ENTREGA --> ENTREGUE
  PRONTO_PARA_RETIRADA --> ENTREGUE
  ENTREGUE --> [*]
  CANCELADO --> [*]
```

Implementado em `app/models/pedido.py` (`TRANSICOES`).
