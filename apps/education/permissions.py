from rest_framework import permissions
from apps.users.models import UserRole, User # Import User model


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permette accesso completo agli Admin, accesso in sola lettura agli altri utenti autenticati.
    Utile per i QuizTemplate.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        # Check if user is a Django User and has ADMIN role
        return isinstance(request.user, User) and request.user.role == UserRole.ADMIN

class IsQuizTemplateOwnerOrAdmin(permissions.BasePermission):
    """
    Permette modifiche solo all'Admin creatore del template.
    (In realtà, tutti gli Admin possono modificare tutti i template per semplicità).
    Lettura permessa a tutti gli autenticati (specialmente Docenti).
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            # Allow read access for authenticated users (Teachers mainly)
            return request.user and request.user.is_authenticated
        # Write access only for Admins
        return request.user and request.user.is_authenticated and isinstance(request.user, User) and request.user.role == UserRole.ADMIN

class IsQuizOwnerOrAdmin(permissions.BasePermission): # Renamed
    """
    Permette accesso:
    - View Level (list, create): Solo a Docenti o Admin autenticati.
    - Object Level (retrieve, update, delete): Solo al Docente creatore o Admin autenticati.
    """
    def has_permission(self, request, view):
        # Allow access only to authenticated Teachers or Admins for list/create actions
        return (
            request.user and
            request.user.is_authenticated and
            isinstance(request.user, User) and # Check it's a Django User
            (request.user.role == UserRole.TEACHER or request.user.role == UserRole.ADMIN)
        )

    def has_object_permission(self, request, view, obj):
        # Already checked for authenticated Teacher/Admin in has_permission
        # Now check ownership for object-specific actions (safe or unsafe methods)
        if not request.user or not isinstance(request.user, User): # Should not happen if has_permission passed, but safe check
             return False

        is_owner = obj.teacher == request.user and request.user.role == UserRole.TEACHER
        is_admin = request.user.role == UserRole.ADMIN
        return is_owner or is_admin
class IsPathwayOwnerOrAdmin(permissions.BasePermission): # Renamed
    """
    Permette accesso:
    - View Level (list, create): Solo a Docenti o Admin autenticati.
    - Object Level (retrieve, update, delete): Solo al Docente creatore o Admin autenticati.
    """
    def has_permission(self, request, view):
        # Allow access only to authenticated Teachers or Admins for list/create actions
        return (
            request.user and
            request.user.is_authenticated and
            isinstance(request.user, User) and # Check it's a Django User
            (request.user.role == UserRole.TEACHER or request.user.role == UserRole.ADMIN)
        )

    def has_object_permission(self, request, view, obj):
        # Already checked for authenticated Teacher/Admin in has_permission
        # Now check ownership for object-specific actions (safe or unsafe methods)
        if not request.user or not isinstance(request.user, User): # Should not happen if has_permission passed, but safe check
             return False

        is_owner = obj.teacher == request.user and request.user.role == UserRole.TEACHER
        is_admin = request.user.role == UserRole.ADMIN
        return is_owner or is_admin

class IsStudentOwnerForAttempt(permissions.BasePermission):
    """
    Permette accesso solo allo Studente proprietario del tentativo/progresso.
    """
    def has_object_permission(self, request, view, obj):
        # obj può essere QuizAttempt, StudentAnswer, PathwayProgress
        # Usa request.student impostato da StudentJWTAuthentication
        student = getattr(request, 'student', None)
        if not student:
            return False

        if hasattr(obj, 'student'): # Per QuizAttempt, PathwayProgress
            return obj.student == student
        elif hasattr(obj, 'quiz_attempt'): # Per StudentAnswer
            return obj.quiz_attempt.student == student
        return False

class IsTeacherOfStudentForAttempt(permissions.BasePermission):
    """
    Permette accesso al Docente associato allo Studente del tentativo/progresso.
    Utile per vedere risultati o correggere risposte manuali.
    """
    def has_object_permission(self, request, view, obj):
        student = None
        if hasattr(obj, 'student'):
            student = obj.student
        elif hasattr(obj, 'quiz_attempt'):
            student = obj.quiz_attempt.student

        if student:
            return student.teacher == request.user and request.user.role == UserRole.TEACHER
        return False

class IsAnswerOptionOwner(permissions.BasePermission):
    """
    Permette modifiche solo al Docente creatore del Quiz a cui appartiene la Domanda dell'Opzione,
    o a un Admin.
    """
    def has_object_permission(self, request, view, obj):
        # obj is an AnswerOption instance
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(obj, 'question') and hasattr(obj.question, 'quiz') and hasattr(obj.question.quiz, 'teacher'):
            is_owner = obj.question.quiz.teacher == request.user and request.user.role == UserRole.TEACHER
            is_admin = request.user.role == UserRole.ADMIN
            # Allow read access for safe methods if needed, otherwise restrict
            # if request.method in permissions.SAFE_METHODS:
            #     return is_owner or is_admin # Or potentially broader access
            return is_owner or is_admin
        return False

# Potremmo aggiungere permessi più granulari, es. per assegnare quiz/percorsi.