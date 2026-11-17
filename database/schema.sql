-- =============================================================
-- Projeto Físico do Banco de Dados — Cupcakes Gourmet (PostgreSQL 14+)
-- Gerado a partir dos modelos SQLAlchemy (app/models) e revisado.
-- Uso:  psql "$DATABASE_URL" -f database/schema.sql
-- =============================================================

CREATE TABLE categoria (
	id SERIAL NOT NULL, 
	nome VARCHAR(60) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nome)
);


CREATE TABLE usuario (
	id SERIAL NOT NULL, 
	nome VARCHAR(120) NOT NULL, 
	email VARCHAR(160) NOT NULL, 
	telefone VARCHAR(20) NOT NULL, 
	senha_hash VARCHAR(255) NOT NULL, 
	is_admin BOOLEAN NOT NULL, 
	criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_usuario_email ON usuario (email);

CREATE TABLE cupcake (
	id SERIAL NOT NULL, 
	categoria_id INTEGER NOT NULL, 
	nome VARCHAR(100) NOT NULL, 
	descricao VARCHAR(400) NOT NULL, 
	preco NUMERIC(10, 2) NOT NULL, 
	emoji VARCHAR(8) NOT NULL, 
	disponivel BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_cupcake_preco_positivo CHECK (preco > 0), 
	FOREIGN KEY(categoria_id) REFERENCES categoria (id)
);

CREATE INDEX ix_cupcake_categoria_id ON cupcake (categoria_id);

CREATE TABLE endereco (
	id SERIAL NOT NULL, 
	usuario_id INTEGER NOT NULL, 
	cep VARCHAR(9) NOT NULL, 
	logradouro VARCHAR(160) NOT NULL, 
	numero VARCHAR(10) NOT NULL, 
	complemento VARCHAR(80), 
	bairro VARCHAR(80) NOT NULL, 
	cidade VARCHAR(80) NOT NULL, 
	uf VARCHAR(2) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuario (id)
);

CREATE INDEX ix_endereco_usuario_id ON endereco (usuario_id);

CREATE TABLE pedido (
	id SERIAL NOT NULL, 
	usuario_id INTEGER NOT NULL, 
	endereco_id INTEGER, 
	tipo_entrega VARCHAR(10) NOT NULL, 
	status VARCHAR(25) NOT NULL, 
	subtotal NUMERIC(10, 2) NOT NULL, 
	taxa_entrega NUMERIC(10, 2) NOT NULL, 
	total NUMERIC(10, 2) NOT NULL, 
	observacoes VARCHAR(300), 
	criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_pedido_tipo CHECK (tipo_entrega IN ('ENTREGA','RETIRADA')), 
	CONSTRAINT ck_pedido_total CHECK (total >= 0), 
	FOREIGN KEY(usuario_id) REFERENCES usuario (id), 
	FOREIGN KEY(endereco_id) REFERENCES endereco (id)
);

CREATE INDEX ix_pedido_usuario_id ON pedido (usuario_id);

CREATE TABLE item_pedido (
	id SERIAL NOT NULL, 
	pedido_id INTEGER NOT NULL, 
	cupcake_id INTEGER NOT NULL, 
	quantidade INTEGER NOT NULL, 
	preco_unitario NUMERIC(10, 2) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_item_quantidade CHECK (quantidade > 0), 
	FOREIGN KEY(pedido_id) REFERENCES pedido (id), 
	FOREIGN KEY(cupcake_id) REFERENCES cupcake (id)
);

CREATE INDEX ix_item_pedido_pedido_id ON item_pedido (pedido_id);

CREATE TABLE pagamento (
	id SERIAL NOT NULL, 
	pedido_id INTEGER NOT NULL, 
	metodo VARCHAR(10) NOT NULL, 
	status VARCHAR(12) NOT NULL, 
	valor NUMERIC(10, 2) NOT NULL, 
	transacao_id VARCHAR(40) NOT NULL, 
	cartao_final VARCHAR(4), 
	criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_pagamento_metodo CHECK (metodo IN ('PIX','CARTAO')), 
	CONSTRAINT ck_pagamento_status CHECK (status IN ('APROVADO','RECUSADO')), 
	FOREIGN KEY(pedido_id) REFERENCES pedido (id), 
	UNIQUE (transacao_id)
);

CREATE INDEX ix_pagamento_pedido_id ON pagamento (pedido_id);
