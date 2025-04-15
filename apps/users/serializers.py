from rest_framework import serializers
from django.conf import settings # Aggiunto import per accedere alle impostazioni Django
from .models import User, Student, UserRole, StudentGroup, StudentRegistrationToken # Aggiunto StudentRegistrationToken
import random
import string
import uuid # Per generare parti casuali del codice studente
from django.utils import timezone # Per validazione token

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer per il modello User (Admin/Docente).
    Usato principalmente per la gestione da parte dell'Admin.
    """
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'is_active', 'date_joined',
        ]
        read_only_fields = ['date_joined', 'role_display']


class UserCreateSerializer(serializers.ModelSerializer):
    """ Serializer specifico per la creazione di User (Admin/Docente) con gestione password. """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    role = serializers.ChoiceField(choices=UserRole.choices, required=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'role', 'is_active',
        ]

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class StudentGroupSerializer(serializers.ModelSerializer):
    """
    Serializer per il modello StudentGroup.
    Permette ai docenti di creare e gestire i propri gruppi.
    """
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    member_count = serializers.IntegerField(source='members.count', read_only=True)

    class Meta:
        model = StudentGroup
        fields = [
            'id', 'name', 'teacher', 'teacher_username',
            'member_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'teacher', 'teacher_username', 'member_count', 'created_at', 'updated_at']

    def create(self, validated_data):
        teacher = self.context['request'].user
        if not teacher.is_teacher:
            raise serializers.ValidationError("Solo i docenti possono creare gruppi.")
        group = StudentGroup.objects.create(teacher=teacher, **validated_data)
        return group

    def update(self, instance, validated_data):
        validated_data.pop('teacher', None)
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance


class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer per il modello Student.
    Usato principalmente dai Docenti per gestire i propri studenti.
    Include ora il gruppo dello studente.
    """
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(
        source='group', queryset=StudentGroup.objects.all(),
        allow_null=True, required=False, write_only=True
    )
    group_name = serializers.CharField(source='group.name', read_only=True, allow_null=True)

    class Meta:
        model = Student
        fields = [
            'id', 'teacher', 'teacher_username', 'first_name', 'last_name',
            'student_code', 'group_id', 'group_name', 'is_active',
            'created_at', 'full_name',
        ]
        read_only_fields = ['teacher', 'created_at', 'teacher_username', 'full_name', 'group_name'] # Rimosso 'student_code'

    def validate_group_id(self, group):
        teacher = self.context['request'].user
        if group and group.teacher != teacher:
            raise serializers.ValidationError(f"Il gruppo '{group.name}' non appartiene a questo docente.")
        return group


# --- Serializer per Creazione Studente da Docente ---

def generate_unique_student_code(first_name, last_name):
    fn_part = first_name[:2].lower() if first_name else 'xx'
    ln_part = last_name[:3].lower() if last_name else 'xxx'
    base_code = f"{fn_part}{ln_part}"
    while True:
        random_part = uuid.uuid4().hex[:4]
        code = f"{base_code}-{random_part}"
        if not Student.objects.filter(student_code=code).exists():
            return code

def generate_random_pin(length=6):
    return ''.join(random.choices(string.digits, k=length))


class TeacherStudentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer per permettere ai docenti di creare studenti.
    Genera automaticamente student_code e PIN.
    Permette l'assegnazione opzionale a un gruppo esistente del docente.
    Restituisce il PIN generato in chiaro *solo* nella risposta alla creazione.
    """
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=StudentGroup.objects.all(), source='group',
        allow_null=True, required=False,
        help_text="ID del gruppo a cui assegnare lo studente (opzionale)."
    )
    student_code = serializers.CharField(read_only=True)
    pin = serializers.CharField(read_only=True, help_text="PIN generato (visibile solo alla creazione)")
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True, allow_null=True)

    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'group_id', 'student_code', 'pin',
            'teacher', 'teacher_username', 'group_name', 'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'student_code', 'pin', 'teacher', 'teacher_username', 'group_name', 'is_active', 'created_at']

    def validate_group_id(self, group):
        teacher = self.context['request'].user
        if group and group.teacher != teacher:
            raise serializers.ValidationError(f"Il gruppo '{group.name}' non appartiene a questo docente.")
        return group

    def create(self, validated_data):
        teacher = self.context['request'].user
        if not teacher.is_teacher:
             raise serializers.ValidationError("Solo i docenti possono creare studenti.")
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        group = validated_data.get('group')
        student_code = generate_unique_student_code(first_name, last_name)
        raw_pin = generate_random_pin()
        student = Student(
            teacher=teacher, first_name=first_name, last_name=last_name,
            student_code=student_code, group=group
        )
        try:
            student.set_pin(raw_pin)
        except ValueError as e:
            raise serializers.ValidationError(f"Errore nella generazione del PIN: {e}")
        student.save()
        student.pin = raw_pin
        return student


# --- Serializer per Sommario Progressi Studente ---

class StudentProgressSummarySerializer(serializers.Serializer):
    """
    Serializer per visualizzare un sommario dei progressi di uno studente.
    Non è un ModelSerializer perché aggrega dati.
    """
    student_id = serializers.IntegerField(read_only=True, source='id')
    full_name = serializers.CharField(read_only=True)
    student_code = serializers.CharField(read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True, allow_null=True)
    completed_quizzes_count = serializers.IntegerField(read_only=True, default=0)
    completed_pathways_count = serializers.IntegerField(read_only=True, default=0)
    total_points_earned = serializers.IntegerField(read_only=True, default=0)
    average_quiz_score = serializers.FloatField(read_only=True, default=0.0)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        avg_score = getattr(instance, 'average_quiz_score', None)
        if avg_score is not None:
            try:
                representation['average_quiz_score'] = round(float(avg_score), 2)
            except (ValueError, TypeError):
                 representation['average_quiz_score'] = 0.0
        else:
             representation['average_quiz_score'] = 0.0
        return representation


# --- Serializers per Registrazione Studente con Token ---

class StudentRegistrationTokenSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare i dettagli di un token di registrazione. """
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True, allow_null=True)
    is_valid = serializers.BooleanField(read_only=True) # Aggiunge lo stato di validità

    class Meta:
        model = StudentRegistrationToken
        fields = [
            'token', 'teacher', 'teacher_username', 'group', 'group_name',
            'created_at', 'expires_at', 'is_active', 'is_valid'
        ]
        read_only_fields = [
            'token', 'teacher', 'teacher_username', 'group_name',
            'created_at', 'expires_at', 'is_active', 'is_valid'
        ]


