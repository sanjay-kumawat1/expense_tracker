from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from .models import Expense, OTPCode
import re

def generate_otp():
    return get_random_string(length=6, allowed_chars='0123456789')

def send_otp_email(email, code):
    subject = 'Your Expense Tracker OTP Code'
    message = f'''
    Hi there,

    Your OTP code for password reset is: **{code}**

    This code will expire in 10 minutes.

    If you didn't request this, please ignore this email.

    Regards,
    Expense Tracker Team
    '''
    
    send_mail(
        subject,
        message,
        'your-email@gmail.com',  
        [email],
        fail_silently=False,
    )

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'login.html')

def signup_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, 'Passwords do not match')

        elif User.objects.filter(username=email).exists():
            messages.error(request, 'Email already exists')

        else:
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=name,
                password=password
            )
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')

    return render(request, 'signup.html')

# Forgot Password Views
def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            messages.error(request, 'Please enter a valid email address')
            return render(request, 'forgot_password.html')
        
        try:
            user = User.objects.get(username=email)
            
            # Delete old OTPs
            OTPCode.objects.filter(user=user).delete()
            
            # Generate new OTP
            code = generate_otp()
            otp = OTPCode.objects.create(user=user, code=code)
            
            # Send OTP
            send_otp_email(email, code)
            
            request.session['reset_email'] = email
            messages.success(request, 'OTP sent to your email! Check inbox/spam.')
            return redirect('verify_otp')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email')
    
    return render(request, 'forgot_password.html')

def verify_otp_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')
    
    if request.method == 'POST':
        code = request.POST.get('otp')
        try:
            otp = OTPCode.objects.filter(
                user__username=email,
                is_used=False,
                created_at__gte=timezone.now() - timedelta(minutes=10)
            ).latest('created_at')
            
            if otp.code == code:
                otp.is_used = True
                otp.save()
                request.session['reset_email'] = email
                messages.success(request, 'OTP verified successfully!')
                return redirect('reset_password')
            else:
                messages.error(request, 'Invalid or expired OTP')
                
        except OTPCode.DoesNotExist:
            messages.error(request, 'Invalid or expired OTP')
    
    return render(request, 'verify_otp.html', {'email': email})

def reset_password_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'reset_password.html')
        
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return render(request, 'reset_password.html')
        
        user = User.objects.get(username=email)
        user.set_password(password)
        user.save()
        
        # Clear session
        if 'reset_email' in request.session:
            del request.session['reset_email']
        messages.success(request, 'Password reset successfully!')
        return redirect('login')
    
    return render(request, 'reset_password.html')

@login_required
def dashboard_view(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')

    if request.method == 'POST' and not request.POST.get('delete') and not request.POST.get('edit_id'):
        title = request.POST.get('title')
        amount = request.POST.get('amount')
        category = request.POST.get('category')
        description = request.POST.get('description')

        try:
            amount = float(amount)
        except:
            messages.error(request, "Invalid amount")
            return redirect('dashboard')

        Expense.objects.create(
            user=request.user,
            title=title,
            amount=amount,
            category=category,
            description=description
        )
        messages.success(request, "Expense added!")
        return redirect('dashboard')

    if request.method == 'POST' and request.POST.get('delete'):
        Expense.objects.filter(
            id=request.POST.get('delete'),
            user=request.user
        ).delete()
        messages.success(request, "Deleted!")
        return redirect('dashboard')

    if request.method == 'POST' and request.POST.get('edit_id'):
        expense = get_object_or_404(
            Expense, id=request.POST.get('edit_id'), user=request.user
        )

        expense.title = request.POST.get('title')
        expense.amount = request.POST.get('amount')
        expense.category = request.POST.get('category')
        expense.description = request.POST.get('description')
        expense.save()

        messages.success(request, "Updated!")
        return redirect('dashboard')

    month = request.GET.get('month')
    if month and month.isdigit():
        expenses = expenses.filter(date__month=int(month))

    total = sum(exp.amount for exp in expenses)
    highest = expenses.order_by('-amount').first()

    return render(request, 'dashboard.html', {
        'expenses': expenses,
        'highest': highest,
        'total': total
    })

def logout_view(request):
    logout(request)
    return redirect('login')