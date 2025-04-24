from rest_framework import permissions
# Assumiamo che i ruoli siano definiti nel modello User o in un profilo collegato
# Potrebbe essere necessario importare il modello User: from apps.users.models import User
# O usare settings.AUTH_USER_MODEL e accedere ai ruoli/profili da lì.

class IsAdminOrTeacher(permissions.BasePermission):
    """
    Permesso per consentire l'accesso solo agli Admin o ai Docenti.
    """
    def has_permission(self, request, view):
        # Assicurati che l'utente sia autenticato
        if not request.user or not request.user.is_authenticated:
            return False
        # Controlla se l'utente ha il ruolo 'Admin' o 'Docente'
        # Questo presuppone che il modello User abbia un campo 'role'
        # o un metodo/proprietà per verificarlo. Adattare se necessario.
        # Confronto case-insensitive
        return request.user.role.upper() in ['ADMIN', 'DOCENTE', 'TEACHER']

class IsTeacherOwner(permissions.BasePermission):
    """
    Permesso per consentire l'accesso solo al Docente che ha creato l'oggetto.
    Assicura anche che l'utente sia un Docente.
    """
    def has_object_permission(self, request, view, obj):
        # L'utente deve essere un Docente o Teacher
        if not request.user or not request.user.is_authenticated or request.user.role.upper() not in ['DOCENTE', 'TEACHER']:
            return False

        # Controlla se l'oggetto è un LessonContent o simile che ha una lezione padre
        if hasattr(obj, 'lesson'):
            # Controlla se l'utente è il creatore della lezione padre
            # Assicurati che obj.lesson.creator esista e sia confrontabile con request.user
            try:
                return obj.lesson.creator == request.user
            except AttributeError:
                 # Se obj.lesson o obj.lesson.creator non esistono, nega il permesso
                 return False
        # Altrimenti, assumi che l'oggetto sia la Lezione stessa (o altro oggetto con 'creator')
        elif hasattr(obj, 'creator'):
            return obj.creator == request.user
        else:
            # Se l'oggetto non ha né 'lesson' né 'creator', non possiamo verificare la proprietà
            return False

class IsAdminOrTeacherOwner(permissions.BasePermission):
    """
    Permesso per consentire l'accesso agli Admin o al Docente creatore.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin ha sempre accesso
        user_role = getattr(request.user, 'role', None)
        if user_role and user_role.upper() == 'ADMIN':
            return True

        # Il Docente ha accesso solo se è il creatore (della lezione o del contenuto tramite la lezione)
        if user_role and user_role.upper() in ['DOCENTE', 'TEACHER']:
            # Controlla se l'oggetto è un LessonContent o simile
            if hasattr(obj, 'lesson'):
                try:
                    return obj.lesson.creator == request.user
                except AttributeError:
                    return False
            # Altrimenti, assumi che l'oggetto sia la Lezione stessa (o altro oggetto con 'creator')
            elif hasattr(obj, 'creator'):
                return obj.creator == request.user
            else:
                return False # Non può verificare la proprietà

        # Altri ruoli o utenti non autenticati non hanno accesso
        return False

class IsAssignedStudentOrTeacherOwner(permissions.BasePermission):
    """
    Permesso per consentire l'accesso al Docente creatore della Lezione
    o allo Studente a cui la Lezione è stata assegnata.
    Usato principalmente per la visualizzazione di Lesson e LessonContent.
    """
    def has_object_permission(self, request, view, obj):
        # obj qui può essere Lesson, LessonContent, o LessonAssignment
        if not request.user or not request.user.is_authenticated:
            return False

        lesson = None
        if hasattr(obj, 'lesson'): # Se obj è LessonContent o LessonAssignment
            lesson = obj.lesson
        elif hasattr(obj, 'title'): # Se obj è Lesson stessa
            lesson = obj
        else:
            return False # Oggetto non supportato

        # Determina il tipo di utente in modo sicuro
        user_role = getattr(request.user, 'role', None)

        # Caso 1: L'utente è uno Studente (non ha l'attributo 'role')
        if not user_role:
            # Assumiamo che request.user sia l'istanza dello Studente
            # Verificare l'esistenza dell'assegnazione
            try:
                from .models import LessonAssignment
            except ImportError:
                 print("Attenzione: Impossibile importare LessonAssignment in permissions.")
                 return False # Non possiamo verificare, nega accesso

            # Basandoci sui log di StudentAuth, assumiamo che request.user SIA l'istanza Studente.
            try:
                # Verifica se esiste un'assegnazione per questa lezione e questo studente
                return LessonAssignment.objects.filter(lesson=lesson, student=request.user).exists()
            except Exception as e: # Cattura altri errori potenziali (es. field error)
                 print(f"Errore durante la verifica dell'assegnazione studente: {e}")
                 return False # Meglio negare l'accesso se non sicuri

        # Caso 2: L'utente ha un ruolo (Docente/Teacher/Admin?)
        elif user_role.upper() in ['DOCENTE', 'TEACHER']:
             # Verifica se è il creatore della lezione
             return lesson.creator == request.user # Assumendo che lesson.creator sia l'oggetto User

        # Altri ruoli (es. Admin) o casi non gestiti non hanno accesso tramite questo permesso
        return False

# Potrebbero essere necessari altri permessi specifici, ad esempio per l'assegnazione.