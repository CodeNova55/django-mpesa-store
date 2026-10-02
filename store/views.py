from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from .cart import Cart
from .models import Category, Product


class ProductListView(ListView):
    model = Product
    context_object_name = "products"

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related("category")
        category_id = self.request.GET.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["selected_category"] = self.request.GET.get("category", "")
        return context


class ProductDetailView(DetailView):
    model = Product
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.filter(is_active=True)


def _read_quantity(request, default=1):
    try:
        return int(request.POST.get("quantity", default))
    except ValueError:
        return default


@require_POST
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    Cart(request).add(product, quantity=max(_read_quantity(request), 1))
    return redirect("cart_detail")


@require_POST
def cart_update(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    Cart(request).add(product, quantity=_read_quantity(request, 0), override=True)
    return redirect("cart_detail")


@require_POST
def cart_remove(request, pk):
    product = get_object_or_404(Product, pk=pk)
    Cart(request).remove(product)
    return redirect("cart_detail")


def cart_detail(request):
    return render(request, "store/cart_detail.html")