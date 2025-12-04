from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator

class User(AbstractUser):
    """Extended User model with role-based access"""
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        INSTRUCTOR = 'INSTRUCTOR', 'Instructor'
        STUDENT = 'STUDENT', 'Student'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
    )
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Gamification fields for students
    total_points = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    current_streak = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    longest_streak = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    last_activity_date = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    def is_instructor(self):
        return self.role == self.Role.INSTRUCTOR
    
    def is_student(self):
        return self.role == self.Role.STUDENT
    
    def update_streak(self):
        """Update learning streak based on activity"""
        from datetime import date, timedelta
        
        today = date.today()
        
        if self.last_activity_date:
            days_diff = (today - self.last_activity_date).days
            
            if days_diff == 0:
                # Already logged in today
                return
            elif days_diff == 1:
                # Consecutive day
                self.current_streak += 1
                if self.current_streak > self.longest_streak:
                    self.longest_streak = self.current_streak
            else:
                # Streak broken
                self.current_streak = 1
        else:
            # First activity
            self.current_streak = 1
            self.longest_streak = 1
        
        self.last_activity_date = today
        self.save()
    
    def add_points(self, points):
        """Add points to user's total"""
        self.total_points += points
        self.save()


class Badge(models.Model):
    """Achievement badges for gamification"""
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='trophy')  # Bootstrap icon name
    points_required = models.IntegerField(default=0)
    color = models.CharField(max_length=20, default='primary')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['points_required']
    
    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """Track badges earned by users"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"
