"""expense_tracker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from my_app import urls as my_app_urls
    2. Add a URL to urlpatterns:  path('my_app/', include(my_app_urls))
"""
from django.contrib import admin
from django.urls import path
from tracker.views import (
    login_view, signup_view, dashboard_view, logout_view,
    forgot_password_view, verify_otp_view, reset_password_view
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Main Pages
    path('', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    
    # FORGOT PASSWORD PAGES
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('reset-password/', reset_password_view, name='reset_password'),
]