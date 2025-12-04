from django import forms
from django.forms import inlineformset_factory
from .models import (
    Course, Lesson, Quiz, Question, Answer,
    Assignment, AssignmentSubmission
)

class CourseForm(forms.ModelForm):
    """Form for creating/editing courses"""
    
    class Meta:
        model = Course
        fields = ['title', 'description', 'thumbnail', 'level', 'duration_weeks', 'is_published']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'thumbnail' and field != 'is_published':
                self.fields[field].widget.attrs.update({'class': 'form-control'})
            elif field == 'is_published':
                self.fields[field].widget.attrs.update({'class': 'form-check-input'})


class LessonForm(forms.ModelForm):
    """Form for creating/editing lessons"""
    
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'order', 'video_url', 'duration_minutes', 'content', 'attachments', 'is_published']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['attachments', 'is_published']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
            elif field == 'is_published':
                self.fields[field].widget.attrs.update({'class': 'form-check-input'})


class QuizForm(forms.ModelForm):
    """Form for creating/editing quizzes"""
    
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'passing_score', 'time_limit_minutes']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class QuestionForm(forms.ModelForm):
    """Form for creating/editing quiz questions"""
    
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'points', 'order']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class AnswerForm(forms.ModelForm):
    """Form for creating/editing answers"""
    
    class Meta:
        model = Answer
        fields = ['answer_text', 'is_correct', 'order']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['answer_text'].widget.attrs.update({'class': 'form-control'})
        self.fields['is_correct'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['order'].widget.attrs.update({'class': 'form-control'})


# Formset for managing multiple answers
AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    form=AnswerForm,
    extra=4,
    can_delete=True
)


class AssignmentForm(forms.ModelForm):
    """Form for creating/editing assignments"""
    
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'max_points', 'attachment']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'attachment':
                self.fields[field].widget.attrs.update({'class': 'form-control'})


class AssignmentSubmissionForm(forms.ModelForm):
    """Form for submitting assignments"""
    
    class Meta:
        model = AssignmentSubmission
        fields = ['submission_file', 'submission_text']
        widgets = {
            'submission_text': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Additional notes or comments...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['submission_text'].widget.attrs.update({'class': 'form-control'})
        self.fields['submission_text'].required = False


class AssignmentGradeForm(forms.ModelForm):
    """Form for grading assignments"""
    
    class Meta:
        model = AssignmentSubmission
        fields = ['grade', 'feedback', 'status']
        widgets = {
            'feedback': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})