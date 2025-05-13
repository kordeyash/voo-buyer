import os
import requests
from datetime import datetime, timedelta
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
    response = requests.get(
        f"{BASE_URL}/v2/stocks/{symbol}/bars",
        headers=HEADERS,
        params={
            "timeframe": "1Day",
            "limit": 2  # We want the last full close
        }
    )
    if response.ok:
        bars = response.json().get("bars", [])
        if len(bars) < 2:
            print("❌ Not enough daily bar data.")
            return None
        return bars[-2]["c"]  # Close of previous full trading day
    else:
        print("❌ Failed to fetch last close price:", response.status_code, response.text)
        return None

def get_current_price(symbol):
    response = requests.get(
        f"{BASE_URL}/v2/stocks/{symbol}/bars",
        headers=HEADERS,
        params={
            "timeframe": "1Min",
            "limit": 1
        }
    )
    if response.ok:
        bars = response.json().get("bars", [])
        if not bars:
            print("❌ No current minute bar data.")
            return None
        return bars[-1]["c"]  # Latest close (current price)
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
    response = requests.post(f"{BASE_URL}/v2/orders", json=order, headers=HEADERS)
    if response.ok:
        print("✅ Order placed successfully:", response.json())
    else:
        print("❌ Order failed:", response.status_code, response.text)

if __name__ == "__main__":
    symbol = "VOO"

    if is_market_open_today():
        last_close = get_last_close_price(symbol)
        current_price = get_current_price(symbol)

        if last_close is not None and current_price is not None:
            percent_change = ((current_price - last_close) / last_close) * 100
            print(f"📉 {symbol} price change since last close: {percent_change:.2f}%")

            if percent_change < 0:
                qty_to_buy = abs(percent_change) * 0.10  # Buy 10% fractional of 1 share per % drop
                print(f"🛒 Placing fractional order for {qty_to_buy:.4f} shares of {symbol}")
                place_order(symbol=symbol, qty=round(qty_to_buy, 4))
            else:
                print("📈 Price did not drop — no order placed.")
        else:
            print("❌ Could not retrieve prices. Exiting.")
    else:
        print("📅 Market is closed today (weekend or holiday). Exiting.")
