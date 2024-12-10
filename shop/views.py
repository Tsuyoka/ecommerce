from django.shortcuts import render, redirect,get_object_or_404
from .forms import RegistrationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from .models import Product,Cart,Order
import paypalrestsdk
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .forms import CheckoutForm
from django.db.models import Avg
import random

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        return '/'


def logout_view(request):
    logout(request)
    return redirect('login')




def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart_items = Cart.objects.filter(user=request.user) if request.user.is_authenticated else []


    same_category_products = Product.objects.filter(category=product.category).exclude(pk=product.pk)
    product_based_recommendations = random.sample(list(same_category_products),
                                                   min(2, same_category_products.count()))


    cart_recommendations = []
    if cart_items:
        random_cart_item = random.choice(cart_items)
        related_products = Product.objects.filter(category=random_cart_item.product.category).exclude(
            pk=random_cart_item.product.pk)
        cart_recommendations = random.sample(list(related_products),
                                             min(1, related_products.count()))

    # Combine recommendations
    recommendations = product_based_recommendations + cart_recommendations

    average_rating = Order.get_average_rating(product)

    return render(request, 'product_detail.html', {
        'product': product,
        'average_rating': average_rating,
        'recommendations': recommendations
    })



@login_required
def add_to_cart(request, pk):
    product = Product.objects.get(pk=pk)

    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)

    if created:

        cart_item.quantity = 1
        cart_item.save()
    else:

        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart')

def cart_view(request):
    payment_status = request.GET.get('payment_status')  # Get the payment status from the query parameter
    cart_items = Cart.get_cart(request.user) if request.user.is_authenticated else None

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'payment_status': payment_status
    })


@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.product.price * item.quantity for item in cart_items)  # Calculate total price

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            return redirect('payment')
    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'form': form
    })
@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)

    if request.method == "POST":
        order_id = request.POST.get("order_id")
        rating = request.POST.get("rating")

        # Ensure the order belongs to the user
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if rating and rating.isdigit() and 1 <= int(rating) <= 5:
            order.rating = int(rating)
            order.save()

        return redirect("order_list")

    return render(request, "orders.html", {"orders": orders})

@login_required
def mark_return(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, user=request.user)
        order.is_returned = True
        order.save()
    return redirect('order_list')


def returns(request):
    print(f"User authenticated: {request.user.is_authenticated}")
    orders = Order.objects.filter(user=request.user, is_returned=True)
    return render(request, 'returns.html', {'orders': orders})



@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        return redirect('cart')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            return redirect('payment')
    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {'form': form, 'cart_items': cart_items})


def payment_success(request):
    cart_items = Cart.objects.filter(user=request.user)

    for item in cart_items:
        Order.objects.create(
            user=request.user,
            product=item.product,
            address=request.POST.get('address', ''),
            phone_number=request.POST.get('phone_number', ''),
            pincode=request.POST.get('pincode', ''),
            is_paid=True
        )

    cart_items.delete()  # Clear the cart after successful payment

    return redirect('/cart?payment_status=success')


def payment_cancel(request):
    return redirect('/cart?payment_status=failed')




@login_required
def payment(request):
    orders = Order.objects.filter(user=request.user, is_paid=False)
    total_amount = sum(order.product.price for order in orders)

    if request.method == 'POST':
        paypalrestsdk.configure({
            "mode": "sandbox",
            "client_id": "AawuVFGg8dtOVu2tl5wjDpfCLhxzhSo2gb6SomDohG08yT807Q3i4Xpilst4tBfk7vtKo7QUHBoux35e",
            "client_secret": "EM29PJZKmbnTMbqGJUiScDZ569qb3oRt9_aWT_FiG31Q5lcNIyfofoAwljX1esIkbtDmwZogxZfbYkx4"
        })

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": "http://127.0.0.1:8000/payment-success/",
                "cancel_url": "http://127.0.0.1:8000/payment-cancel/"
            },
            "transactions": [{
                "item_list": {
                    "items": [
                        {
                            "name": order.product.name,
                            "price": str(order.product.price),
                            "currency": "USD",
                            "quantity": 1
                        } for order in orders
                    ]
                },
                "amount": {
                    "total": str(total_amount),
                    "currency": "USD"
                },
                "description": "Payment for your order"
            }]
        })

        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    return redirect(link.href)
        else:
            return render(request, 'payment.html', {'error': payment.error})

    return render(request, 'payment.html', {'total_amount': total_amount})
