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


def stk_push(request,phone, amount, order_id):
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
        #"CallBackURL": "https://800c-102-203-143-208.ngrok-free.app/callback",
        "CallBackURL":request.build_absolute_uri('/callback'),
        "AccountReference": f"Order{order_id}",
        "TransactionDesc": "Payment for order"
    }
    print(request.build_absolute_uri('/callback/'))
    
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

def stk_query(checkout_request_id):
    access_token = get_access_token()
    shortcode = "174379"
    passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    password = base64.b64encode(
        (shortcode + passkey + timestamp).encode()
    ).decode()

    url = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id
    }

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    return response.json()     

def send_b2c(phone, amount):

    access_token = get_access_token()

    url = "https://sandbox.safaricom.co.ke/mpesa/b2c/v1/paymentrequest"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "InitiatorName": "testapi",
        "SecurityCredential": "bfWt3M6US/GeXPuMb1AdJ/WBKswqXwt/JuZr411cL4o9t/jjiQznsMWmspirujkVuSlRaEhH9A008JIme31WgQaszDVaH3e8bBsliTIWpEt2QnJtX86/+NsOVjLLO7CPSbcYb9BCE84XZ236IK+1kgNmt0S/6t8kHZDfGlY9iQHKWP6FkltjwrdxQ2FWow3mFdk5ZrSZ68ws/iZuylvatGdbB77piltJ7MVynDqY3j2Pv7D+R9mjpS9PVrUKyoYj3zqDV0V17MJw1YAcqelws1/F9410aNwJ3zmEUieDA2wOvKDywy/YOFRaBTMqFDABYroHTbqxT6ll4YFI7Y7g2g==",
        "CommandID": "BusinessPayment",
        "Amount": int(amount),
        "PartyA": "600000",
        "PartyB": "254708374149",
        "Remarks": "Refund",
        # "QueueTimeOutURL": "https://73da-102-203-143-208.ngrok-free.app/timeout",
        # "ResultURL": "https://73da-102-203-143-208.ngrok-free.app/result",
        "QueueTimeOutURL":"https://7ef6-105-164-47-90.ngrok-free.app/timeout",
        "ResultURL": "https://7ef6-105-164-47-90.ngrok-free.app/result",
        "Occasion": "Order Refund"
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.json()       