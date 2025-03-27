from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model # Per recuperare il modello User standard (Admin/Docente)
from .models import Student

UserModel = get_user_model()

class StudentCodeBackend(BaseBackend):
    """
    Backend di autenticazione che permette il login usando student_code e PIN.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Tenta l'autenticazione usando student_code (passato come 'username') e PIN (passato come 'password').
        Restituisce un oggetto Student se l'autenticazione ha successo, None altrimenti.
        """
        student_code = username # Usiamo il campo 'username' per passare lo student_code
        pin = password

        if not student_code or not pin:
            return None

        try:
            # Cerca lo studente attivo tramite il codice fornito
            student = Student.objects.get(student_code=student_code, is_active=True)
        except Student.DoesNotExist:
            # Esegui un controllo a tempo costante per prevenire timing attacks
            # se si usasse il modello User standard. Qui è meno critico ma buona pratica.
            # UserModel().set_password(pin) # Non necessario qui
            return None

        # Verifica il PIN fornito con l'hash memorizzato
        if student.check_pin(pin):
            # Autenticazione riuscita! Restituiamo l'oggetto Student.
            # Nota: NON restituiamo un oggetto User standard.
            return student
        else:
            return None

    def get_user(self, user_id):
        """
        Recupera un utente (in questo caso, uno Studente) dato il suo ID.
        Questo è richiesto da Django per gestire la sessione/autenticazione.
        """
        try:
            # Dato che authenticate restituisce un oggetto Student, user_id sarà lo student.pk
            return Student.objects.get(pk=user_id)
        except Student.DoesNotExist:
            return None

# Nota: Questo backend gestisce SOLO l'autenticazione degli studenti.
# Per Admin/Docenti, useremo il backend di default di Django (ModelBackend).