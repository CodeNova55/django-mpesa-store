from decimal import Decimal

from .models import Product

CART_SESSION_ID = "cart"


class Cart:
    """A shopping cart stored in the user's session: {product_id: quantity}."""

    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.setdefault(CART_SESSION_ID, {})

    def add(self, product, quantity=1, override=False):
        key = str(product.id)
        new_quantity = quantity if override else self.cart.get(key, 0) + quantity
        new_quantity = min(new_quantity, product.stock)  # never exceed stock
        if new_quantity <= 0:
            self.remove(product)
            return
        self.cart[key] = new_quantity
        self.save()

    def remove(self, product):
        self.cart.pop(str(product.id), None)
        self.save()

    def clear(self):
        self.cart.clear()
        self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        products = Product.objects.filter(id__in=self.cart.keys(), is_active=True)
        for product in products:
            quantity = self.cart[str(product.id)]
            yield {
                "product": product,
                "quantity": quantity,
                "subtotal": product.price * quantity,
            }

    def __len__(self):
        return sum(self.cart.values())

    def total(self):
        return sum((item["subtotal"] for item in self), Decimal("0"))