from rest_framework import serializers
from .models import User, Student, UserRole

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