# config.py
# -*- coding: utf-8 -*-

# BotFather'dan olingan tokenni shu yerga qo'ying
BOT_TOKEN = "SIZNING_BOT_TOKEN_INGIZ"

# Admin(lar) telegram ID lari (Stars kursini o'zgartira oladiganlar)
# O'zingizning Telegram ID'ingizni bilish uchun @userinfobot ga yozing
ADMIN_IDS = [123456789]

# Boshlang'ich kurslar (1 birlik = necha so'm)
# Bot ishga tushganda shu qiymatlar bilan boshlaydi,
# keyin fon rejimida (background) avtomatik yangilanadi.
DEFAULT_RATES = {
    "USD": 11974.0,
    "RUB": 154.82,
    "TON": 21314.0,
    "STARS": 240.0,   # Rasmiy API bo'lmagani uchun qo'lda /setstars bilan yangilanadi
    "UZS": 1.0,       # baza valyuta - o'zgarmaydi
}

# Kurslarni necha soniyada bir yangilash (default: 60 soniya = 1 daqiqa)
UPDATE_INTERVAL_SECONDS = 60

# Kurslar saqlanadigan fayl (bot qayta ishga tushsa ham eslab qolishi uchun)
RATES_STORAGE_FILE = "rates_state.json"

# Tashqi API manzillari
CBU_API_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
COINGECKO_TON_URL = "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd"
