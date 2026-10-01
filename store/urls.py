from django.urls import path

from . import order_views, views

urlpatterns = [
    path("", views.ProductListView.as_view(), name="product_list"),
    path("products/<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:pk>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:pk>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:pk>/", views.cart_remove, name="cart_remove"),
    path("checkout/", order_views.checkout, name="checkout"),
    path("orders/<int:pk>/", order_views.order_detail, name="order_detail"),
    path(
        "orders/<int:pk>/simulate-payment/",
        order_views.simulate_payment,
        name="simulate_payment",
    ),
    path("mpesa/callback/", order_views.mpesa_callback, name="mpesa_callback"),
]