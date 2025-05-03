import uuid
from datetime import date, timedelta
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.rewards.models import Wallet # Importa Wallet
from apps.student_groups.models import StudentGroup, StudentGroupMembership # Importa modelli gruppi
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from .models import User, Student, UserRole, RegistrationToken
from .emails import send_parental_consent_email # Importa la funzione email
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken
from django.utils.translation import gettext_lazy as _

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
            'can_create_public_groups', # Aggiunto per frontend
            # Escludiamo password e altri campi sensibili/gestionali
            # 'password', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'last_login'
        ]
        read_only_fields = ['date_joined', 'role_display', 'can_create_public_groups'] # Aggiunto ai read_only

    # Potremmo aggiungere validazione specifica qui se necessario


class UserCreateSerializer(serializers.ModelSerializer):
    """ Serializer specifico per la creazione di User (Admin/Docente) con gestione password. """
    # Rende la password scrivibile solo durante la creazione
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    role = serializers.ChoiceField(choices=UserRole.choices, required=True) # Rende il ruolo obbligatorio alla creazione
    accept_privacy_policy = serializers.BooleanField(
        write_only=True,
        required=True,
        help_text=_("Indicates whether the user accepts the Privacy Policy.")
    )
    accept_terms_of_service = serializers.BooleanField(
        write_only=True,
        required=True,
        help_text=_("Indicates whether the user accepts the Terms of Service.")
    )

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

    def validate(self, attrs):
        """ Validate that both policy and terms are accepted. """
        if not attrs.get('accept_privacy_policy'):
            raise serializers.ValidationError({"accept_privacy_policy": _("You must accept the Privacy Policy to register.")})
        if not attrs.get('accept_terms_of_service'):
            raise serializers.ValidationError({"accept_terms_of_service": _("You must accept the Terms of Service to register.")})
        return attrs

    def create(self, validated_data):
        """ Crea l'utente, imposta la password hashata e registra l'accettazione delle policy. """
        # Rimuovi i campi booleani prima di passarli a create_user
        accept_privacy = validated_data.pop('accept_privacy_policy', False)
        accept_terms = validated_data.pop('accept_terms_of_service', False)

        user = User.objects.create_user(**validated_data)
        # create_user gestisce automaticamente l'hashing della password

        # Imposta i timestamp di accettazione delle policy
        now = timezone.now()
        update_fields = []
        if accept_privacy:
            user.privacy_policy_accepted_at = now
            update_fields.append('privacy_policy_accepted_at')
        if accept_terms:
            user.terms_of_service_accepted_at = now
            update_fields.append('terms_of_service_accepted_at')

        if update_fields:
            user.save(update_fields=update_fields)

        return user


