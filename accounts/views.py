from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import UserProfile
import random
import string

def auth_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/auth.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid password. Please try again.', extra_tags='invalid_password')
        except User.DoesNotExist:
            messages.error(request, 'Email not found.', extra_tags='email_not_exist')
    
    return redirect('auth')

def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        gender = request.POST.get('gender')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Account already exists with this email.')
            return redirect('auth')
        
        base_username = name.lower().replace(' ', '_')[:20]
        username = base_username
        while User.objects.filter(username=username).exists():
            suffix = ''.join(random.choices(string.digits, k=4))
            username = f"{base_username}_{suffix}"
        
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = name
        user.save()
        
        if gender == 'male':
            avatar_url = 'https://pratik-image-api.vercel.app/male/'
        elif gender == 'female':
            avatar_url = 'https://pratik-image-api.vercel.app/female'
        else:
            avatar_url = 'https://pratik-image-api.vercel.app/male/'
        
        UserProfile.objects.create(user=user, gender=gender)
        login(request, user)
        messages.success(request, f'Welcome to VitalTrack, {name}! Your journey to healthy living starts now.')
        return redirect('dashboard')
    
    return redirect('auth')

@require_POST
def check_email_view(request):
    email = request.POST.get('email', '')
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('landing')
