# parser.py
# -*- coding: utf-8 -*-
"""
Foydalanuvchi yozgan matndan summalar va valyutalarni ajratib oladi.

Qo'llab-quvvatlanadigan formatlar:
  "1.36 usd"        -> 1.36 USD, maqsad ko'rsatilmagan (default: so'm)
  "27 stars"        -> 27 STARS
  "1 ton usd"       -> 1 TON dan USD ga
  "50000 som ton"   -> 50000 UZS dan TON ga
  "$10"             -> 10 USD
"""
import re
from typing import Optional, Tuple, List

# Valyuta nomlarining turli yozilishlari -> ichki kod
ALIASES = {
    "USD": {"usd", "dollar", "dollor", "dollars", "$"},
    "RUB": {"rub", "rubl", "rubli", "rubles", "ruble"},
    "TON": {"ton", "tons"},
    "STARS": {"stars", "star", "stras", "★", "⭐"},
    "UZS": {"som", "so'm", "sum", "sўm", "uzs", "soum", "so’m"},
}

# Tezkor teskari lug'at: so'z -> kod
WORD_TO_CODE = {}
for code, words in ALIASES.items():
    for w in words:
        WORD_TO_CODE[w.lower()] = code


def normalize_currency(word: str) -> Optional[str]:
    if not word:
        return None
    w = word.strip().lower().strip(".,!?")
    return WORD_TO_CODE.get(w)


def _clean_number(raw: str) -> Optional[float]:
    """'50,000' yoki '1.36' yoki '$10' dagi sonni float ga o'giradi."""
    raw = raw.replace("$", "").replace(",", "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


ParsedLine = Tuple[float, str, Optional[str]]  # (amount, source_code, target_code_or_None)


def parse_line(line: str) -> Optional[ParsedLine]:
    line = line.strip()
    if not line:
        return None

    tokens = line.split()
    if not tokens:
        return None

    first = tokens[0]
    source = None
    rest = tokens[1:]

    if first.startswith("$"):
        amount = _clean_number(first)
        source = "USD"
    else:
        amount = _clean_number(first)

    if amount is None:
        return None

    if source is None:
        if not rest:
            return None
        source = normalize_currency(rest[0])
        rest = rest[1:]

    if source is None:
        return None

    target = None
    if rest:
        target = normalize_currency(rest[0])

    return (amount, source, target)


def parse_message(text: str) -> List[ParsedLine]:
    """Ko'p qatorli xabarni qatorma-qator parse qiladi, tushunarli qatorlarni qaytaradi."""
    results = []
    for line in text.splitlines():
        parsed = parse_line(line)
        if parsed:
            results.append(parsed)
    return results
