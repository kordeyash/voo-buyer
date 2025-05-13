import os
import requests
from datetime import datetime
import pytz

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

BASE_URL = "https://paper-api.alpaca.markets"
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

def get_last_close_price(symbol):
    print(f"📊 Fetching last close price for {symbol}...")
    url = f"{BASE_URL}/v2/stocks/{symbol}/bars"
    params = {
        "timeframe": "1Day",
        "limit": 2
    }
    print("🔗 URL:", url)
    print("🧾 Params:", params)

    response = requests.get(url, headers=HEADERS, params=params)
    print("🔄 Response status code:", response.status_code)

    if response.ok:
        data = response.json()
        print("📦 Response JSON:", data)

        bars = data.get("bars", [])
        if len(bars) < 2:
            print("⚠️ Not enough daily bar data returned.")
            return None
        close_price = bars[-2]["c"]
        print(f"✅ Last close price: {close_price}")
        return close_price
    else:
        print("❌ Failed to fetch last close price:", response.status_code, response.text)
        return None

def get_current_price(symbol):
    print(f"📊 Fetching current price for {symbol}...")
    url = f"{BASE_URL}/v2/stocks/{symbol}/bars"
    params = {
        "timeframe": "1Min",
        "limit": 1
    }
    print("🔗 URL:", url)
    print("🧾 Params:", params)

    response = requests.get(url, headers=HEADERS, params=params)
    print("🔄 Response status code:", response.status_code)

    if response.ok:
        data = response.json()
        print("📦 Response JSON:", data)

        bars = data.get("bars", [])
        if not bars:
            print("⚠️ No minute bar data returned.")
            return None
        current_price = bars[-1]["c"]
        print(f"✅ Current price: {current_price}")
        return current_price
    else:
        print("❌ Failed to fetch current price:", response.status_code, response.text)
        return None

def place_order(symbol="VOO", qty=1, side="buy", type="market", time_in_force="day"):
    order = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": type,
        "time_in_force": time_in_force
    }
    print(f"🛒 Placing order: {order}")
    response = requests.post(f"{BASE_URL}/v2/orders", json=order, headers=HEADERS)
    if response.ok:
        print("✅ Order placed successfully:", response.json())
    else:
        print("❌ Order failed:", response.status_code, response.text)

if __name__ == "__main__":
    symbol = "VOO"

    if is_market_open_today():
        print("✅ Market is open today.")
        last_close = get_last_close_price(symbol)
        current_price = get_current_price(symbol)

        if last_close is not None and current_price is not None:
            percent_change = ((current_price - last_close) / last_close) * 100
            print(f"📈 {symbol} price change since last close: {percent_change:.2f}%")

            if percent_change < 0:
                qty_to_buy = abs(percent_change) * 0.10  # Example logic
                print(f"🛒 Placing fractional order for {qty_to_buy:.4f} shares of {symbol}")
                place_order(symbol=symbol, qty=round(qty_to_buy, 4))
            else:
                print("📈 Price did not drop — no order placed.")
        else:
            print("❌ Could not retrieve both prices. Skipping order.")
    else:
        print("📅 Market is closed today (weekend or holiday). Exiting.")
