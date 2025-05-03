from rest_framework import serializers
from .models import (
    QuizAttempt, StudentAnswer, PathwayProgress, QuizAssignment, PathwayAssignment,
    Quiz, Question, Pathway
)

# --- GDPR Serializers for Education Data ---

class GDPRQuizSerializer(serializers.ModelSerializer):
    """Minimal quiz info for GDPR export."""
    class Meta:
        model = Quiz
        fields = ('id', 'title')

class GDPRQuestionSerializer(serializers.ModelSerializer):
    """Minimal question info for GDPR export."""
    class Meta:
        model = Question
        fields = ('id', 'text', 'question_type')

class GDPRStudentAnswerSerializer(serializers.ModelSerializer):
    """Serializer for student's answers for GDPR export."""
    question = GDPRQuestionSerializer(read_only=True)
    # selected_answers: Contains the actual answer provided by the student.
    # score: Score obtained for this specific answer (if applicable).
    # is_correct: Whether the answer was marked as correct.
    class Meta:
        model = StudentAnswer
        fields = ('id', 'question', 'selected_answers', 'score', 'is_correct', 'submitted_at')

class GDPRQuizAttemptSerializer(serializers.ModelSerializer):
    """Serializer for quiz attempts for GDPR export."""
    quiz = GDPRQuizSerializer(read_only=True)
    student_answers = GDPRStudentAnswerSerializer(many=True, read_only=True, source='student_answers') # Use source
    # status: e.g., COMPLETED, FAILED
    # score: Final score for the attempt.
    # started_at, completed_at: Timestamps for the attempt.
    class Meta:
        model = QuizAttempt
        fields = ('id', 'quiz', 'status', 'score', 'started_at', 'completed_at', 'student_answers')


class GDPRPathwaySerializer(serializers.ModelSerializer):
    """Minimal pathway info for GDPR export."""
    class Meta:
        model = Pathway
        fields = ('id', 'title')

class GDPRPathwayProgressSerializer(serializers.ModelSerializer):
    """Serializer for pathway progress for GDPR export."""
    pathway = GDPRPathwaySerializer(read_only=True)
    # status: e.g., IN_PROGRESS, COMPLETED
    # last_completed_quiz_order: Tracks progress within the pathway.
    # started_at, completed_at: Timestamps for the pathway attempt.
    # completed_orders: List of completed step orders.
    class Meta:
        model = PathwayProgress
        fields = ('id', 'pathway', 'status', 'last_completed_quiz_order', 'completed_orders', 'started_at', 'completed_at')

class GDPRQuizAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for quiz assignments for GDPR export."""
    quiz = GDPRQuizSerializer(read_only=True)
    # assigned_at: Timestamp of assignment.
    # due_date: Optional due date.
    # status: e.g., PENDING, COMPLETED (if tracking is needed here)
    class Meta:
        model = QuizAssignment
        fields = ('id', 'quiz', 'assigned_at', 'due_date', 'status') # Added status

class GDPRPathwayAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for pathway assignments for GDPR export."""
    pathway = GDPRPathwaySerializer(read_only=True)
    # assigned_at: Timestamp of assignment.
    # due_date: Optional due date.
    # status: e.g., PENDING, COMPLETED (if tracking is needed here)
    class Meta:
        model = PathwayAssignment
        fields = ('id', 'pathway', 'assigned_at', 'due_date', 'status') # Added status