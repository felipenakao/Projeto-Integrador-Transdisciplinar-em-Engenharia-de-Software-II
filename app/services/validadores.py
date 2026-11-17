"""Funções puras de validação (fáceis de testar unitariamente)."""

from __future__ import annotations
import re
from datetime import date

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
    "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


def somente_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def email_valido(email: str) -> bool:
    return bool(email and EMAIL_RE.match(email.strip()))


def telefone_valido(telefone: str) -> bool:
    return len(somente_digitos(telefone)) in (10, 11)


def cep_valido(cep: str) -> bool:
    return len(somente_digitos(cep)) == 8


def formatar_cep(cep: str) -> str:
    d = somente_digitos(cep)
    return f"{d[:5]}-{d[5:]}"


def senha_valida(senha: str) -> bool:
    return bool(senha) and len(senha) >= 8 and any(c.isdigit() for c in senha) \
        and any(c.isalpha() for c in senha)


def cartao_luhn_valido(numero: str) -> bool:
    d = somente_digitos(numero)
    if not 13 <= len(d) <= 19:
        return False
    soma = 0
    for i, c in enumerate(reversed(d)):
        n = int(c)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        soma += n
    return soma % 10 == 0


def validade_cartao_ok(mm_aa: str, hoje: date | None = None) -> bool:
    """Aceita 'MM/AA'. Válido até o último dia do mês informado."""
    hoje = hoje or date.today()
    m = re.fullmatch(r"(\d{2})/(\d{2})", (mm_aa or "").strip())
    if not m:
        return False
    mes, ano = int(m.group(1)), 2000 + int(m.group(2))
    if not 1 <= mes <= 12:
        return False
    return (ano, mes) >= (hoje.year, hoje.month)


def cvv_valido(cvv: str) -> bool:
    return bool(re.fullmatch(r"\d{3,4}", (cvv or "").strip()))
