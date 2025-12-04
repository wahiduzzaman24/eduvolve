from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Course browsing
    path('', views.course_list, name='course_list'),
    path('course/<int:pk>/', views.course_detail, name='course_detail'),
    path('course/<int:pk>/enroll/', views.enroll_course, name='enroll_course'),

    # Instructor - Course management
    path('course/create/', views.course_create, name='course_create'),
    path('course/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('course/<int:pk>/manage/', views.course_manage, name='course_manage'),
    path('course//edit/', views.course_edit, name='course_edit'),
    path('course//delete/', views.course_delete, name='course_delete'),
    path('course//lesson/create/', views.lesson_create, name='lesson_create'),

    # Instructor - Lesson management
    path('course/<int:course_pk>/lesson/create/',
         views.lesson_create, name='lesson_create'),
    path('lesson/<int:pk>/edit/', views.lesson_edit, name='lesson_edit'),
    path('lesson/<int:pk>/delete/', views.lesson_delete, name='lesson_delete'),
    path('lesson//edit/', views.lesson_edit, name='lesson_edit'),
    path('lesson//delete/', views.lesson_delete, name='lesson_delete'),

    # Student - Lesson viewing
    path('lesson/<int:pk>/', views.lesson_view, name='lesson_view'),
    path('lesson/<int:pk>/complete/',
         views.complete_lesson, name='complete_lesson'),

    # Instructor - Quiz management
    path('lesson/<int:lesson_pk>/quiz/create/',
         views.quiz_create, name='quiz_create'),
    path('quiz/<int:pk>/edit/', views.quiz_edit, name='quiz_edit'),
    path('quiz/<int:pk>/manage/', views.quiz_manage, name='quiz_manage'),
    path('quiz/<int:pk>/delete/', views.quiz_delete, name='quiz_delete'),

    # Instructor - Question management
    path('quiz/<int:quiz_pk>/question/create/',
         views.question_create, name='question_create'),
    path('question/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('question/<int:pk>/delete/',
         views.question_delete, name='question_delete'),

    # Instructor - Assignment management
    path('lesson/<int:lesson_pk>/assignment/create/',
         views.assignment_create, name='assignment_create'),
    path('assignment/<int:pk>/edit/',
         views.assignment_edit, name='assignment_edit'),
    path('assignment/<int:pk>/delete/',
         views.assignment_delete, name='assignment_delete'),
    path('assignment/<int:pk>/submissions/',
         views.assignment_submissions, name='assignment_submissions'),
    path('submission/<int:pk>/grade/',
         views.assignment_grade, name='assignment_grade'),

    # Student - Quiz
    path('quiz/<int:pk>/take/', views.quiz_take, name='quiz_take'),
    path('quiz/result/<int:pk>/', views.quiz_result, name='quiz_result'),

    # Student - Assignment
    path('assignment/<int:pk>/submit/',
         views.assignment_submit, name='assignment_submit'),


]
