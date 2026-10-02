import json

from django.conf import settings
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem
from .mpesa import initiate_stk_push


def checkout(request):
    cart = Cart(request)
    if not len(cart):
        return redirect("cart_detail")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = Order.objects.create(
                    full_name=form.cleaned_data["full_name"],
                    phone=form.cleaned_data["phone"],
                    total=cart.total(),
                )
                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=item["product"],
                        price=item["product"].price,
                        quantity=item["quantity"],
                    )
            try:
                order.checkout_request_id = initiate_stk_push(order)
                order.save(update_fields=["checkout_request_id"])
            except Exception:
                order.status = Order.Status.FAILED
                order.save(update_fields=["status"])

            # Remember which orders belong to this browser session
            request.session.setdefault("order_ids", []).append(order.pk)
            request.session.modified = True
            cart.clear()
            return redirect("order_detail", pk=order.pk)
    else:
        form = CheckoutForm()
    return render(request, "store/checkout.html", {"form": form, "cart": cart})


def _get_own_order(request, pk):
    """Only the browser session that placed the order can view it."""
    if pk not in request.session.get("order_ids", []):
        raise Http404
    return get_object_or_404(Order, pk=pk)


def order_detail(request, pk):
    order = _get_own_order(request, pk)
    return render(
        request,
        "store/order_detail.html",
        {"order": order, "simulated": settings.MPESA_SIMULATED},
    )


@require_POST
def simulate_payment(request, pk):
    if not settings.MPESA_SIMULATED:
        raise Http404
    order = _get_own_order(request, pk)
    if order.status == Order.Status.PENDING:
        order.mark_paid(receipt=f"SIM{order.pk:06d}")
    return redirect("order_detail", pk=order.pk)


@csrf_exempt
@require_POST
def mpesa_callback(request):
    """Safaricom posts the STK push result here."""
    try:
        data = json.loads(request.body)["Body"]["stkCallback"]
        order = Order.objects.get(checkout_request_id=data["CheckoutRequestID"])
    except (ValueError, KeyError, Order.DoesNotExist):
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Rejected"})

    if data["ResultCode"] == 0:
        items = data.get("CallbackMetadata", {}).get("Item", [])
        receipt = next(
            (i.get("Value", "") for i in items if i.get("Name") == "MpesaReceiptNumber"),
            "",
        )
        order.mark_paid(receipt=str(receipt))
    elif order.status == Order.Status.PENDING:
        order.status = Order.Status.FAILED
        order.save(update_fields=["status"])
    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})