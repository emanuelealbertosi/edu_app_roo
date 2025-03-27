from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from .models import Student

class StudentJWTAuthentication(JWTAuthentication):
    """
    Classe di autenticazione JWT personalizzata per gli studenti.
    Verifica la presenza del claim 'is_student' e 'student_id' nel token
    e associa l'oggetto Student corrispondente a request.student.
    """

    def authenticate(self, request):
        # Esegue l'autenticazione JWT standard
        auth_result = super().authenticate(request)

        if auth_result is None:
            # Nessun token valido trovato o utente non autenticato (potrebbe essere User standard)
            return None

        # L'autenticazione standard JWT restituisce (user, validated_token)
        # 'user' qui è un SimpleLazyObject basato su AUTH_USER_MODEL, che non ci serve direttamente.
        _user, validated_token = auth_result

        # Controlla i claim custom per lo studente
        is_student = validated_token.get('is_student', False)
        student_id = validated_token.get('student_id')

        if not is_student or not student_id:
            # Se non è un token studente valido, consideriamo l'autenticazione fallita *per questo backend*
            # Un altro backend (es. JWTAuthentication standard per User) potrebbe ancora funzionare.
            # Sollevare AuthenticationFailed qui impedirebbe ad altri backend di essere provati.
            # Restituire None permette ad altri backend di tentare.
            # Tuttavia, se vogliamo che SOLO questo backend gestisca i token con 'is_student',
            # potremmo sollevare AuthenticationFailed. Decidiamo di restituire None per ora.
            # raise AuthenticationFailed('Token non valido per lo studente.')
            return None

        try:
            # Recupera l'oggetto Studente dal DB usando l'ID nel token
            student = Student.objects.get(pk=student_id, is_active=True)
        except Student.DoesNotExist:
            raise AuthenticationFailed('Studente non trovato o non attivo.')

        # Associa l'oggetto studente alla request per un facile accesso nelle view/permessi
        request.student = student

        # Restituisce la tupla (user, token) come richiesto da DRF.
        # Usiamo lo studente come 'user' in questo contesto, anche se non è AUTH_USER_MODEL.
        # Questo potrebbe avere implicazioni se si usano permessi DRF standard basati su request.user.
        # Un'alternativa è restituire (_user, validated_token) e usare sempre request.student.
        # Scegliamo di restituire lo studente come primo elemento per coerenza con get_user.
        return (student, validated_token)

    # Non è necessario sovrascrivere get_user qui perché il backend StudentCodeBackend
    # già gestisce il recupero dello Studente tramite ID.