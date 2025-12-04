from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import JsonResponse
from accounts.models import User
from .models import (
    Course, Lesson, Quiz, Question, Answer, Assignment,
    Enrollment, LessonProgress, QuizAttempt, AssignmentSubmission, Certificate
)
from .forms import (
    CourseForm, LessonForm, QuizForm, QuestionForm, AnswerFormSet,
    AssignmentForm, AssignmentSubmissionForm
)


@login_required
def dashboard(request):
    """Main dashboard - redirects based on user role"""
    if request.user.is_admin():
        return admin_dashboard(request)
    elif request.user.is_instructor():
        return instructor_dashboard(request)
    else:
        return student_dashboard(request)


@login_required
def admin_dashboard(request):
    """Admin dashboard"""
    total_users = User.objects.count()
    total_courses = Course.objects.count()
    total_students = User.objects.filter(role='STUDENT').count()
    total_instructors = User.objects.filter(role='INSTRUCTOR').count()

    recent_courses = Course.objects.all()[:5]
    recent_users = User.objects.all()[:10]

    context = {
        'total_users': total_users,
        'total_courses': total_courses,
        'total_students': total_students,
        'total_instructors': total_instructors,
        'recent_courses': recent_courses,
        'recent_users': recent_users,
    }
    return render(request, 'courses/admin_dashboard.html', context)


@login_required
def instructor_dashboard(request):
    """Instructor dashboard"""
    my_courses = Course.objects.filter(instructor=request.user)
    total_students = Enrollment.objects.filter(
        course__instructor=request.user,
        is_active=True
    ).count()

    # Pending submissions
    pending_submissions = AssignmentSubmission.objects.filter(
        assignment__lesson__course__instructor=request.user,
        status='PENDING'
    ).count()

    context = {
        'my_courses': my_courses,
        'total_students': total_students,
        'pending_submissions': pending_submissions,
    }
    return render(request, 'courses/instructor_dashboard.html', context)


@login_required
def student_dashboard(request):
    """Student dashboard"""
    enrolled_courses = Enrollment.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('course')

    # Update streak
    request.user.update_streak()

    # Get recent activity
    recent_progress = LessonProgress.objects.filter(
        enrollment__student=request.user
    ).order_by('-completed_at')[:5]

    context = {
        'enrolled_courses': enrolled_courses,
        'total_points': request.user.total_points,
        'current_streak': request.user.current_streak,
        'longest_streak': request.user.longest_streak,
        'recent_progress': recent_progress,
    }
    return render(request, 'courses/student_dashboard.html', context)


@login_required
def course_list(request):
    """List all published courses"""
    courses = Course.objects.filter(
        is_published=True).select_related('instructor')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Filter by level
    level = request.GET.get('level', '')
    if level:
        courses = courses.filter(level=level)

    context = {
        'courses': courses,
        'search_query': search_query,
        'level': level,
    }
    return render(request, 'courses/course_list.html', context)


@login_required
def course_detail(request, pk):
    """Course detail page"""
    course = get_object_or_404(Course, pk=pk, is_published=True)
    lessons = course.lessons.filter(is_published=True)

    is_enrolled = False
    enrollment = None

    if request.user.is_student():
        enrollment = Enrollment.objects.filter(
            student=request.user,
            course=course,
            is_active=True
        ).first()
        is_enrolled = enrollment is not None

    context = {
        'course': course,
        'lessons': lessons,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
    }
    return render(request, 'courses/course_detail.html', context)


@login_required
def enroll_course(request, pk):
    """Enroll in a course"""
    if not request.user.is_student():
        messages.error(request, 'Only students can enroll in courses.')
        return redirect('courses:course_list')

    course = get_object_or_404(Course, pk=pk, is_published=True)

    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={'is_active': True}
    )

    if created:
        messages.success(request, f'Successfully enrolled in {course.title}!')
        request.user.add_points(10)  # Award points for enrollment
    else:
        enrollment.is_active = True
        enrollment.save()
        messages.info(request, f'You are already enrolled in {course.title}.')

    return redirect('courses:course_detail', pk=pk)


