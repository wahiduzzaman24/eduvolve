from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
import re

class Course(models.Model):
    """Main Course model"""
    
    class Level(models.TextChoices):
        BEGINNER = 'BEGINNER', 'Beginner'
        INTERMEDIATE = 'INTERMEDIATE', 'Intermediate'
        ADVANCED = 'ADVANCED', 'Advanced'
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='courses_taught',
        limit_choices_to={'role': 'INSTRUCTOR'}
    )
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.BEGINNER)
    duration_weeks = models.IntegerField(default=4, validators=[MinValueValidator(1)])
    
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_total_lessons(self):
        return self.lessons.count()
    
    def get_enrolled_count(self):
        return self.enrollments.filter(is_active=True).count()
    
    def get_completion_rate(self):
        """Calculate average completion rate"""
        enrollments = self.enrollments.filter(is_active=True)
        if not enrollments.exists():
            return 0
        
        total_progress = sum(e.progress for e in enrollments)
        return round(total_progress / enrollments.count(), 2)


class Lesson(models.Model):
    """Course lessons with video content"""
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.IntegerField(default=1)
    
    # Video content (YouTube embed)
    video_url = models.URLField(help_text="YouTube video URL")
    duration_minutes = models.IntegerField(default=10, validators=[MinValueValidator(1)])
    
    # Additional content
    content = models.TextField(blank=True, help_text="Additional lesson text content")
    attachments = models.FileField(upload_to='lesson_attachments/', blank=True, null=True)
    
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def get_youtube_embed_url(self):
        """
        Convert YouTube URL to embed format
        Handles various YouTube URL formats:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID (already embed format)
        - https://www.youtube.com/watch?v=VIDEO_ID&t=123s (with timestamp)
        """
        video_url = self.video_url.strip()
        
        # If already in embed format, return as is
        if 'youtube.com/embed/' in video_url:
            return video_url
        
        # Extract video ID using regex
        video_id = None
        
        # Pattern 1: https://www.youtube.com/watch?v=VIDEO_ID
        pattern1 = r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})'
        match1 = re.search(pattern1, video_url)
        if match1:
            video_id = match1.group(1)
        
        # Pattern 2: https://youtu.be/VIDEO_ID
        pattern2 = r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})'
        match2 = re.search(pattern2, video_url)
        if match2:
            video_id = match2.group(1)
        
        # Pattern 3: Just the video ID
        pattern3 = r'^([a-zA-Z0-9_-]{11})$'
        match3 = re.search(pattern3, video_url)
        if match3:
            video_id = match3.group(1)
        
        # If video ID found, return embed URL
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"
        
        # If no pattern matched, return original URL
        return video_url


class Quiz(models.Model):
    """Quiz for lessons"""
    
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    passing_score = models.IntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    time_limit_minutes = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        help_text="Time limit in minutes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Quiz: {self.title}"
    
    def get_total_questions(self):
        return self.questions.count()
    
    def get_total_points(self):
        return sum(q.points for q in self.questions.all())


class Question(models.Model):
    """Quiz questions"""
    
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = 'MC', 'Multiple Choice'
        TRUE_FALSE = 'TF', 'True/False'
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=2,
        choices=QuestionType.choices,
        default=QuestionType.MULTIPLE_CHOICE
    )
    points = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    order = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['quiz', 'order']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


class Answer(models.Model):
    """Answer options for questions"""
    
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['question', 'order']
    
    def __str__(self):
        return f"{self.answer_text} ({'✓' if self.is_correct else '✗'})"


class Assignment(models.Model):
    """Course assignments"""
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    max_points = models.IntegerField(default=100, validators=[MinValueValidator(1)])
    
    attachment = models.FileField(upload_to='assignment_files/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date']
    
    def __str__(self):
        return f"{self.lesson.course.title} - {self.title}"


class Enrollment(models.Model):
    """Student course enrollments"""
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': 'STUDENT'}
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    progress = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"
    
    def update_progress(self):
        """Calculate and update course progress"""
        total_lessons = self.course.lessons.count()
        if total_lessons == 0:
            self.progress = 0
        else:
            completed_lessons = self.lesson_progress.filter(is_completed=True).count()
            self.progress = round((completed_lessons / total_lessons) * 100, 2)
        
        # Check if course is completed
        if self.progress == 100 and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
            # Award points for completion
            self.student.add_points(100)
        
        self.save()


class LessonProgress(models.Model):
    """Track student progress in lessons"""
    
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    time_spent_minutes = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['enrollment', 'lesson']
    
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.lesson.title}"


class QuizAttempt(models.Model):
    """Student quiz attempts"""
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    
    score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    points_earned = models.IntegerField(default=0)
    is_passed = models.BooleanField(default=False)
    
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} ({self.score}%)"


class AssignmentSubmission(models.Model):
    """Student assignment submissions"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        GRADED = 'GRADED', 'Graded'
        RETURNED = 'RETURNED', 'Returned for Revision'
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    
    submission_file = models.FileField(upload_to='submissions/')
    submission_text = models.TextField(blank=True)
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Grading
    grade = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(blank=True, null=True)
    graded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions'
    )
    
    class Meta:
        unique_together = ['student', 'assignment']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"


class Certificate(models.Model):
    """Course completion certificates"""
    
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate')
    certificate_id = models.CharField(max_length=50, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Certificate - {self.enrollment.student.username} - {self.enrollment.course.title}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_id:
            import uuid
            self.certificate_id = f"EDU-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)