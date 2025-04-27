from rest_framework import serializers
from .models import User, Student, UserRole, RegistrationToken # Aggiungi RegistrationToken
from django.utils import timezone # Aggiungi timezone
from apps.rewards.models import Wallet # Importa Wallet
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer per il modello User (Admin/Docente).
    Usato principalmente per la gestione da parte dell'Admin.
    """
    # Rendiamo il campo role leggibile ma non scrivibile direttamente qui
    # La gestione del ruolo potrebbe avvenire tramite azioni specifiche o permessi.
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        # Campi da esporre/gestire tramite API
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role', # Includiamo il valore grezzo per filtri/logica
            'role_display', # Versione leggibile
            'is_active',
            'date_joined',
            # Escludiamo password e altri campi sensibili/gestionali
            # 'password', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'last_login'
        ]
        read_only_fields = ['date_joined', 'role_display'] # Campi non modificabili tramite questo serializer base

    # Potremmo aggiungere validazione specifica qui se necessario


class UserCreateSerializer(serializers.ModelSerializer):
    """ Serializer specifico per la creazione di User (Admin/Docente) con gestione password. """
    # Rende la password scrivibile solo durante la creazione
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    role = serializers.ChoiceField(choices=UserRole.choices, required=True) # Rende il ruolo obbligatorio alla creazione

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password', # Includi password per la creazione
            'role',     # Includi ruolo per la creazione
            'is_active',
        ]
        # Non ci sono campi read_only specifici per la creazione qui,
        # 'id' è gestito automaticamente.

    def create(self, validated_data):
        """ Crea l'utente e imposta la password hashata. """
        user = User.objects.create_user(**validated_data)
        # create_user gestisce automaticamente l'hashing della password
        return user


class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer per il modello Student.
    Usato principalmente dai Docenti per gestire i propri studenti.
    """
    # Mostriamo il nome completo del docente associato (sola lettura)
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id',
            'teacher', # ID del docente (scrivibile per creare/associare)
            'teacher_username', # Nome utente del docente (sola lettura)
            'first_name',
            'last_name',
            'student_code', # Aggiunto campo mancante
            'is_active',
            'created_at',
            'full_name', # Proprietà del modello (sola lettura)
        ]
        # Teacher è impostato automaticamente nella view per i docenti, quindi read_only qui.
        # Per gli admin che creano studenti, dovranno usare un serializer diverso o un endpoint specifico?
        # Per ora, lo rendiamo read_only e la view gestisce l'impostazione.
        read_only_fields = ['teacher', 'created_at', 'teacher_username', 'full_name']

    # La validazione del teacher non è più necessaria qui se il campo è read_only
    # def validate_teacher(self, value):
    #     """
    #     Assicura che l'utente fornito come 'teacher' sia effettivamente un Docente.
    #     """
    #     if not value.is_teacher:
    #         raise serializers.ValidationError("L'utente selezionato non è un Docente.")
    #     return value

    # Potremmo aggiungere un metodo create o update per gestire logica specifica,
    # ad esempio assicurarsi che il docente che crea lo studente sia l'utente autenticato.
    # Questo di solito viene gestito nella ViewSet.


class StudentBasicSerializer(serializers.ModelSerializer):
    """ Serializer minimale per lo studente, usato per rappresentazioni annidate. """
    class Meta:
        model = Student
        fields = ['id', 'student_code', 'first_name', 'last_name', 'full_name']
        read_only_fields = fields # Sola lettura in questo contesto


# --- Serializer per Sommario Progressi Studente ---

class StudentProgressSummarySerializer(serializers.Serializer):
    """
    Serializer per visualizzare un sommario dei progressi di uno studente.
    Non è un ModelSerializer perché aggrega dati.
    """
    student_id = serializers.IntegerField(read_only=True, source='id') # ID dello studente
    full_name = serializers.CharField(read_only=True)
    student_code = serializers.CharField(read_only=True) # Sostituito username con student_code
    # Campi aggregati (verranno calcolati nella view con annotazioni)
    completed_quizzes_count = serializers.IntegerField(read_only=True, default=0)
    completed_pathways_count = serializers.IntegerField(read_only=True, default=0)
    total_points_earned = serializers.IntegerField(read_only=True, default=0) # Punti totali dal wallet
    # Potremmo aggiungere altri campi aggregati se necessario
    # last_activity_at = serializers.DateTimeField(read_only=True, allow_null=True)

    # Nota: La view che usa questo serializer dovrà fornire un queryset
    # annotato con i campi aggregati (completed_quizzes_count, etc.).


# --- Serializer per Token di Registrazione ---

class RegistrationTokenSerializer(serializers.ModelSerializer):
    """
    Serializer per visualizzare i token di registrazione generati dai docenti.
    Include il link di registrazione completo.
    """
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    registration_link = serializers.CharField(read_only=True) # Proprietà del modello
    is_valid = serializers.BooleanField(read_only=True) # Proprietà del modello

    class Meta:
        model = RegistrationToken
        fields = [
            'token',
            'teacher',
            'teacher_username',
            'created_at',
            'expires_at',
            'used_at',
            'student', # ID dello studente registrato (se presente)
            'is_valid',
            'registration_link',
        ]
        read_only_fields = fields # Questo serializer è solo per la lettura


