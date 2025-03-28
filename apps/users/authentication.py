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
       # print(f"[StudentAuth DEBUG] authenticate() called. Request path: {request.path}")
       header = self.get_header(request)
       if header is None:
           # print("[StudentAuth DEBUG] No Authorization header found.")
           return None # Nessun header, passa al prossimo backend

       raw_token = self.get_raw_token(header)
       if raw_token is None:
           # print("[StudentAuth DEBUG] Could not extract raw token from header.")
           return None # Formato header non valido, passa al prossimo backend

       # print(f"[StudentAuth DEBUG] Raw token extracted: {raw_token[:10]}...") # Mostra solo inizio

       try:
           validated_token = self.get_validated_token(raw_token)
           # print(f"[StudentAuth DEBUG] Token validated successfully. Claims: {validated_token}")
       except InvalidToken as e:
           # print(f"[StudentAuth DEBUG] Token validation failed: {e}")
           # Non sollevare eccezione qui, lascia che il backend standard lo gestisca se necessario
           return None # Token non valido, passa al prossimo backend
       except Exception as e:
           # print(f"[StudentAuth DEBUG] Unexpected error during token validation: {e}")
           return None # Errore generico, passa al prossimo backend


       # Ora controlliamo i claim specifici dello studente NEL token validato
       is_student = validated_token.get('is_student', False)
       student_id = validated_token.get('student_id')

       if is_student and student_id:
           # È un token studente, proviamo a recuperare lo studente
           print(f"[StudentAuth] Student token identified. student_id: {student_id}")
           try:
               student = Student.objects.get(pk=student_id, is_active=True)
           except Student.DoesNotExist:
               print(f"[StudentAuth] Studente non trovato o non attivo (ID: {student_id}).")
               # Se il token è valido ma lo studente non esiste più, consideralo un fallimento
               raise AuthenticationFailed('Studente associato al token non trovato o non attivo.')
           except Exception as e:
                print(f"[StudentAuth] ERRORE durante recupero studente: {e}")
                raise AuthenticationFailed('Errore interno durante recupero studente.')

           # Autenticazione studente riuscita!
           # Impostiamo request.student E restituiamo (student, validated_token)
           # DRF imposterà request.user = student e request.auth = validated_token
           request.student = student # Manteniamo per compatibilità se usato altrove
           print(f"[StudentAuth] Autenticazione studente {student.pk} riuscita. Restituisce (student, token).")
           return (student, validated_token)
       else:
           # Il token è valido ma NON è un token studente (mancano i claim specifici).
           # Restituiamo None per permettere al prossimo backend di autenticazione
           # (JWTAuthentication standard) di provare a gestirlo come token Admin/Docente.
           print("[StudentAuth] Token valido ma non è un token studente (claim mancanti). Passa al prossimo backend.")
           return None

   # get_user non è necessario qui perché authenticate restituisce già l'oggetto utente corretto (Student)