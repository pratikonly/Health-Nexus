from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile
import random

def auth_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/auth.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return redirect('auth')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        gender = request.POST.get('gender')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('auth')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('auth')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('auth')
        
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Assign random avatar based on gender
        male_avatars = ['👨', '🧔', '👨‍💼', '👨‍🔬', '👨‍⚕️', '👨‍🎓', '🧑', '👦']
        female_avatars = ['👩', '👩‍💼', '👩‍🔬', '👩‍⚕️', '👩‍🎓', '👧', '🧑‍🦰', '👱‍♀️']
        other_avatars = ['🧑', '😊', '🙂', '😎', '🤓', '🥳']
        
        if gender == 'male':
            avatar_emoji = random.choice(male_avatars)
        elif gender == 'female':
            avatar_emoji = random.choice(female_avatars)
        else:
            avatar_emoji = random.choice(other_avatars)
        
        UserProfile.objects.create(user=user, gender=gender, avatar_emoji=avatar_emoji)
        login(request, user)
        messages.success(request, f'Welcome to VitalTrack, {user.username}! Your journey to healthy living starts now.')
        return redirect('dashboard')
    
    return redirect('auth')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('landing')
