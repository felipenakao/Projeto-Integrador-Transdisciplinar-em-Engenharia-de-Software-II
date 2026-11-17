"""Testes unitários das funções puras de validação."""
from datetime import date

import pytest

from app.services import validadores as v


@pytest.mark.parametrize("email,esperado", [
    ("ana@exemplo.com", True), ("ana@exemplo", False), ("ana exemplo.com", False), ("", False),
])
def test_email(email, esperado):
    assert v.email_valido(email) is esperado


@pytest.mark.parametrize("tel,esperado", [
    ("(11) 99999-9999", True), ("1133334444", True), ("99999", False), ("", False),
])
def test_telefone(tel, esperado):
    assert v.telefone_valido(tel) is esperado


def test_cep_e_formatacao():
    assert v.cep_valido("01310-100") and v.cep_valido("01310100")
    assert not v.cep_valido("123")
    assert v.formatar_cep("01310100") == "01310-100"


@pytest.mark.parametrize("senha,esperado", [
    ("Senha1234", True), ("curta1", False), ("somenteletras", False), ("12345678", False),
])
def test_senha(senha, esperado):
    assert v.senha_valida(senha) is esperado


@pytest.mark.parametrize("numero,esperado", [
    ("4111 1111 1111 1111", True), ("4111111111111111", True),
    ("4111 1111 1111 1112", False), ("1234", False), ("abcd", False),
])
def test_luhn(numero, esperado):
    assert v.cartao_luhn_valido(numero) is esperado


def test_validade_cartao():
    hoje = date(2026, 11, 15)
    assert v.validade_cartao_ok("11/26", hoje)      # vale até o fim do mês
    assert not v.validade_cartao_ok("10/26", hoje)  # vencido
    assert v.validade_cartao_ok("01/30", hoje)
    assert not v.validade_cartao_ok("13/30", hoje)  # mês inexistente
    assert not v.validade_cartao_ok("1130", hoje)   # formato errado


def test_cvv():
    assert v.cvv_valido("123") and v.cvv_valido("1234")
    assert not v.cvv_valido("12") and not v.cvv_valido("abc")
