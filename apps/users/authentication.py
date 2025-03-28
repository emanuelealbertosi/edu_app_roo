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
        print(f"[StudentAuth] Token validato: {validated_token}") # DEBUG

        # Controlla i claim custom per lo studente
        is_student = validated_token.get('is_student', False)
        student_id = validated_token.get('student_id')

        if is_student and student_id:
            # È un token studente, proviamo ad autenticarlo
            print(f"[StudentAuth] Student token identified. student_id: {student_id}") # DEBUG
            try:
                student = Student.objects.get(pk=student_id, is_active=True)
            except Student.DoesNotExist:
                print(f"[StudentAuth] Studente non trovato o non attivo (ID: {student_id}).") # DEBUG
                raise AuthenticationFailed('Studente non trovato o non attivo.')
            except Exception as e:
                 print(f"[StudentAuth] ERRORE durante recupero studente: {e}") # DEBUG
                 raise AuthenticationFailed('Errore interno autenticazione studente.')

            # Autenticazione studente riuscita, imposta request.student
            request.student = student
            print(f"[StudentAuth] Autenticazione studente {student.pk} riuscita. Impostato request.student. Restituisce (student, token).") # DEBUG
            # Restituiamo lo studente come 'user' per questa richiesta.
            return (student, validated_token)
        else:
            # Non è un token studente (mancano claim o sono false).
            # Restituiamo il risultato originale di super().authenticate()
            # per permettere al prossimo backend (JWTAuthentication standard) di provare.
            print("[StudentAuth] Non è un token studente valido, passa al prossimo backend.") # DEBUG
            return auth_result

    # Non è necessario sovrascrivere get_user qui perché il backend StudentCodeBackend
    # già gestisce il recupero dello Studente tramite ID.