class StudentRegistrationSerializer(serializers.Serializer):
    """
    Serializer per validare i dati inviati durante la registrazione
    di uno studente tramite un token.
    """
    token = serializers.UUIDField(required=True)
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    # Il codice studente verrà generato automaticamente
    pin = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=4, # Assicura una lunghezza minima per il PIN
        validators=[lambda value: value.isdigit() or serializers.ValidationError("Il PIN deve essere numerico.")]
    )

    def validate_token(self, value):
        """
        Verifica che il token esista, sia valido (non scaduto, non usato)
        e appartenga a un docente attivo.
        """
        try:
            token_instance = RegistrationToken.objects.select_related('teacher').get(token=value)
        except RegistrationToken.DoesNotExist:
            raise serializers.ValidationError("Token di registrazione non valido o inesistente.")

        if not token_instance.is_valid:
            if token_instance.used_at:
                raise serializers.ValidationError("Questo token di registrazione è già stato utilizzato.")
            elif timezone.now() >= token_instance.expires_at:
                raise serializers.ValidationError("Questo token di registrazione è scaduto.")
            else: # Caso generico (dovrebbe essere coperto sopra)
                 raise serializers.ValidationError("Token di registrazione non valido.")

        if not token_instance.teacher.is_active:
             raise serializers.ValidationError("Il docente associato a questo token non è più attivo.")

        # Passa l'istanza del token al contesto per usarla nel metodo create
        self.context['token_instance'] = token_instance
        return value

    def create(self, validated_data):
        """
        Crea il nuovo studente, lo associa al docente del token,
        imposta il PIN, crea il Wallet, marca il token come usato
        e aggiunge lo studente al gruppo di origine del token (se presente).
        """
        token_instance = self.context['token_instance']
        teacher = token_instance.teacher
        source_group = token_instance.source_group # Ottieni il gruppo di origine (può essere None)

        # Genera un codice studente univoco (esempio semplice, potrebbe essere migliorato)
        base_code = f"{validated_data['first_name'][:2]}{validated_data['last_name'][:2]}".lower()
        unique_code = base_code
        counter = 1
        while Student.objects.filter(student_code=unique_code).exists():
            unique_code = f"{base_code}{counter}"
            counter += 1

        # Crea lo studente
        student = Student(
            teacher=teacher,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            student_code=unique_code,
            is_active=True # Attivo di default
        )
        student.set_pin(validated_data['pin']) # Imposta l'hash del PIN
        student.save()

        # Non creare il Wallet qui, viene creato automaticamente dal segnale post_save
        # Wallet.objects.create(student=student)

        # Aggiungi lo studente al gruppo di origine, se specificato nel token
        if source_group:
            from apps.student_groups.models import StudentGroupMembership # Importa qui per evitare dipendenze circolari
            try:
                StudentGroupMembership.objects.create(group=source_group, student=student)
                # Log o gestione successo opzionale
            except Exception as e:
                # Logga l'errore ma non interrompere la registrazione
                # Potrebbe accadere se lo studente è già nel gruppo per qualche motivo? (get_or_create sarebbe più sicuro)
                # O se ci sono altri vincoli.
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Errore durante l'aggiunta automatica dello studente {student.id} al gruppo {source_group.id} dopo registrazione con token {token_instance.token}: {e}", exc_info=True)


        # Marca il token come usato
        token_instance.used_at = timezone.now()
        token_instance.student = student
        token_instance.save(update_fields=['used_at', 'student'])

        return student # Restituisce l'istanza dello studente creato


# --- Serializer per Refresh Token Studente ---

class StudentTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Serializer personalizzato per il refresh del token JWT per gli Studenti.
    Valida il refresh token cercando lo studente tramite 'student_id' nel payload.
    """
    def validate(self, attrs):
        # Il metodo validate di TokenRefreshSerializer gestisce già la decodifica
        # e la validazione base del refresh token (scadenza, blacklist se attiva).
        # Noi dobbiamo solo assicurarci che l'utente associato (in questo caso, lo studente) esista.
        data = super().validate(attrs) # Questo popola self.token

        # Il token decodificato è in self.token dopo la validazione base
        if not self.token:
             # Questo non dovrebbe accadere se super().validate() non ha sollevato eccezioni,
             # ma è una sicurezza aggiuntiva.
             raise InvalidToken('Token non valido o non trovato dopo la validazione base.')

        student_id = self.token.get('student_id') # Estrai il claim custom

        if not student_id:
            raise InvalidToken('Token non contiene l\'ID studente richiesto.')

        try:
            # Verifica che lo studente esista e sia attivo
            student = Student.objects.get(pk=student_id, is_active=True)
        except Student.DoesNotExist:
            raise InvalidToken('Studente associato al token non trovato o non attivo.')

        # Se tutto ok, restituisci i dati validati (che includono il nuovo access token generato da super().validate)
        # Non è necessario aggiungere lo studente qui, serve solo per la validazione.
        return data