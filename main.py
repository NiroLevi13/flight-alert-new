
import os
import time
import requests
from twilio.rest import Client
from datetime import datetime

API_URL = "https://skyscanner89.p.rapidapi.com/flights/roundtrip/list"
HEADERS = {
    "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
    "X-RapidAPI-Host": "skyscanner89.p.rapidapi.com"
}
PARAMS = {
    "origin": "TLV",
    "originId": "95673635",
    "destination": "ATH",
    "destinationId": "95673624",
    "inDate": "2025-06-18",
    "outDate": "2025-06-23",
    "adults": "1",
    "cabinClass": "economy",
    "currency": "USD",
    "market": "US",
    "locale": "en-US"
}
CHECK_INTERVAL = 1800  # 30 minutes

def get_cheapest_direct_flight():
    try:
        print("📡 Checking for direct flights under $400...")
        response = requests.get(API_URL, headers=HEADERS, params=PARAMS)
        response.raise_for_status()
        data = response.json()

        itineraries = data.get("data", {}).get("itineraries", {})
        buckets = itineraries.get("buckets", [])
        for bucket in buckets:
            for item in bucket.get("items", []):
                if item["legs"][0]["stopCount"] == 0 and item["price"]["raw"] <= 400:
                    return {
                        "airline": item["legs"][0]["carriers"]["marketing"][0]["name"],
                        "departure": item["legs"][0]["departure"],
                        "arrival": item["legs"][0]["arrival"],
                        "return_departure": item["legs"][1]["departure"],
                        "return_arrival": item["legs"][1]["arrival"],
                        "price_usd": item["price"]["raw"],
                        "price_ils": round(item["price"]["raw"] * 3.7),
                        "link": item["deeplinkUrl"]
                    }
    except Exception as e:
        print("❌ Error fetching flight data:", e)
    return None

def send_alert(flight):
    client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH"))
    message = (
        f"✈️ נמצאה טיסה ישירה הלוך־חזור
"
        f"חברת תעופה: {flight['airline']}
"
        f"המראה: {datetime.fromisoformat(flight['departure']).strftime('%H:%M')} ← נחיתה: {datetime.fromisoformat(flight['arrival']).strftime('%H:%M')}
"
        f"חזור: {datetime.fromisoformat(flight['return_departure']).strftime('%H:%M')} ← נחיתה: {datetime.fromisoformat(flight['return_arrival']).strftime('%H:%M')}
"
        f"מחיר: ${flight['price_usd']} / ₪{flight['price_ils']}
"
        f"🔗 קישור להזמנה: {flight['link']}"
    )
    client.messages.create(
        body=message,
        from_=os.getenv("TWILIO_PHONE"),
        to=os.getenv("MY_PHONE")
    )
    print("📤 נשלחה הודעה בווטסאפ.")

if __name__ == "__main__":
    print("🚀 מתחיל לעקוב אחרי טיסות...")
    while True:
        flight = get_cheapest_direct_flight()
        if flight:
            send_alert(flight)
        else:
            print(f"🔍 לא נמצאו טיסות ישירות מתחת ל־$400. ({datetime.now().strftime('%H:%M:%S')})")
        time.sleep(CHECK_INTERVAL)
