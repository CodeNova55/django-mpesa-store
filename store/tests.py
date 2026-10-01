import json
from decimal import Decimal

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .forms import CheckoutForm
from .models import Category, Order, Product


@override_settings(MPESA_SIMULATED=True)
class StoreTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Groceries")
        self.product = Product.objects.create(
            category=category, name="Sugar 1kg", price=Decimal("180"), stock=10
        )

    def add_to_cart(self, quantity=1):
        self.client.post(
            reverse("cart_add", args=[self.product.pk]), {"quantity": quantity}
        )

    def place_order(self, quantity=2):
        self.add_to_cart(quantity)
        self.client.post(
            reverse("checkout"), {"full_name": "Jane Doe", "phone": "0712345678"}
        )
        return Order.objects.get()

    def callback_body(self, checkout_id, code=0):
        callback = {
            "CheckoutRequestID": checkout_id,
            "ResultCode": code,
            "ResultDesc": "test",
        }
        if code == 0:
            callback["CallbackMetadata"] = {
                "Item": [{"Name": "MpesaReceiptNumber", "Value": "QWE123XYZ"}]
            }
        return json.dumps({"Body": {"stkCallback": callback}})

    # Catalog
    def test_inactive_products_are_hidden(self):
        Product.objects.create(
            category=self.product.category,
            name="Hidden item",
            price=100,
            stock=5,
            is_active=False,
        )
        response = self.client.get(reverse("product_list"))
        self.assertContains(response, "Sugar 1kg")
        self.assertNotContains(response, "Hidden item")

    # Cart
    def test_add_to_cart(self):
        self.add_to_cart(2)
        self.assertEqual(self.client.session["cart"], {str(self.product.pk): 2})

    def test_cart_quantity_is_capped_at_stock(self):
        self.add_to_cart(50)
        self.assertEqual(self.client.session["cart"][str(self.product.pk)], 10)

    def test_cart_shows_total(self):
        self.add_to_cart(3)
        response = self.client.get(reverse("cart_detail"))
        self.assertContains(response, "540.00")

    # Checkout form
    def test_phone_is_normalised(self):
        form = CheckoutForm({"full_name": "Jane Doe", "phone": "0712 345 678"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["phone"], "254712345678")

    def test_bad_phone_is_rejected(self):
        form = CheckoutForm({"full_name": "Jane Doe", "phone": "12345"})
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    # Orders and payment
    def test_checkout_creates_pending_order_and_clears_cart(self):
        order = self.place_order(quantity=2)
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.total, Decimal("360"))
        self.assertEqual(order.phone, "254712345678")
        self.assertEqual(self.client.session.get("cart"), {})

    def test_simulated_payment_marks_paid_and_reduces_stock(self):
        order = self.place_order(quantity=2)
        self.client.post(reverse("simulate_payment", args=[order.pk]))
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(self.product.stock, 8)

    def test_order_is_hidden_from_other_sessions(self):
        order = self.place_order()
        other_visitor = Client()
        response = other_visitor.get(reverse("order_detail", args=[order.pk]))
        self.assertEqual(response.status_code, 404)

    # M-Pesa callback
    def test_callback_success_marks_order_paid(self):
        order = Order.objects.create(
            full_name="Jane Doe",
            phone="254712345678",
            total=180,
            checkout_request_id="ws_CO_123",
        )
        self.client.post(
            reverse("mpesa_callback"),
            self.callback_body("ws_CO_123", code=0),
            content_type="application/json",
        )
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.mpesa_receipt, "QWE123XYZ")

    def test_callback_failure_marks_order_failed(self):
        order = Order.objects.create(
            full_name="Jane Doe",
            phone="254712345678",
            total=180,
            checkout_request_id="ws_CO_456",
        )
        self.client.post(
            reverse("mpesa_callback"),
            self.callback_body("ws_CO_456", code=1032),
            content_type="application/json",
        )
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.FAILED)

    def test_callback_with_unknown_request_is_rejected(self):
        response = self.client.post(
            reverse("mpesa_callback"),
            self.callback_body("does-not-exist"),
            content_type="application/json",
        )
        self.assertEqual(response.json()["ResultCode"], 1)