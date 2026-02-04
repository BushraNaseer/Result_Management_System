# takes a request => and gives response (a request handler)
# the url in urls.py file in this app is linked to this views.py fuctions
# then you have to import the urls to the urls.py file in main project 

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile  # if you want to save extra fields

def register(request):
    if request.method == "POST":
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        department = request.POST.get('department')
        date_of_joining = request.POST.get('date_of_joining')
        phone = request.POST.get('phone')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Save extra info in Profile (optional)
        Profile.objects.create(
            user=user,
            department=department,
            date_of_joining=date_of_joining,
            phone=phone
        )

        messages.success(request, "Account created! Please login.")
        return redirect('login')

    return render(request, 'register.html')


def login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password")
            return redirect('login')

    return render(request, 'login.html')


@login_required
def dashboard(request):
    return render(request, 'dashboard.html')


def logout_view(request):
    logout(request)
    return redirect('login')