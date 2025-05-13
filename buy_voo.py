import os
import requests
from datetime import datetime
import pytz
import yfinance as yf
from bs4 import BeautifulSoup  # For scraping

# === ENV VARS ===
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

BASE_URL = "https://paper-api.alpaca.markets"  # Use live URL for real trades
HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
}

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

def get_fear_and_greed_index():
    """
    Scrapes the current Fear & Greed Index from CNN.
    """
    try:
        url = "https://money.cnn.com/data/fear-and-greed/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to fetch page: Status {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        score_span = soup.find("span", class_="market-fng-gauge__dial-number-value")
        if score_span:
            score = score_span.text.strip()
            print(f"🧠 CNN Fear & Greed Index: {score}")
            return score
        else:
            print("⚠️ Could not locate the Fear & Greed value.")
            return None
    except Exception as e:
        print(f"❌ Exception while scraping Fear & Greed Index: {e}")
        return None

if __name__ == "__main__":
    if not is_market_open_today():
        print("📅 Market is closed today. Exiting.")
        exit()

    # Fetch and print the Fear & Greed Index (not used in logic yet)
    get_fear_and_greed_index()

    yesterday_close, current_price, percent_change = get_voo_price_data()
    if yesterday_close is None:
        exit()

    print(f"📈 Yesterday's Close: ${yesterday_close:.2f}")
    print(f"💰 Current Price: ${current_price:.2f}")
    print(f"📉 Percent Change: {percent_change:.2f}%")

    if percent_change < 0:
        amount_to_buy_percent = abs(percent_change) * 10
        qty_to_buy = amount_to_buy_percent / 100
        print(f"🛒 Placing order for {qty_to_buy:.4f} shares of VOO...")
        place_order(qty=round(qty_to_buy, 4))
    else:
        print("🚫 No drop in price. No action taken.")
