import requests
import time
import os
from twilio.rest import Client
from datetime import datetime

RAPID_API_KEY = os.getenv("RAPID_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
MY_PHONE = os.getenv("MY_PHONE")

def get_cheapest_flight():
    url = "https://skyscanner89.p.rapidapi.com/flights/roundtrip/list"
    querystring = {
        "origin": "TLV",
        "originId": "95673635",
        "destination": "ATH",
        "destinationId": "95673624",
        "inDate": "2025-06-18",
        "outDate": "2025-06-23",
        "cabinClass": "economy",
        "adults": "1",
        "currency": "USD",
        "market": "US",
        "locale": "en-US"
    }
    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "skyscanner89.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()

    try:
        buckets = data["data"]["itineraries"]["buckets"]
        for bucket in buckets:
            for item in bucket["items"]:
                legs = item.get("legs", [])
                if len(legs) >= 2 and all(leg["stopCount"] == 0 for leg in legs):
                    price_usd = item["price"]["raw"]
                    if price_usd <= 400:
                        price_ils = round(price_usd * 3.7)
                        return {
                            "airline": legs[0]["carriers"]["marketing"][0]["name"],
                            "depart": legs[0]["departure"],
                            "return": legs[1]["departure"],
                            "price_usd": price_usd,
                            "price_ils": price_ils
                        }
    except Exception as e:
        print("Error parsing response:", e)
    return None

def send_whatsapp(flight):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    depart_time = datetime.fromisoformat(flight["depart"]).strftime("%H:%M")
    return_time = datetime.fromisoformat(flight["return"]).strftime("%H:%M")
    message = f"""טיסה ישירה הלוך חזור נמצאה!
חברת תעופה: {flight["airline"]}
המראה: {depart_time}
חזרה: {return_time}
מחיר: {flight["price_usd"]}$ (כ-{flight["price_ils"]} ש"ח)"""
    print("שולח לווצאפ:")
    print(message)
    client.messages.create(
        body=message,
        from_=TWILIO_PHONE,
        to=MY_PHONE
    )

if __name__ == "__main__":
    while True:
        print("בודק טיסות...")
        flight = get_cheapest_flight()
        if flight:
            send_whatsapp(flight)
        else:
            print("אין טיסות מתאימות עכשיו.")
        time.sleep(1800)
