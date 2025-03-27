from rest_framework import permissions
from .models import UserRole # Import UserRole if needed for checks

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
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.TEACHER)

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
    """
    def has_permission(self, request, view):
        return hasattr(request, 'student') and request.student is not None

# Potremmo aggiungere altri permessi qui, come IsReadOnly, etc.