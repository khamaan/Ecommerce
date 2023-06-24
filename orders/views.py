from django.shortcuts import render, redirect
from django.http import JsonResponse
from carts.models import Cart, CartItem, Product
from .models import Order, OrderProduct, Payment
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from carts.views import _cart_id
import datetime
import json
from django.template.loader import render_to_string
from django.conf import settings


# Create your views here.
@login_required(login_url="login")
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except:
        pass

    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total,
    }

    return render(request, "store/checkout.html", context)


@login_required(login_url="login")
def place_order(request, total=0, quantity=0):
    current_user = request.user
    # if the cart count is less than or equal to 0,then redirect back to shop page
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect("store")
    tax = 0
    grand_total = 0
    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        quantity += cart_item.quantity
    tax = (8 * total) / 100
    grand_total = total + tax

    if request.method == "POST":
        # store all the billing information inside order table
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        phone = request.POST["phone"]
        email = request.POST["email"]
        address_line_1 = request.POST["address_line_1"]
        address_line_2 = request.POST["address_line_2"]
        country = request.POST["country"]
        state = request.POST["state"]
        city = request.POST["city"]
        order_note = request.POST["order_note"]
        order_total = grand_total
        tax = tax
        ip = request.META.get("REMOTE_ADDR")

        current_data = Order(
            user=current_user,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            country=country,
            state=state,
            city=city,
            order_note=order_note,
            order_total=order_total,
            tax=tax,
            ip=ip,
        )
        current_data.save()
        # generate order number
        yr = int(datetime.date.today().strftime("%Y"))
        dt = int(datetime.date.today().strftime("%d"))
        mt = int(datetime.date.today().strftime("%m"))
        d = datetime.date(yr, mt, dt)
        current_date = d.strftime("%Y%m%d")
        order_number = current_date + str(current_data.id)
        current_data.order_number = order_number
        current_data.current_date = current_date
        current_data.save()
        order = Order.objects.get(
            user=current_user, is_ordered=False, order_number=order_number
        )
        context = {
            "order": order,
            "cart_items": cart_items,
            "total": total,
            "tax": tax,
            "grand_total": grand_total,
        }
        return render(request, "orders/payments.html", context)
    else:
        return redirect("checkout")
        # store payment information


def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(
        user=request.user, is_ordered=False, order_number=body["orderID"]
    )
    payment = Payment(
        user=request.user,
        payment_id=body["transID"],
        payment_method=body["payment_method"],
        amount_paid=order.order_total,
        status=body["status"],
    )
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        cart_items = CartItem.objects.filter(user=request.user)
        product_variation = item.variation.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variation.set(product_variation)
        orderproduct.save()

        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

        CartItem.objects.filter(user=request.user).delete()
        mail_subject = "Thank you for your order!"
        message = render_to_string(
            "orders/order_received_email.html",
            {
                "user": request.user,
                "order": order,
            },
        )
        to_mail = request.user.email
        send_mail(
            mail_subject,
            message,
            recipient_list=[to_mail],
            from_email=settings.EMAIL_HOST_USER,
        )
        data = {
            "order_number": order.order_number,
            "transID": payment.payment_id,
        }
        return JsonResponse(data)
    return render(request, "orders/payments.html")


def order_complete(request):
    order_number = request.GET.get("order_number")
    transID = request.GET.get("payment_id")
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity
            payment = Payment.objects.get(payment_id=transID)
        context = {
            "order": order,
            "ordered_products": ordered_products,
            "order_number": order.order_number,
            "transID": payment.payment_id,
            "payment": payment,
            "subtotal": subtotal,
        }
        return render(request, "orders/order_complete.html", context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect("home")
