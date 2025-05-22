from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied # Importa l'eccezione
from .models import UserRole, User, Student # Import UserRole, User, Student

class IsAdminUser(permissions.BasePermission):
    """
    Permesso personalizzato per consentire l'accesso solo agli utenti Admin.
    """
    def has_permission(self, request, view):
        # Controlla se l'utente è un'istanza di User, autenticato e ha il ruolo ADMIN
        return bool(
            request.user and
            request.user.is_authenticated and
            isinstance(request.user, User) and # Verifica che sia un User
            request.user.role == UserRole.ADMIN
        )

class IsTeacherUser(permissions.BasePermission):
    """
    Permesso personalizzato per consentire l'accesso solo agli utenti Docenti.
    """
    def has_permission(self, request, view):
        # Controlla se l'utente è autenticato e ha il ruolo TEACHER
        # print(f"[IsTeacherUser] Checking user: {request.user} (Type: {type(request.user)}), Role: {getattr(request.user, 'role', 'N/A')}") # DEBUG
        # Controlla se l'utente è un'istanza di User, autenticato e ha il ruolo TEACHER
        is_teacher = bool(
            request.user and
            request.user.is_authenticated and
            isinstance(request.user, User) and # Verifica che sia un User
            request.user.role == UserRole.TEACHER
        )
        # print(f"[IsTeacherUser] Result: {is_teacher}") # DEBUG
        return is_teacher

class IsStudentOwnerOrAdmin(permissions.BasePermission):
    """
    Permesso a livello di oggetto per consentire modifiche solo al Docente proprietario
    dello Studente o a un Admin.
    Assume che l'oggetto (obj) abbia un attributo 'teacher'.
    """
    def has_object_permission(self, request, view, obj):
        # L'utente admin ha sempre il permesso
        if hasattr(request.user, 'role') and request.user.role == UserRole.ADMIN:
            return True

        # Per i metodi di lettura (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            # Un insegnante può visualizzare i dettagli dello studente
            if hasattr(request.user, 'role') and request.user.role == UserRole.TEACHER:
                return True
            # Uno studente può visualizzare i propri dettagli
            # Assumendo che obj sia l'istanza dello studente e request.user sia l'utente studente autenticato
            if isinstance(request.user, Student) and obj == request.user:
                return True
            return False # Altri utenti non autenticati o con ruoli diversi non possono leggere

        # Per i metodi di scrittura (PUT, PATCH, DELETE)
        # Qui la logica di 'owner' è cruciale.
        # Dato che 'obj.teacher' causa AttributeError, questa logica deve essere rivista
        # in base alla reale struttura di ownership/management degli studenti da parte dei docenti.
        # Per ora, per evitare modifiche non autorizzate se la relazione non è diretta 'obj.teacher',
        # si potrebbe limitare la scrittura agli admin o implementare la logica corretta.
        if hasattr(request.user, 'role') and request.user.role == UserRole.TEACHER:
            # Esempio di logica di proprietà se lo studente fosse legato all'insegnante
            # tramite un campo diretto (che attualmente manca o è nominato diversamente):
            # if hasattr(obj, 'managing_teacher') and obj.managing_teacher == request.user:
            #     return True
            # Oppure, se gli studenti sono in classi gestite dall'insegnante:
            # if obj.student_classes.filter(teacher=request.user).exists():
            # return True
            # ATTENZIONE: La riga seguente è un placeholder e probabilmente NON è corretta
            # perché 'obj.teacher' è la causa dell'AttributeError.
            # is_owner_for_write = hasattr(obj, 'teacher') and obj.teacher == request.user
            # Per ora, si disabilita la scrittura per i docenti in questa classe di permesso
            # fino a che la logica di ownership non sia chiarita e implementata correttamente.
            # Questo previene l'AttributeError e comportamenti non definiti per la scrittura.
            return False # Modificare questa riga con la logica di ownership corretta per la scrittura

        return False # Nega il permesso per default per operazioni di scrittura se non admin o proprietario definito

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