@login_required
def lesson_view(request, pk):
    """View a lesson"""
    lesson = get_object_or_404(Lesson, pk=pk, is_published=True)

    # Check enrollment
    if request.user.is_student():
        enrollment = get_object_or_404(
            Enrollment,
            student=request.user,
            course=lesson.course,
            is_active=True
        )

        # Get or create lesson progress
        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson
        )
    else:
        enrollment = None
        progress = None

    context = {
        'lesson': lesson,
        'course': lesson.course,
        'enrollment': enrollment,
        'progress': progress,
    }
    return render(request, 'courses/lesson_view.html', context)


@login_required
def complete_lesson(request, pk):
    """Mark lesson as completed"""
    if not request.user.is_student():
        return JsonResponse({'error': 'Only students can complete lessons'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    lesson = get_object_or_404(Lesson, pk=pk)
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=lesson.course,
        is_active=True
    )

    progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )

    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save()

        # Update enrollment progress
        enrollment.update_progress()

        # Award points
        request.user.add_points(20)

        return JsonResponse({
            'success': True,
            'message': 'Lesson completed!',
            'points_earned': 20
        })

    return JsonResponse({'success': True, 'message': 'Already completed'})


@login_required
def quiz_take(request, pk):
    """Take a quiz"""
    quiz = get_object_or_404(Quiz, pk=pk)
    questions = quiz.questions.prefetch_related('answers').all()

    if request.method == 'POST':
        # Calculate score
        total_points = quiz.get_total_points()
        earned_points = 0

        for question in questions:
            answer_id = request.POST.get(f'question_{question.id}')
            if answer_id:
                answer = Answer.objects.filter(
                    id=answer_id,
                    question=question,
                    is_correct=True
                ).first()

                if answer:
                    earned_points += question.points

        score = (earned_points / total_points * 100) if total_points > 0 else 0
        is_passed = score >= quiz.passing_score

        # Save attempt
        attempt = QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz,
            score=score,
            points_earned=earned_points,
            is_passed=is_passed,
            submitted_at=timezone.now()
        )

        # Award points if passed
        if is_passed:
            request.user.add_points(earned_points)

        messages.success(request, f'Quiz submitted! Score: {score:.1f}%')
        return redirect('courses:quiz_result', pk=attempt.id)

    context = {
        'quiz': quiz,
        'questions': questions,
    }
    return render(request, 'courses/quiz_take.html', context)


@login_required
def quiz_result(request, pk):
    """View quiz result"""
    attempt = get_object_or_404(QuizAttempt, pk=pk, student=request.user)

    context = {
        'attempt': attempt,
        'quiz': attempt.quiz,
    }
    return render(request, 'courses/quiz_result.html', context)


@login_required
def assignment_submit(request, pk):
    """Submit an assignment"""
    assignment = get_object_or_404(Assignment, pk=pk)

    # Check enrollment
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=assignment.lesson.course,
        is_active=True
    )

    # Check if already submitted
    existing_submission = AssignmentSubmission.objects.filter(
        student=request.user,
        assignment=assignment
    ).first()

    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.student = request.user
            submission.assignment = assignment

            if existing_submission:
                # Update existing submission
                existing_submission.submission_file = submission.submission_file
                existing_submission.submission_text = submission.submission_text
                existing_submission.submitted_at = timezone.now()
                existing_submission.status = 'PENDING'
                existing_submission.save()
                messages.success(
                    request, 'Assignment resubmitted successfully!')
            else:
                submission.save()
                messages.success(request, 'Assignment submitted successfully!')

            return redirect('courses:lesson_view', pk=assignment.lesson.id)
    else:
        form = AssignmentSubmissionForm()

    context = {
        'assignment': assignment,
        'form': form,
        'existing_submission': existing_submission,
    }
    return render(request, 'courses/assignment_submit.html', context)


