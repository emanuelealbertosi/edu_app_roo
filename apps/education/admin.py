from django.contrib import admin
from django.db import models # Import models
from django_json_widget.widgets import JSONEditorWidget # Import the widget
from .models import (
    QuizTemplate, QuestionTemplate, AnswerOptionTemplate,
    Quiz, Question, AnswerOption, Pathway, PathwayQuiz,
    QuizAttempt, StudentAnswer, PathwayProgress,
    QuizAssignment, PathwayAssignment # Aggiungi i nuovi modelli
)

# --- Inlines ---

class AnswerOptionTemplateInline(admin.TabularInline):
    model = AnswerOptionTemplate
    extra = 2

class QuestionTemplateInline(admin.StackedInline): # O TabularInline se preferito
    model = QuestionTemplate
    extra = 1
    show_change_link = True # Permette di navigare alla domanda per aggiungere opzioni
    # Non possiamo mettere l'inline delle opzioni qui direttamente in modo semplice

class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True

class PathwayQuizInline(admin.TabularInline):
    model = PathwayQuiz
    extra = 1
    autocomplete_fields = ['quiz']

class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0 # Generalmente non si aggiungono risposte manualmente qui
    fields = ('question', 'selected_answers', 'is_correct', 'score') # Campi da mostrare
    readonly_fields = ('question', 'selected_answers') # Risposta data dallo studente
    # Potremmo permettere la modifica di is_correct/score qui per grading?
    # Dipende dal flusso di lavoro desiderato.

# --- ModelAdmins ---

@admin.register(QuizTemplate)
class QuizTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'admin', 'created_at')
    search_fields = ('title', 'description', 'admin__username')
    inlines = [QuestionTemplateInline]
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

@admin.register(QuestionTemplate)
class QuestionTemplateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'quiz_template', 'question_type', 'order')
    list_filter = ('question_type', 'quiz_template')
    search_fields = ('text', 'quiz_template__title')
    inlines = [AnswerOptionTemplateInline] # Mostra opzioni per MC/TF
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'source_template', 'created_at', 'available_from', 'available_until')
    list_filter = ('teacher', 'source_template')
    search_fields = ('title', 'description', 'teacher__username')
    autocomplete_fields = ['teacher', 'source_template']
    inlines = [QuestionInline]
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'quiz', 'question_type', 'order')
    list_filter = ('question_type', 'quiz')
    search_fields = ('text', 'quiz__title')
    inlines = [AnswerOptionInline]
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

@admin.register(Pathway)
class PathwayAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'created_at')
    search_fields = ('title', 'description', 'teacher__username')
    autocomplete_fields = ['teacher']
    inlines = [PathwayQuizInline]
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'status', 'score', 'started_at', 'completed_at')
    list_filter = ('status', 'quiz') # Rimosso 'student__teacher'
    search_fields = ('student__first_name', 'student__last_name', 'quiz__title')
    autocomplete_fields = ['student', 'quiz']
    readonly_fields = ('started_at', 'completed_at', 'score') # Gestiti da logica
    list_select_related = ('student', 'quiz')
    inlines = [StudentAnswerInline] # Mostra le risposte date

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('quiz_attempt', 'question', 'is_correct', 'score')
    list_filter = ('is_correct', 'question__question_type', 'quiz_attempt__quiz')
    search_fields = ('quiz_attempt__student__first_name', 'quiz_attempt__student__last_name', 'question__text')
    autocomplete_fields = ['quiz_attempt', 'question']
    readonly_fields = ('selected_answers',) # Risposta dello studente
    list_select_related = ('quiz_attempt__student', 'question')

@admin.register(PathwayProgress)
class PathwayProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'pathway', 'status', 'last_completed_quiz_order', 'started_at', 'completed_at')
    list_filter = ('status', 'pathway') # Rimosso 'student__teacher'
    search_fields = ('student__first_name', 'student__last_name', 'pathway__title')
    autocomplete_fields = ['student', 'pathway']
    # Aggiunto completed_orders ai readonly se non si vuole modificarlo manualmente
    readonly_fields = ('started_at', 'completed_at', 'last_completed_quiz_order', 'completed_orders') 
    list_select_related = ('student', 'pathway')
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget}, # Aggiunto per completed_orders
    }

@admin.register(QuizAssignment)
class QuizAssignmentAdmin(admin.ModelAdmin):
    # Rimosso 'due_date' da list_display e list_filter
    list_display = ('student', 'group', 'quiz', 'assigned_at') # Aggiunto group, rimosso assigned_by
    list_filter = ('assigned_at', 'quiz__teacher', 'group') # Aggiunto filtro per gruppo
    search_fields = ('student__first_name', 'student__last_name', 'group__name', 'quiz__title') # Aggiunto group__name, rimosso assigned_by__username
    autocomplete_fields = ['student', 'group', 'quiz'] # Aggiunto group, rimosso assigned_by
    list_select_related = ('student', 'group', 'quiz') # Aggiunto group, rimosso assigned_by

@admin.register(PathwayAssignment)
class PathwayAssignmentAdmin(admin.ModelAdmin):
    # Rimosso 'due_date' da list_display e list_filter
    list_display = ('student', 'group', 'pathway', 'assigned_at') # Aggiunto group, rimosso assigned_by
    list_filter = ('assigned_at', 'pathway__teacher', 'group') # Aggiunto filtro per gruppo
    search_fields = ('student__first_name', 'student__last_name', 'group__name', 'pathway__title') # Aggiunto group__name, rimosso assigned_by__username
    autocomplete_fields = ['student', 'group', 'pathway'] # Aggiunto group, rimosso assigned_by
    list_select_related = ('student', 'group', 'pathway') # Aggiunto group, rimosso assigned_by

# Non registriamo AnswerOptionTemplate, AnswerOption, PathwayQuiz direttamente (gestiti da inline)
