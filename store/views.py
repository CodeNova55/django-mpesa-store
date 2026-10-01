from django.views.generic import DetailView, ListView

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