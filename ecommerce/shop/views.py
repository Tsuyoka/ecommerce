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
    product = Product.objects.get(pk=pk)
    average_rating = Order.get_average_rating(product)
    return render(request, 'product_detail.html', {'product': product, 'average_rating': average_rating})



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
    if request.user.is_authenticated:
        cart_items = Cart.get_cart(request.user)
        return render(request, 'cart.html', {'cart_items': cart_items})
    else:
        return redirect('login')
    

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
    return render(request, 'returns.html', {'orders': orders})  # Pass 'orders' to the template



@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        return redirect('cart')  
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            for item in cart_items:
                Order.objects.create(
                    user=request.user,
                    product=item.product,
                    address=form.cleaned_data['address'],
                    phone_number=form.cleaned_data['phone_number'],
                    pincode=form.cleaned_data['pincode']
                )
            cart_items.delete()  
            return redirect('payment')  
    else:
        form = CheckoutForm()
    
    return render(request, 'checkout.html', {'form': form, 'cart_items': cart_items})


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

def payment_success(request):
    orders = Order.objects.filter(user=request.user, is_paid=False)
    orders.update(is_paid=True)  
    return render(request, 'payment_success.html')

def payment_cancel(request):
    return render(request, 'payment_cancel.html')
