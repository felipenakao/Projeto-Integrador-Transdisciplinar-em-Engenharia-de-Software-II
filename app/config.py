"""Configurações da aplicação (12-factor: tudo sensível vem de variáveis de ambiente)."""
import os
from decimal import Decimal


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "sqlite:///cupcakes_dev.db")
    # Render/Heroku entregam "postgres://", mas o SQLAlchemy exige "postgresql://".
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-troque-em-producao")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Regras de negócio da loja
    TAXA_ENTREGA = Decimal("8.00")
    FRETE_GRATIS_ACIMA_DE = Decimal("120.00")
    QUANTIDADE_MAXIMA_POR_ITEM = 50


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "teste"
    WTF_CSRF_ENABLED = False
