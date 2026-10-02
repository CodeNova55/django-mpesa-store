from django.core.management.base import BaseCommand

from store.models import Category, Product

SAMPLE = {
    "Groceries": [
        ("Unga wa Ngano 2kg", "Wheat flour, 2kg pack", 220, 50),
        ("Cooking Oil 1L", "Vegetable cooking oil", 330, 40),
        ("Sugar 1kg", "White sugar", 180, 60),
    ],
    "Electronics": [
        ("Phone Charger", "Fast USB-C charger", 850, 25),
        ("Earphones", "Wired earphones with mic", 600, 30),
    ],
    "Household": [
        ("Mop and Bucket", "Cleaning set", 1200, 15),
        ("Water Bottle 1L", "Reusable bottle", 450, 35),
    ],
}


class Command(BaseCommand):
    help = "Create sample categories and products"

    def handle(self, *args, **options):
        for category_name, items in SAMPLE.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for name, description, price, stock in items:
                Product.objects.get_or_create(
                    name=name,
                    defaults={
                        "category": category,
                        "description": description,
                        "price": price,
                        "stock": stock,
                    },
                )
        self.stdout.write(self.style.SUCCESS("Sample products created."))