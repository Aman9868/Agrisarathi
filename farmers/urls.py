from django.urls import path
from .views import *

urlpatterns = [
    path('FarmerLogin',FarmerLogin.as_view(), name='FarmerLogin'),
    path('FarmerLogout',FarmerLogout.as_view(), name='FarmerLogout'),
    # Add more URL patterns here
]