# bot.py
# -*- coding: utf-8 -*-
"""
Valyuta konvertatsiya boti.
Ishga tushirish: python bot.py
"""
import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from config import BOT_TOKEN, ADMIN_IDS
from rates import rates_store
from parser import parse_message, ParsedLine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

CURRENCY_EMOJI = {
    "USD": "❤️",
    "RUB": "👍",
    "TON": "💕",
    "STARS": "⭐",
    "UZS": "💰",
}


# ---------- yordamchi funksiyalar ----------

def to_som(amount: float, source: str) -> float:
    rate = rates_store.get(source)
    if rate is None:
        return 0.0
    return amount * rate


def from_som(som_amount: float, target: str) -> float:
    rate = rates_store.get(target)
    if not rate:
        return 0.0
    return som_amount / rate


def fmt_amount(value: float) -> str:
    """Umumiy holatlar uchun (masalan noma'lum valyuta)."""
    if abs(value - round(value)) < 0.005:
        return f"{value:,.0f}"
    return f"{value:,.4f}".rstrip("0").rstrip(".")


# Har bir valyuta uchun necha xonali kasr ko'rsatish kerakligi
DECIMALS = {
    "USD": 2,
    "RUB": 2,
    "TON": 4,
    "STARS": 0,
    "UZS": 0,
}


def fmt_for(code: str, value: float) -> str:
    decimals = DECIMALS.get(code, 2)
    if decimals == 0:
        return f"{value:,.0f}"
    text = f"{value:,.{decimals}f}"
    # keraksiz nollarni olib tashlash (masalan 5.0000 -> 5, 5.0100 -> 5.01)
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def emoji_for(code: str) -> str:
    return CURRENCY_EMOJI.get(code, "💠")


# ---------- javob formatlash ----------

def format_direct_conversion(amount: float, source: str, target: str) -> str:
    som = to_som(amount, source)
    result = from_som(som, target)
    return (
        f"{emoji_for(source)} {fmt_for(source, amount)} {source} "
        f"→ {fmt_for(target, result)} {target}\n\n"
        f"Kurs: {rates_store.current_time_label()}"
    )


def format_to_som(amount: float, source: str) -> str:
    som = to_som(amount, source)
    return (
        f"{emoji_for(source)} {fmt_for(source, amount)} {source} "
        f"→ {fmt_for('UZS', som)} so'm\n\n"
        f"Kurs: {rates_store.current_time_label()}"
    )


def format_summary(parsed_lines: list) -> str:
    total_som = sum(to_som(a, s) for a, s, t in parsed_lines)

    usd = from_som(total_som, "USD")
    stars = from_som(total_som, "STARS")
    ton = from_som(total_som, "TON")

    lines = [
        f"💖 {fmt_for('USD', usd)} USD  →  {fmt_for('UZS', total_som)} so'm",
        f"⭐ {fmt_for('STARS', stars)} Stars",
        f"💕 {fmt_for('TON', ton)} TON",
        f"❤️ {fmt_for('USD', usd)} USD",
        "",
        f"Kurs: {rates_store.current_time_label()}",
    ]
    return "\n".join(lines)


# ---------- handlerlar ----------

@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "Salom! 👋\n\n"
        "Men valyuta konvertatsiya botiman.\n\n"
        "Hozirgi kurslar:\n"
        f"❤️ 1 USD — {fmt_amount(rates_store.get('USD'))} so'm\n"
        f"👍 1 RUB — {fmt_amount(rates_store.get('RUB'))} so'm\n"
        f"💕 1 TON — {fmt_amount(rates_store.get('TON'))} so'm\n"
        f"⭐ 1 Stars — {fmt_amount(rates_store.get('STARS'))} so'm\n\n"
        "Qanday ishlatish:\n"
        "• 1 ton — necha so'm\n"
        "• 100 stars — necha so'm\n"
        "• 1 ton usd — TON dan USD ga\n"
        "• 50000 som ton — so'mdan TON ga\n"
        "• $10 — USD dan so'mga\n\n"
        "Bir nechta qator yozsangiz, hammasini yig'ib umumiy natijani chiqarib beraman."
    )
    await message.answer(text)


@dp.message(Command("setstars"))
async def cmd_set_stars(message: Message):
    """Admin Stars kursini qo'lda belgilaydi: /setstars 240"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu buyruq faqat admin uchun.")
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Format: /setstars 240")
        return
    try:
        value = float(parts[1])
    except ValueError:
        await message.answer("Son noto'g'ri kiritildi.")
        return
    rates_store.set_rate("STARS", value)
    await message.answer(f"⭐ Stars kursi yangilandi: 1 Stars = {fmt_amount(value)} so'm")


@dp.message(Command("kurs"))
async def cmd_kurs(message: Message):
    await cmd_start(message)


@dp.message(F.text)
async def handle_text(message: Message):
    parsed = parse_message(message.text)
    if not parsed:
        return  # tanish valyuta topilmadi, e'tiborsiz qoldiramiz

    if len(parsed) == 1:
        amount, source, target = parsed[0]
        if target:
            reply = format_direct_conversion(amount, source, target)
        else:
            reply = format_to_som(amount, source)
    else:
        reply = format_summary(parsed)

    await message.reply(reply)


# ---------- ishga tushirish ----------

async def main():
    # Fon rejimida kurslarni har doim yangilab turadigan vazifani ishga tushiramiz
    asyncio.create_task(rates_store.background_updater())
    logger.info("Bot ishga tushdi.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
