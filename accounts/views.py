from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from .forms import UserRegistrationForm, UserUpdateForm, ProfileUpdateForm
from .models import User, Badge, UserBadge

def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('courses:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to EduVolve, {user.username}!')
            return redirect('courses:dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('courses:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Update streak on login
            if user.is_student():
                user.update_streak()
            
            next_url = request.GET.get('next', 'courses:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


@login_required
def user_logout(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def profile(request):
    """User profile view"""
    context = {
        'user': request.user,
    }
    
    if request.user.is_student():
        # Get badges
        user_badges = UserBadge.objects.filter(user=request.user).select_related('badge')
        all_badges = Badge.objects.all()
        
        # Check for new badges
        for badge in all_badges:
            if request.user.total_points >= badge.points_required:
                UserBadge.objects.get_or_create(user=request.user, badge=badge)
        
        context['user_badges'] = user_badges
        context['all_badges'] = all_badges
    
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    """Edit user profile"""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def leaderboard(request):
    """Display student leaderboard"""
    top_students = User.objects.filter(
        role=User.Role.STUDENT
    ).order_by('-total_points')[:50]
    
    # Get current user rank
    user_rank = None
    if request.user.is_student():
        students_above = User.objects.filter(
            role=User.Role.STUDENT,
            total_points__gt=request.user.total_points
        ).count()
        user_rank = students_above + 1
    
    context = {
        'top_students': top_students,
        'user_rank': user_rank,
    }
    return render(request, 'accounts/leaderboard.html', context)