@login_required
def course_create(request):
    """Create a new course (Instructor only)"""
    if not request.user.is_instructor():
        messages.error(request, 'Only instructors can create courses.')
        return redirect('courses:dashboard')

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(
                request, f'Course "{course.title}" created successfully!')
            return redirect('courses:course_manage', pk=course.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseForm()

    context = {
        'form': form,
        'action': 'Create',
    }
    return render(request, 'courses/course_form.html', context)


@login_required
def course_edit(request, pk):
    """Edit a course (Instructor only)"""
    course = get_object_or_404(Course, pk=pk, instructor=request.user)

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Course "{course.title}" updated successfully!')
            return redirect('courses:course_manage', pk=course.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseForm(instance=course)

    context = {
        'form': form,
        'course': course,
        'action': 'Edit',
    }
    return render(request, 'courses/course_form.html', context)


@login_required
def course_manage(request, pk):
    """Manage course content (Instructor only)"""
    course = get_object_or_404(Course, pk=pk, instructor=request.user)
    lessons = course.lessons.all().order_by('order')

    context = {
        'course': course,
        'lessons': lessons,
    }
    return render(request, 'courses/course_manage.html', context)


@login_required
def lesson_create(request, course_pk):
    """Create a new lesson (Instructor only)"""
    course = get_object_or_404(Course, pk=course_pk, instructor=request.user)

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(
                request, f'Lesson "{lesson.title}" created successfully!')
            return redirect('courses:course_manage', pk=course.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Set default order
        last_lesson = course.lessons.order_by('-order').first()
        initial_order = (last_lesson.order + 1) if last_lesson else 1
        form = LessonForm(initial={'order': initial_order})

    context = {
        'form': form,
        'course': course,
        'action': 'Create',
    }
    return render(request, 'courses/lesson_form.html', context)


@login_required
def lesson_edit(request, pk):
    """Edit a lesson (Instructor only)"""
    lesson = get_object_or_404(Lesson, pk=pk, course__instructor=request.user)

    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Lesson "{lesson.title}" updated successfully!')
            return redirect('courses:course_manage', pk=lesson.course.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LessonForm(instance=lesson)

    context = {
        'form': form,
        'lesson': lesson,
        'course': lesson.course,
        'action': 'Edit',
    }
    return render(request, 'courses/lesson_form.html', context)


@login_required
def lesson_delete(request, pk):
    """Delete a lesson (Instructor only)"""
    lesson = get_object_or_404(Lesson, pk=pk, course__instructor=request.user)
    course_id = lesson.course.id

    if request.method == 'POST':
        lesson_title = lesson.title
        lesson.delete()
        messages.success(
            request, f'Lesson "{lesson_title}" deleted successfully!')
        return redirect('courses:course_manage', pk=course_id)

    context = {
        'lesson': lesson,
    }
    return render(request, 'courses/lesson_confirm_delete.html', context)


@login_required
def course_delete(request, pk):
    """Delete a course (Instructor only)"""
    course = get_object_or_404(Course, pk=pk, instructor=request.user)

    if request.method == 'POST':
        course_title = course.title
        course.delete()
        messages.success(
            request, f'Course "{course_title}" deleted successfully!')
        return redirect('courses:dashboard')

    context = {
        'course': course,
    }
    return render(request, 'courses/course_confirm_delete.html', context)


# Quiz Management Views

@login_required
def quiz_create(request, lesson_pk):
    """Create a quiz for a lesson (Instructor only)"""
    lesson = get_object_or_404(
        Lesson, pk=lesson_pk, course__instructor=request.user)

    # Check if quiz already exists
    if hasattr(lesson, 'quiz'):
        messages.warning(
            request, 'This lesson already has a quiz. Edit the existing one.')
        return redirect('courses:quiz_edit', pk=lesson.quiz.id)

    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.lesson = lesson
            quiz.save()
            messages.success(
                request, f'Quiz "{quiz.title}" created successfully! Now add questions.')
            return redirect('courses:question_create', quiz_pk=quiz.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuizForm(initial={'title': f'{lesson.title} Quiz'})

    context = {
        'form': form,
        'lesson': lesson,
        'action': 'Create',
    }
    return render(request, 'courses/quiz_form.html', context)


@login_required
def quiz_edit(request, pk):
    """Edit a quiz (Instructor only)"""
    quiz = get_object_or_404(
        Quiz, pk=pk, lesson__course__instructor=request.user)

    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Quiz "{quiz.title}" updated successfully!')
            return redirect('courses:quiz_manage', pk=quiz.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuizForm(instance=quiz)

    context = {
        'form': form,
        'quiz': quiz,
        'lesson': quiz.lesson,
        'action': 'Edit',
    }
    return render(request, 'courses/quiz_form.html', context)


@login_required
def quiz_manage(request, pk):
    """Manage quiz questions (Instructor only)"""
    quiz = get_object_or_404(
        Quiz, pk=pk, lesson__course__instructor=request.user)
    questions = quiz.questions.all().order_by('order')

    context = {
        'quiz': quiz,
        'questions': questions,
        'lesson': quiz.lesson,
    }
    return render(request, 'courses/quiz_manage.html', context)


@login_required
def quiz_delete(request, pk):
    """Delete a quiz (Instructor only)"""
    quiz = get_object_or_404(
        Quiz, pk=pk, lesson__course__instructor=request.user)
    lesson = quiz.lesson

    if request.method == 'POST':
        quiz_title = quiz.title
        quiz.delete()
        messages.success(request, f'Quiz "{quiz_title}" deleted successfully!')
        return redirect('courses:lesson_edit', pk=lesson.id)

    context = {
        'quiz': quiz,
    }
    return render(request, 'courses/quiz_confirm_delete.html', context)


# Question Management Views

@login_required
def question_create(request, quiz_pk):
    """Create a question for a quiz (Instructor only)"""
    quiz = get_object_or_404(
        Quiz, pk=quiz_pk, lesson__course__instructor=request.user)

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        formset = AnswerFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()

            # Save answers
            answers = formset.save(commit=False)
            for answer in answers:
                answer.question = question
                answer.save()

            messages.success(request, 'Question added successfully!')
            return redirect('courses:question_create', quiz_pk=quiz.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Set default order
        last_question = quiz.questions.order_by('-order').first()
        initial_order = (last_question.order + 1) if last_question else 1
        form = QuestionForm(initial={'order': initial_order})
        formset = AnswerFormSet()

    context = {
        'form': form,
        'formset': formset,
        'quiz': quiz,
        'action': 'Create',
    }
    return render(request, 'courses/question_form.html', context)


@login_required
def question_edit(request, pk):
    """Edit a question (Instructor only)"""
    question = get_object_or_404(
        Question, pk=pk, quiz__lesson__course__instructor=request.user)

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = AnswerFormSet(request.POST, instance=question)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Question updated successfully!')
            return redirect('courses:quiz_manage', pk=question.quiz.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuestionForm(instance=question)
        formset = AnswerFormSet(instance=question)

    context = {
        'form': form,
        'formset': formset,
        'question': question,
        'quiz': question.quiz,
        'action': 'Edit',
    }
    return render(request, 'courses/question_form.html', context)


@login_required
def question_delete(request, pk):
    """Delete a question (Instructor only)"""
    question = get_object_or_404(
        Question, pk=pk, quiz__lesson__course__instructor=request.user)
    quiz = question.quiz

    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully!')
        return redirect('courses:quiz_manage', pk=quiz.id)

    context = {
        'question': question,
    }
    return render(request, 'courses/question_confirm_delete.html', context)


# Assignment Management Views

@login_required
def assignment_create(request, lesson_pk):
    """Create an assignment for a lesson (Instructor only)"""
    lesson = get_object_or_404(
        Lesson, pk=lesson_pk, course__instructor=request.user)

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.lesson = lesson
            assignment.save()
            messages.success(
                request, f'Assignment "{assignment.title}" created successfully!')
            return redirect('courses:lesson_edit', pk=lesson.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AssignmentForm()

    context = {
        'form': form,
        'lesson': lesson,
        'action': 'Create',
    }
    return render(request, 'courses/assignment_form.html', context)


@login_required
def assignment_edit(request, pk):
    """Edit an assignment (Instructor only)"""
    assignment = get_object_or_404(
        Assignment, pk=pk, lesson__course__instructor=request.user)

    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(
                request, f'Assignment "{assignment.title}" updated successfully!')
            return redirect('courses:lesson_edit', pk=assignment.lesson.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AssignmentForm(instance=assignment)

    context = {
        'form': form,
        'assignment': assignment,
        'lesson': assignment.lesson,
        'action': 'Edit',
    }
    return render(request, 'courses/assignment_form.html', context)


@login_required
def assignment_delete(request, pk):
    """Delete an assignment (Instructor only)"""
    assignment = get_object_or_404(
        Assignment, pk=pk, lesson__course__instructor=request.user)
    lesson = assignment.lesson

    if request.method == 'POST':
        assignment_title = assignment.title
        assignment.delete()
        messages.success(
            request, f'Assignment "{assignment_title}" deleted successfully!')
        return redirect('courses:lesson_edit', pk=lesson.id)

    context = {
        'assignment': assignment,
    }
    return render(request, 'courses/assignment_confirm_delete.html', context)
