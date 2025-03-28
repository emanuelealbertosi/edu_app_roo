from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied # Importa l'eccezione
from .models import UserRole, User, Student # Import UserRole, User, Student

class IsAdminUser(permissions.BasePermission):
    """
    Permesso personalizzato per consentire l'accesso solo agli utenti Admin.
    """
    def has_permission(self, request, view):
        # Controlla se l'utente è autenticato e ha il ruolo ADMIN
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.ADMIN)

class IsTeacherUser(permissions.BasePermission):
    """
    Permesso personalizzato per consentire l'accesso solo agli utenti Docenti.
    """
    def has_permission(self, request, view):
        # Controlla se l'utente è autenticato e ha il ruolo TEACHER
        # print(f"[IsTeacherUser] Checking user: {request.user} (Type: {type(request.user)}), Role: {getattr(request.user, 'role', 'N/A')}") # DEBUG
        is_teacher = bool(
            request.user and
            request.user.is_authenticated and
            isinstance(request.user, User) and # Assicura che sia il modello User corretto
            request.user.role == UserRole.TEACHER
        )
        # print(f"[IsTeacherUser] Result: {is_teacher}") # DEBUG
        # Ripristina: restituisce semplicemente il booleano
        return is_teacher

class IsStudentOwnerOrAdmin(permissions.BasePermission):
    """
    Permesso a livello di oggetto per consentire modifiche solo al Docente proprietario
    dello Studente o a un Admin.
    Assume che l'oggetto (obj) abbia un attributo 'teacher'.
    """
    def has_object_permission(self, request, view, obj):
        # I permessi di lettura (GET, HEAD, OPTIONS) potrebbero essere più ampi,
        # ma per ora li limitiamo al proprietario o Admin.
        # SAFE_METHODS sono metodi che non modificano l'oggetto.
        # if request.method in permissions.SAFE_METHODS:
        #     return obj.teacher == request.user or request.user.is_admin

        # I permessi di scrittura (PUT, PATCH, DELETE) sono solo per il proprietario o Admin.
        # Assicurati che request.user sia un User (Admin/Docente)
        is_owner = hasattr(request.user, 'role') and obj.teacher == request.user
        is_admin = hasattr(request.user, 'role') and request.user.role == UserRole.ADMIN
        return is_owner or is_admin

class IsStudent(permissions.BasePermission):
    """
    Permesso per verificare se l'utente autenticato è uno Studente
    (controllando la presenza di request.student impostato da StudentJWTAuthentication).
    Questo implica che l'utente è autenticato tramite un token studente valido.
    """
    def has_permission(self, request, view):
        # Verifica la presenza di request.student impostato da StudentJWTAuthentication
        is_student = hasattr(request, 'student') and request.student is not None
        print(f"[IsStudent] Checking request.student. Result: {is_student}. request.user: {request.user}") # DEBUG
        return is_student

class IsStudentAuthenticated(permissions.BasePermission):
    """
    Permesso per verificare se l'utente è uno Studente autenticato.
    Combina la verifica di IsStudent e la presenza della property is_authenticated.
    """
    def has_permission(self, request, view):
        # request.user sarà l'oggetto Student grazie a StudentJWTAuthentication
        print(f"[IsStudentAuthenticated] Checking permission...") # DEBUG
        print(f"[IsStudentAuthenticated] request.user: {request.user} (Type: {type(request.user)})") # DEBUG
        print(f"[IsStudentAuthenticated] request.auth: {getattr(request, 'auth', 'N/A')}") # DEBUG
        is_student_instance = isinstance(request.user, Student)
        has_auth_prop = hasattr(request.user, 'is_authenticated')
        is_auth_val = getattr(request.user, 'is_authenticated', False) if has_auth_prop else False
        print(f"[IsStudentAuthenticated] is_student_instance: {is_student_instance}") # DEBUG
        print(f"[IsStudentAuthenticated] has_auth_prop: {has_auth_prop}") # DEBUG
        print(f"[IsStudentAuthenticated] is_auth_val: {is_auth_val}") # DEBUG

        result = (
            is_student_instance and
            has_auth_prop and
            is_auth_val
        )
        print(f"[IsStudentAuthenticated] Result: {result}") # DEBUG
        return result

# Potremmo aggiungere altri permessi qui, come IsReadOnly, etc.