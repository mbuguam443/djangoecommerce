import requests
import base64
from datetime import datetime

CONSUMER_KEY = "9Fhevbx7JPg35tGmjhkaYNaZAuU9uP6S"
CONSUMER_SECRET = "k5MCkJz8DEo7WZHT"
SHORTCODE = "174379"  # sandbox
PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"

def get_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(CONSUMER_KEY, CONSUMER_SECRET))
    return response.json()['access_token']


def stk_push(phone, amount, order_id):
    access_token = get_access_token()

    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode((SHORTCODE + PASSKEY + timestamp).encode()).decode()

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": "https://djangoecommerce-94z3.onrender.com/callback",
        #"CallBackURL":"https://313c-102-210-247-38.ngrok-free.app/callback",
        "AccountReference": f"Order{order_id}",
        "TransactionDesc": "Payment for order"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        try:
            return response.json()
        except ValueError:
            print("MPESA did not return JSON:", response.text)
            return {"ResponseCode": "999", "ResponseDescription": "Invalid response from MPESA"}
    except requests.RequestException as e:
        print("MPESA request failed:", str(e))
        return {"ResponseCode": "999", "ResponseDescription": "MPESA request failed"}