class StudentRegistrationTokenCreateSerializer(serializers.Serializer):
    """ Serializer per l'input della creazione di un token da parte del docente. """
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=StudentGroup.objects.all(), # Filtrato nella view/validazione
        source='group', # Mappa a 'group' nel modello
        allow_null=True,
        required=False,
        help_text="ID del gruppo a cui associare il token (opzionale)."
    )
    # Potremmo aggiungere un campo per la durata della validità qui, se necessario

    def validate_group_id(self, group):
        """ Valida che il gruppo appartenga al docente che crea il token. """
        teacher = self.context['request'].user
        if group and group.teacher != teacher:
            raise serializers.ValidationError(f"Il gruppo '{group.name}' non appartiene a questo docente.")
        return group

    def create(self, validated_data):
        """ Crea il token associandolo al docente autenticato. """
        teacher = self.context['request'].user
        if not teacher.is_teacher:
            # Questo non dovrebbe accadere con i permessi corretti sulla view
            raise serializers.ValidationError("Solo i docenti possono creare token.")

        # Crea il token, la scadenza viene impostata nel metodo save() del modello
        token = StudentRegistrationToken.objects.create(
            teacher=teacher,
            group=validated_data.get('group') # Può essere None
        )
        return token


class StudentSelfRegisterSerializer(serializers.Serializer):
    """ Serializer per l'input della registrazione dello studente. """
    token = serializers.UUIDField(required=True, write_only=True) # Reso write_only
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    pin = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'},
        help_text="PIN numerico di almeno 4 cifre." # Aggiornare se min length cambia
    )

    def validate_pin(self, value):
        """ Valida il PIN (numerico, lunghezza minima). """
        if not value or not value.isdigit():
            raise serializers.ValidationError("Il PIN deve essere numerico.")
        min_pin_length = getattr(settings, 'STUDENT_PIN_MIN_LENGTH', 4)
        if len(value) < min_pin_length:
            raise serializers.ValidationError(f"Il PIN deve essere di almeno {min_pin_length} cifre.")
        return value

    def validate_token(self, value):
        """ Valida che il token esista, sia attivo e non scaduto. """
        try:
            token_instance = StudentRegistrationToken.objects.get(token=value)
            if not token_instance.is_valid():
                raise serializers.ValidationError("Token non valido o scaduto.")
            # Possiamo aggiungere il token instance al contesto per usarlo nel create
            self.context['registration_token'] = token_instance
        except StudentRegistrationToken.DoesNotExist:
            raise serializers.ValidationError("Token non valido.")
        return value

    def create(self, validated_data):
        """ Crea lo studente usando i dati validati e il token. """
        token_instance = self.context['registration_token']
        teacher = token_instance.teacher
        group = token_instance.group

        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        raw_pin = validated_data['pin']

        # Genera codice studente univoco
        student_code = generate_unique_student_code(first_name, last_name)

        # Crea lo studente
        student = Student(
            teacher=teacher,
            first_name=first_name,
            last_name=last_name,
            student_code=student_code,
            group=group # Assegna il gruppo dal token (se presente)
        )

        # Imposta il PIN hashato
        try:
            student.set_pin(raw_pin)
        except ValueError as e:
            # Questo errore dovrebbe essere già stato catturato da validate_pin, ma per sicurezza
            raise serializers.ValidationError({"pin": str(e)})

        student.save()

        # NON disattivare il token dopo l'uso per permettere registrazioni multiple
        # fino alla scadenza naturale.
        # token_instance.is_active = False
        # token_instance.save(update_fields=['is_active'])

        # Restituiamo l'istanza dello studente creato
        # Potremmo voler restituire anche il codice studente e il nome docente/gruppo
        # per conferma, ma StudentSerializer può farlo.
        # Aggiungiamo il PIN in chiaro per la risposta (anche se lo studente l'ha appena inserito)
        student.pin = raw_pin # Utile se la risposta viene usata per fare login automatico
        return student