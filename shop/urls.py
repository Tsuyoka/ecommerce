from django.urls import path
from .views import register,payment, payment_success,payment_cancel, CustomLoginView, mark_return,logout_view,home, product_detail, cart_view, checkout, order_list, returns,add_to_cart


urlpatterns = [
    path('register/', register, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('', home, name='home'),
    path('product/<int:pk>/', product_detail, name='product_detail'),
    path('cart/', cart_view, name='cart'),
    path('checkout/', checkout, name='checkout'),
    path('orders/', order_list, name='order_list'),
    path('product/<int:pk>/add_to_cart/', add_to_cart, name='add_to_cart'),
    path('returns/', returns, name='returns'),
    path('order/<int:order_id>/return/', mark_return, name='mark_return'),
    path('checkout/', checkout, name='checkout'),
    path('payment/', payment, name='payment'),
    path('payment-success/', payment_success, name='payment_success'),
    path('payment-cancel/', payment_cancel, name='payment_cancel'),
]


