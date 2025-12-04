from django.contrib import admin
from .models import (
    Course, Lesson, Quiz, Question, Answer,
    Assignment, Enrollment, LessonProgress,
    QuizAttempt, AssignmentSubmission, Certificate
)

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ['title', 'order', 'video_url', 'is_published']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'level', 'is_published', 'created_at']
    list_filter = ['level', 'is_published', 'created_at']
    search_fields = ['title', 'description', 'instructor__username']
    inlines = [LessonInline]


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'quiz', 'question_type', 'points', 'order']
    list_filter = ['question_type', 'quiz']
    inlines = [AnswerInline]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'passing_score', 'time_limit_minutes']
    list_filter = ['passing_score']
    search_fields = ['title', 'lesson__title']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'duration_minutes', 'is_published']
    list_filter = ['is_published', 'course']
    search_fields = ['title', 'course__title']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'due_date', 'max_points']
    list_filter = ['due_date']
    search_fields = ['title', 'lesson__title']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'progress', 'enrolled_at', 'is_active']
    list_filter = ['is_active', 'enrolled_at']
    search_fields = ['student__username', 'course__title']


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'lesson', 'is_completed', 'completed_at']
    list_filter = ['is_completed', 'completed_at']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'score', 'is_passed', 'submitted_at']
    list_filter = ['is_passed', 'submitted_at']
    search_fields = ['student__username', 'quiz__title']


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'assignment', 'status', 'grade', 'submitted_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['student__username', 'assignment__title']


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_id', 'enrollment', 'issued_at']
    search_fields = ['certificate_id', 'enrollment__student__username']