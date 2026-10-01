import base64
from datetime import datetime

import requests
from django.conf import settings


def _timestamp():
    return datetime.now().strftime("%Y%m%d%H%M%S")


def _access_token():
    response = requests.get(
        f"{settings.MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
        auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def initiate_stk_push(order):
    """Start an STK push and return the CheckoutRequestID.

    In simulated mode (the default) no request is sent to Safaricom.
    """
    timestamp = _timestamp()
    if settings.MPESA_SIMULATED:
        return f"SIM-{order.pk}-{timestamp}"

    password = base64.b64encode(
        f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()
    ).decode()
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(order.total),
        "PartyA": order.phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": order.phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": f"ORDER{order.pk}",
        "TransactionDesc": f"Payment for order {order.pk}",
    }
    response = requests.post(
        f"{settings.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers={"Authorization": f"Bearer {_access_token()}"},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["CheckoutRequestID"]