class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer per il modello Student.
    Usato principalmente dai Docenti per gestire i propri studenti.
    """
    # Il campo 'teacher' è stato rimosso dal modello Student.
    # La relazione avviene tramite gruppi.

    class Meta:
        model = Student
        fields = [
            'id',
            # 'teacher' rimosso
            # 'teacher_username' rimosso
            'first_name',
            'last_name',
            'student_code', # Assicurati che questo campo esista nel modello Student
            'is_active',
            'created_at',
            'full_name', # Proprietà del modello (sola lettura)
        ]
        # Rimuovi 'teacher' e 'teacher_username' dai read_only_fields
        read_only_fields = ['created_at', 'full_name']

    # La validazione del teacher non è più necessaria
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
    di uno studente tramite un token, includendo la verifica dell'età.
    """
    token = serializers.UUIDField(required=True)
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    date_of_birth = serializers.DateField(
        required=True,
        help_text=_("Student's date of birth for age verification.")
    )
    parent_email = serializers.EmailField(
        required=False, # Obbligatorio solo se minorenne, validato in validate()
        allow_blank=True,
        help_text=_("Parent/Guardian email, required if student is under 14.")
    )
    pin = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=4, # Assicura una lunghezza minima per il PIN
        validators=[lambda value: value.isdigit() or serializers.ValidationError(_("PIN must be numeric."))]
    )
    accept_privacy_policy = serializers.BooleanField(
        write_only=True,
        required=True,
        help_text=_("Indicates whether the student accepts the Privacy Policy.")
    )
    accept_terms_of_service = serializers.BooleanField(
        write_only=True,
        required=True,
        help_text=_("Indicates whether the student accepts the Terms of Service.")
    )

    # Età minima per il consenso (potrebbe venire da settings)
    MIN_CONSENT_AGE = 14

    def _calculate_age(self, born):
        """Helper function to calculate age."""
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    def validate(self, attrs):
        """ Validate policies, terms, and age/parent email requirements. """
        if not attrs.get('accept_privacy_policy'):
            raise serializers.ValidationError({"accept_privacy_policy": _("You must accept the Privacy Policy to register.")})
        if not attrs.get('accept_terms_of_service'):
            raise serializers.ValidationError({"accept_terms_of_service": _("You must accept the Terms of Service to register.")})

        # Verifica età e email genitore
        dob = attrs.get('date_of_birth')
        if not dob:
            # Questo non dovrebbe accadere se required=True, ma per sicurezza
            raise serializers.ValidationError({"date_of_birth": _("Date of birth is required.")})

        age = self._calculate_age(dob)
        if age < self.MIN_CONSENT_AGE:
            parent_email = attrs.get('parent_email')
            if not parent_email:
                raise serializers.ValidationError({"parent_email": _("Parent/Guardian email is required for users under {age}.").format(age=self.MIN_CONSENT_AGE)})
        elif 'parent_email' in attrs and not attrs.get('parent_email'):
            # Se l'utente ha >= 14 anni, ma il campo parent_email è stato inviato vuoto, rimuovilo
            # per evitare di salvarlo involontariamente nel DB se il campo non è blank=True nel modello.
            # (Nel nostro caso è blank=True, ma è buona pratica).
            del attrs['parent_email']


        return attrs

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
        Gestisce la verifica dell'età e il flusso di consenso parentale.
        """
        token_instance = self.context['token_instance']
        teacher = token_instance.teacher
        source_group = token_instance.source_group # Ottieni il gruppo di origine (può essere None)
        now = timezone.now()

        # Genera un codice studente univoco (esempio semplice, potrebbe essere migliorato)
        base_code = f"{validated_data['first_name'][:2]}{validated_data['last_name'][:2]}".lower()
        unique_code = base_code
        counter = 1
        while Student.objects.filter(student_code=unique_code).exists():
            unique_code = f"{base_code}{counter}"
            counter += 1

        # Dati base studente
        student_data = {
            # 'teacher': teacher, # Rimosso dal modello Student
            'first_name': validated_data['first_name'],
            'last_name': validated_data['last_name'],
            'student_code': unique_code,
            'date_of_birth': validated_data['date_of_birth'],
            'privacy_policy_accepted_at': now if validated_data.get('accept_privacy_policy') else None,
            'terms_of_service_accepted_at': now if validated_data.get('accept_terms_of_service') else None,
        }

        # Verifica età e imposta stato iniziale
        age = self._calculate_age(validated_data['date_of_birth'])
        if age < self.MIN_CONSENT_AGE:
            student_data['is_active'] = False # Account inattivo finché non c'è consenso
            student_data['parental_consent_status'] = 'PENDING'
            student_data['parent_email'] = validated_data.get('parent_email') # Già validato che ci sia
            student_data['parental_consent_verification_token'] = uuid.uuid4()
            # Imposta scadenza token (es. 7 giorni, potrebbe venire da settings)
            expiry_days = getattr(settings, 'PARENTAL_CONSENT_TOKEN_EXPIRY_DAYS', 7)
            student_data['parental_consent_token_expires_at'] = now + timedelta(days=expiry_days)
            student_data['parental_consent_requested_at'] = now
        else:
            student_data['is_active'] = True # Attivo di default
            student_data['parental_consent_status'] = 'NOT_REQUIRED'
            # Non impostare altri campi relativi al consenso parentale

        # Crea lo studente
        student = Student(**student_data)
        student.set_pin(validated_data['pin']) # Imposta l'hash del PIN
        student.save()

        # Innesca l'invio dell'email di verifica al genitore se necessario
        if student.parental_consent_status == 'PENDING':
            send_parental_consent_email(student)


        # Il Wallet viene creato automaticamente dal segnale post_save di Student

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
# --- Serializer per Registrazione Studente tramite Token Gruppo ---

class GroupTokenRegistrationSerializer(serializers.Serializer):
    """
    Serializer per validare i dati inviati durante la registrazione
    di uno studente tramite un token di gruppo, includendo la verifica dell'età.
    """
    token = serializers.CharField(required=True) # Il token del gruppo è una stringa
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    date_of_birth = serializers.DateField(
        required=True,
        help_text=_("Student's date of birth for age verification.")
    )
    parent_email = serializers.EmailField(
        required=False, # Obbligatorio solo se minorenne, validato in validate()
        allow_blank=True,
        help_text=_("Parent/Guardian email, required if student is under 14.")
    )
    pin = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=4,
        validators=[lambda value: value.isdigit() or serializers.ValidationError(_("PIN must be numeric."))]
    )
    accept_privacy_policy = serializers.BooleanField(
        write_only=True,
        required=True,
        help_text=_("Indicates whether the student accepts the Privacy Policy.")
    )
    accept_terms_of_service = serializers.BooleanField(
        write_only=True,
        required=True,
        help_text=_("Indicates whether the student accepts the Terms of Service.")
    )

    # Età minima per il consenso (potrebbe venire da settings)
    MIN_CONSENT_AGE = 14

    def _calculate_age(self, born):
        """Helper function to calculate age."""
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    def validate(self, attrs):
        """ Validate policies, terms, and age/parent email requirements. """
        if not attrs.get('accept_privacy_policy'):
            raise serializers.ValidationError({"accept_privacy_policy": _("You must accept the Privacy Policy to register.")})
        if not attrs.get('accept_terms_of_service'):
            raise serializers.ValidationError({"accept_terms_of_service": _("You must accept the Terms of Service to register.")})

        # Verifica età e email genitore
        dob = attrs.get('date_of_birth')
        if not dob:
            raise serializers.ValidationError({"date_of_birth": _("Date of birth is required.")})

        age = self._calculate_age(dob)
        if age < self.MIN_CONSENT_AGE:
            parent_email = attrs.get('parent_email')
            if not parent_email:
                raise serializers.ValidationError({"parent_email": _("Parent/Guardian email is required for users under {age}.").format(age=self.MIN_CONSENT_AGE)})
        elif 'parent_email' in attrs and not attrs.get('parent_email'):
             del attrs['parent_email']

        return attrs

    def validate_token(self, value):
        """
        Verifica che il token del gruppo esista, sia associato a un gruppo attivo
        e a un docente attivo.
        """
        try:
            # Usiamo select_related per ottimizzare l'accesso al docente
            group = StudentGroup.objects.select_related('owner').get(registration_token=value)
        except StudentGroup.DoesNotExist:
            raise serializers.ValidationError("Token di registrazione del gruppo non valido o inesistente.")

        if not group.is_active:
             raise serializers.ValidationError("Il gruppo associato a questo token non è più attivo.")

        if not group.owner.is_active:
             raise serializers.ValidationError("Il docente associato a questo gruppo non è più attivo.")

        # Passa l'istanza del gruppo al contesto per usarla nel metodo create
        self.context['group_instance'] = group
        return value

    def create(self, validated_data):
        """
        Crea il nuovo studente, lo associa al docente del gruppo,
        imposta il PIN, crea il Wallet (tramite segnale) e crea la membership nel gruppo.
        Gestisce la verifica dell'età e il flusso di consenso parentale.
        """
        group_instance = self.context['group_instance']
        teacher = group_instance.owner # Docente proprietario del gruppo
        now = timezone.now()

        # Genera un codice studente univoco
        base_code = f"{validated_data['first_name'][:2]}{validated_data['last_name'][:2]}".lower()
        unique_code = base_code
        counter = 1
        while Student.objects.filter(student_code=unique_code).exists():
            unique_code = f"{base_code}{counter}"
            counter += 1

        # Dati base studente
        student_data = {
            'first_name': validated_data['first_name'],
            'last_name': validated_data['last_name'],
            'student_code': unique_code,
            'date_of_birth': validated_data['date_of_birth'],
            'privacy_policy_accepted_at': now if validated_data.get('accept_privacy_policy') else None,
            'terms_of_service_accepted_at': now if validated_data.get('accept_terms_of_service') else None,
        }

        # Verifica età e imposta stato iniziale
        age = self._calculate_age(validated_data['date_of_birth'])
        if age < self.MIN_CONSENT_AGE:
            student_data['is_active'] = False # Account inattivo finché non c'è consenso
            student_data['parental_consent_status'] = 'PENDING'
            student_data['parent_email'] = validated_data.get('parent_email') # Già validato che ci sia
            student_data['parental_consent_verification_token'] = uuid.uuid4()
            expiry_days = getattr(settings, 'PARENTAL_CONSENT_TOKEN_EXPIRY_DAYS', 7)
            student_data['parental_consent_token_expires_at'] = now + timedelta(days=expiry_days)
            student_data['parental_consent_requested_at'] = now
        else:
            student_data['is_active'] = True # Attivo di default
            student_data['parental_consent_status'] = 'NOT_REQUIRED'

        # Crea lo studente
        student = Student(**student_data)
        student.set_pin(validated_data['pin']) # Imposta l'hash del PIN
        student.save()

        # Innesca l'invio dell'email di verifica al genitore se necessario
        if student.parental_consent_status == 'PENDING':
            send_parental_consent_email(student)

        # Il Wallet viene creato automaticamente dal segnale post_save di Student

        # Crea la membership nel gruppo
        try:
            StudentGroupMembership.objects.create(group=group_instance, student=student)
        except Exception as e:
            # Logga l'errore ma non interrompere la registrazione.
            # Potrebbe fallire se c'è un vincolo UNIQUE violato (improbabile qui)
            # o altri problemi. Considerare get_or_create se necessario.
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Errore durante la creazione della membership per studente {student.id} nel gruppo {group_instance.id} (token: {group_instance.registration_token}): {e}", exc_info=True)
            # Potremmo voler sollevare un'eccezione qui se l'aggiunta al gruppo è critica
            # raise serializers.ValidationError("Impossibile aggiungere lo studente al gruppo.")

        # Non c'è un token da marcare come "usato" come nel caso del RegistrationToken individuale.
        # Il token del gruppo rimane valido per altre registrazioni.

        return student # Restituisce l'istanza dello studente creato
# --- Serializer per Rettifica Profilo Studente (GDPR) ---

class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer specifico per permettere allo studente di aggiornare
    i propri dati personali consentiti (nome, cognome).
    Usato per la rettifica GDPR.
    """
    class Meta:
        model = Student
        fields = [
            'first_name',
            'last_name',
        ]
        # Non ci sono campi read_only qui, questi sono i soli campi modificabili.

    # Aggiungere validazione se necessario (es. lunghezza minima/massima)
    def validate_first_name(self, value):
        if not value:
            raise serializers.ValidationError("Il nome non può essere vuoto.")
        # Aggiungere altre validazioni se serve
        return value

    def validate_last_name(self, value):
        if not value:
            raise serializers.ValidationError("Il cognome non può essere vuoto.")
        # Aggiungere altre validazioni se serve
        return value