import os
import requests
from datetime import datetime
import pytz
import yfinance as yf
from bs4 import BeautifulSoup

# === ENV VARS ===
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

BASE_URL = "https://paper-api.alpaca.markets"  # Use live URL for real trades
HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
}

# === CHECK IF MARKET IS OPEN ===
def is_market_open_today():
    nyc = pytz.timezone("America/New_York")
    today = datetime.now(nyc).date().isoformat()

    response = requests.get(f"{BASE_URL}/v2/calendar?start={today}&end={today}", headers=HEADERS)
    if response.ok:
        calendar = response.json()
        return len(calendar) > 0
    else:
        print("❌ Failed to fetch market calendar:", response.status_code, response.text)
        return False

# === GET VOO PRICE DATA ===
def get_voo_price_data():
    voo = yf.Ticker("VOO")
    data = voo.history(period="2d")

    if len(data) < 2:
        print("❌ Not enough data to compare price change.")
        return None, None, None

    yesterday_close = data['Close'][-2]
    current_price = data['Close'][-1]
    percent_change = ((current_price - yesterday_close) / yesterday_close) * 100

    return yesterday_close, current_price, percent_change

# === PLACE ORDER ===
def place_order(symbol="VOO", qty=1, side="buy", type="market", time_in_force="day"):
    order = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": type,
        "time_in_force": time_in_force
    }
    response = requests.post(f"{BASE_URL}/v2/orders", json=order, headers=HEADERS)
    if response.ok:
        print("✅ Order placed successfully:", response.json())
    else:
        print("❌ Order failed:", response.status_code, response.text)

# === GET FEAR & GREED INDEX (from feargreedmeter.com) ===
def get_fear_greed_index():
    url = "https://feargreedmeter.com/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print("❌ HTTP request failed:", e)
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    try:
        value_elem = soup.select_one("div.text-center.text-4xl.font-semibold.mb-1.text-white")
        if not value_elem:
            raise ValueError("❌ Could not find index value element.")
        value = value_elem.text.strip()
        print(f"📊 Fear & Greed Index: {value}")
        return float(value)
    except Exception as e:
        print("❌ Parsing error:", e)
        return None

# === MAIN SCRIPT ===
if __name__ == "__main__":
    if not is_market_open_today():
        print("📅 Market is closed today. Exiting.")
        exit()

    fear_greed_index = get_fear_greed_index()
    if fear_greed_index is None or fear_greed_index == 0:
        print("⚠️ Invalid Fear & Greed index value. Exiting.")
        exit()

    yesterday_close, current_price, percent_change = get_voo_price_data()
    if yesterday_close is None:
        exit()

    print(f"📈 Yesterday's Close: ${yesterday_close:.2f}")
    print(f"💰 Current Price: ${current_price:.2f}")
    print(f"📉 Percent Change: {percent_change:.2f}%")

    if percent_change < 0:
        multiplier = 1 / (fear_greed_index / 100)
        amount_to_buy_percent = abs(percent_change) * multiplier
        qty_to_buy = amount_to_buy_percent / 100
        print(f"🛒 Placing order for {qty_to_buy:.4f} shares of VOO based on fear/greed multiplier {multiplier:.2f}...")
        place_order(qty=round(qty_to_buy, 4))
    else:
        print("🚫 No drop in price. No action taken.")
