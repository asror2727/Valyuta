# rates.py
# -*- coding: utf-8 -*-
"""
Kurslarni saqlash va tashqi manbalardan avtomatik yangilab turish.
"""
import json
import os
import asyncio
import logging
from datetime import datetime

import aiohttp

from config import (
    DEFAULT_RATES,
    UPDATE_INTERVAL_SECONDS,
    RATES_STORAGE_FILE,
    CBU_API_URL,
    COINGECKO_TON_URL,
)

logger = logging.getLogger("rates")


class RatesStore:
    """
    1 birlik = necha so'm formatida kurslarni ushlab turadi.
    Masalan: rates["USD"] = 11974.0  ->  1 USD = 11974 so'm
    """

    def __init__(self):
        self.rates = dict(DEFAULT_RATES)
        self.last_updated = None
        self._load_from_disk()

    # ---------- saqlash / o'qish ----------

    def _load_from_disk(self):
        if os.path.exists(RATES_STORAGE_FILE):
            try:
                with open(RATES_STORAGE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.rates.update(data.get("rates", {}))
                    self.last_updated = data.get("last_updated")
            except Exception as e:
                logger.warning(f"rates_state.json o'qishda xato: {e}")

    def _save_to_disk(self):
        try:
            with open(RATES_STORAGE_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {"rates": self.rates, "last_updated": self.last_updated},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            logger.warning(f"rates_state.json yozishda xato: {e}")

    # ---------- qo'lda o'zgartirish (masalan Stars uchun) ----------

    def set_rate(self, code: str, value: float):
        self.rates[code.upper()] = float(value)
        self.last_updated = datetime.now().strftime("%H:%M")
        self._save_to_disk()

    def get(self, code: str):
        return self.rates.get(code.upper())

    def current_time_label(self):
        return self.last_updated or datetime.now().strftime("%H:%M")

    # ---------- avtomatik yangilash ----------

    async def _fetch_cbu(self, session: aiohttp.ClientSession):
        """CBU (O'zbekiston Markaziy banki) dan USD va RUB kursini oladi."""
        try:
            async with session.get(CBU_API_URL, timeout=10) as resp:
                data = await resp.json()
                for item in data:
                    code = item.get("Ccy")
                    rate = item.get("Rate")
                    if code in ("USD", "RUB") and rate:
                        self.rates[code] = float(rate)
        except Exception as e:
            logger.warning(f"CBU kursini olishda xato: {e}")

    async def _fetch_ton(self, session: aiohttp.ClientSession):
        """CoinGecko orqali TON/USD narxini olib, so'mga o'giradi."""
        try:
            async with session.get(COINGECKO_TON_URL, timeout=10) as resp:
                data = await resp.json()
                ton_usd = data.get("the-open-network", {}).get("usd")
                if ton_usd and self.rates.get("USD"):
                    self.rates["TON"] = float(ton_usd) * self.rates["USD"]
        except Exception as e:
            logger.warning(f"TON kursini olishda xato: {e}")

    async def refresh_once(self):
        async with aiohttp.ClientSession() as session:
            await asyncio.gather(
                self._fetch_cbu(session),
                self._fetch_ton(session),
            )
        self.last_updated = datetime.now().strftime("%H:%M")
        self._save_to_disk()
        logger.info(f"Kurslar yangilandi: {self.rates}")

    async def background_updater(self):
        """Bot ishlayotgan davomida har UPDATE_INTERVAL_SECONDS da kurslarni yangilaydi."""
        while True:
            try:
                await self.refresh_once()
            except Exception as e:
                logger.error(f"Fon yangilashda xato: {e}")
            await asyncio.sleep(UPDATE_INTERVAL_SECONDS)


# Bitta global instance - butun bot shundan foydalanadi
rates_store = RatesStore()
