# Duka Store (Django + M-Pesa)

A small online store built with Django. Shoppers browse products, fill a cart, and pay with an M-Pesa STK push.

## Features
- Product catalog with categories and a category filter
- Session-based cart (quantities are capped at available stock)
- Checkout with Kenyan phone number validation
- M-Pesa STK push payment (Daraja) with a **simulated mode** for local development
- Order status page, and a callback endpoint for Safaricom's payment result
- Stock is reduced only after payment succeeds
- Django admin for products and orders
- Automated tests

## Tech Stack
- Python 3
- Django
- SQLite (default database)
- `requests` for the Daraja API

## Getting Started

```bash
git clone https://github.com/CodeNova55/django-mpesa-store.git
cd django-mpesa-store
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_products
python manage.py createsuperuser
python manage.py runserver
```

Then open http://127.0.0.1:8000

## M-Pesa Payments

By default the app runs in **simulated mode**: checkout creates a pending order, and a "Simulate M-Pesa payment" button on the order page marks it paid. No Safaricom account is needed.

To use the real Daraja sandbox, set these environment variables (see `.env.example`):

| Variable | Purpose |
|---|---|
| `MPESA_SIMULATED` | set to `false` to call Safaricom |
| `MPESA_CONSUMER_KEY` / `MPESA_CONSUMER_SECRET` | from the Daraja developer portal |
| `MPESA_SHORTCODE` / `MPESA_PASSKEY` | sandbox shortcode and passkey |
| `MPESA_CALLBACK_URL` | public HTTPS URL ending in `/mpesa/callback/` |

Note: the real mode follows the Daraja STK push format but has not yet been tested end to end against Safaricom. The callback endpoint does not yet verify the sender.

## Running Tests

```bash
python manage.py test
```

## Project Structure

```
config/                 project settings and root URLs
store/models.py         Category, Product, Order, OrderItem
store/cart.py           session-based cart
store/mpesa.py          STK push service (real and simulated)
store/views.py          catalog and cart views
store/order_views.py    checkout, order status, and M-Pesa callback
store/tests.py          automated tests
```

## Git Workflow
- One feature branch per piece of work
- Feature branch -> PR into `develop`
- `develop` -> PR into `main` (after approval)
- No direct pushes to `develop` or `main`

## Roadmap
- Verify the M-Pesa callback sender
- Product images
- Customer accounts and order history
- Deployment