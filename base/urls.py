from django.urls import path
from .views import *

urlpatterns = [
    path('', home),
    path('shop/homepage', shophome),
    path('shop/products', products),
    path('users/register', user_register),
    path('users/login', user_login),
    path('users/data/<str:tname>', user_data),
    path('users/update-cart', user_update_cart),
    path('users/remove-cart-item', user_remove_cart_item),
    path('users/change_data', user_change_data),
    path('send-img', send_img),
    path('admin/login', admin_login),
    path('admin/upload-product', admin_upload_product),
    path('payment', razor),
    path('payment/verify', razor_verify),
]
