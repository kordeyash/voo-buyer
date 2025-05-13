import os
import requests

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

BASE_URL = "https://paper-api.alpaca.markets"
HEADERS = {
    "APCA-API-KEY-ID": ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
}

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
    place_order()
