from rest_framework import serializers
from .models import (
    QuizTemplate, QuestionTemplate, AnswerOptionTemplate,
    Quiz, Question, AnswerOption, Pathway, PathwayQuiz,
    QuizAttempt, StudentAnswer, PathwayProgress, QuestionType
)
from apps.users.serializers import UserSerializer, StudentSerializer # Per info utente/studente

# --- Template Serializers ---

class AnswerOptionTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOptionTemplate
        fields = ['id', 'text', 'is_correct', 'order']


class QuestionTemplateSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionTemplateSerializer(
        many=True,
        source='answer_option_templates', # Usa related_name
        read_only=True # Le opzioni sono gestite tramite endpoint dedicati o nested write
    )
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)

    class Meta:
        model = QuestionTemplate
        fields = [
            'id', 'quiz_template', 'text', 'question_type', 'question_type_display',
            'order', 'metadata', 'answer_options'
        ]
        read_only_fields = ['quiz_template'] # Associato tramite URL


class QuizTemplateSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(source='admin.username', read_only=True)
    # Potremmo includere le domande nested in lettura, ma può essere pesante.
    # Meglio un endpoint separato per le domande di un template.
    # questions = QuestionTemplateSerializer(many=True, source='question_templates', read_only=True)

    class Meta:
        model = QuizTemplate
        fields = [
            'id', 'admin', 'admin_username', 'title', 'description', 'metadata', 'created_at'
            # 'questions' # Escluso per performance
        ]
        read_only_fields = ['admin', 'admin_username', 'created_at']


# --- Concrete Serializers ---

class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ['id', 'text', 'is_correct', 'order']


class QuestionSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionSerializer(
        many=True,
        # source='answer_options', # Rimosso perché ridondante
        read_only=True
    )
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)

    class Meta:
        model = Question
        fields = [
            'id', 'quiz', 'text', 'question_type', 'question_type_display',
            'order', 'metadata', 'answer_options'
        ]
        read_only_fields = ['quiz']


class QuizSerializer(serializers.ModelSerializer):
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    # questions = QuestionSerializer(many=True, source='questions', read_only=True) # Escluso per performance

    class Meta:
        model = Quiz
        fields = [
            'id', 'teacher', 'teacher_username', 'source_template', 'title', 'description',
            'metadata', 'created_at', 'available_from', 'available_until'
            # 'questions' # Escluso
        ]
        read_only_fields = ['teacher', 'teacher_username', 'created_at']


class PathwayQuizSerializer(serializers.ModelSerializer):
    """ Serializer per la relazione M2M Pathway-Quiz (usato nested in Pathway). """
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)

    class Meta:
        model = PathwayQuiz
        fields = ['id', 'quiz', 'quiz_title', 'order']


class PathwaySerializer(serializers.ModelSerializer):
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    # Mostra i quiz nel percorso con il loro ordine
    quiz_details = PathwayQuizSerializer(source='pathwayquiz_set', many=True, read_only=True)

    class Meta:
        model = Pathway
        fields = [
            'id', 'teacher', 'teacher_username', 'title', 'description',
            'metadata', 'created_at', 'quiz_details'
        ]
        read_only_fields = ['teacher', 'teacher_username', 'created_at', 'quiz_details']


# --- Student Progress/Attempt Serializers ---

class StudentAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    question_type = serializers.CharField(source='question.question_type', read_only=True)

    class Meta:
        model = StudentAnswer
        fields = [
            'id', 'quiz_attempt', 'question', 'question_text', 'question_type',
            'selected_answers', 'is_correct', 'score', 'answered_at'
        ]
        read_only_fields = [
            'quiz_attempt', 'question', 'question_text', 'question_type',
            'is_correct', 'score', 'answered_at'
            # 'selected_answers' è scrivibile solo in fase di submit
        ]


class QuizAttemptSerializer(serializers.ModelSerializer):
    student_info = StudentSerializer(source='student', read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    # Opzionale: includere le risposte date dallo studente
    # student_answers = StudentAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'student', 'student_info', 'quiz', 'quiz_title', 'started_at',
            'completed_at', 'score', 'status', 'status_display'
            # 'student_answers' # Escluso per performance, usare endpoint dedicato
        ]
        read_only_fields = fields # Gli attempt sono gestiti da azioni specifiche


# Serializer dettagliato per QuizAttempt che include le domande
class QuizAttemptDetailSerializer(QuizAttemptSerializer):
    # Usa il QuestionSerializer che include già le AnswerOptionSerializer nested
    questions = QuestionSerializer(source='quiz.questions', many=True, read_only=True)
    # Potremmo aggiungere anche le risposte già date dallo studente per questo tentativo
    given_answers = StudentAnswerSerializer(source='student_answers', many=True, read_only=True)

    class Meta(QuizAttemptSerializer.Meta): # Eredita Meta dal serializer base
         fields = QuizAttemptSerializer.Meta.fields + ['questions', 'given_answers']
         read_only_fields = fields # Anche questo è read-only


class PathwayProgressSerializer(serializers.ModelSerializer):
    student_info = StudentSerializer(source='student', read_only=True)
    pathway_title = serializers.CharField(source='pathway.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PathwayProgress
        fields = [
            'id', 'student', 'student_info', 'pathway', 'pathway_title',
            'last_completed_quiz_order', 'started_at', 'completed_at', 'status', 'status_display'
        ]
        read_only_fields = fields # Il progresso è gestito internamente