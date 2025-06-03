import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from binance import AsyncClient
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACDIndicator
import pandas as pd
import datetime

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

SYMBOL = "BTCUSDT"
INTERVAL = "1m"
LIMIT = 100

async def fetch_data():
    client = await AsyncClient.create(BINANCE_API_KEY, BINANCE_API_SECRET)
    klines = await client.get_klines(symbol=SYMBOL, interval=INTERVAL, limit=LIMIT)
    await client.close_connection()

    df = pd.DataFrame(klines, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["close"] = pd.to_numeric(df["close"])
    df["time"] = pd.to_datetime(df["time"], unit='ms')
    return df

def analyze(df):
    ema = EMAIndicator(df["close"], window=10).ema_indicator()
    rsi = RSIIndicator(df["close"], window=14).rsi()
    macd = MACDIndicator(df["close"]).macd_diff()

    trend = "Buy" if macd.iloc[-1] > 0 and rsi.iloc[-1] < 70 else "Sell"
    confidence = round(abs(macd.iloc[-1]) * 10, 2)
    payout = "85.0%"
    current_time = datetime.datetime.utcnow().strftime('%H:%M:%S')

    signal = (
        f"{SYMBOL}\n"
        f"Timeframe: M1\n"
        f"UTC Time: {current_time}\n"
        f"Signal: {'CALL' if trend == 'Buy' else 'PUT'}\n\n"
        f"Trend: {trend}\n"
        f"Forecast: {confidence}%\n"
        f"Payout: {payout}"
    )
    return signal

async def main_loop():
    while True:
        df = await fetch_data()
        signal = analyze(df)
        await bot.send_message(chat_id=CHAT_ID, text=signal)
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main_loop())