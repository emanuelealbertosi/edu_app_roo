import logging # Aggiunto import per logging
from rest_framework import serializers
from .models import (
    Wallet, PointTransaction, RewardTemplate, Reward,
    RewardStudentSpecificAvailability, RewardPurchase
)
from apps.users.models import User, Student, UserRole # Import User, Student for validation/representation
from apps.users.serializers import StudentSerializer
from .models import Badge, EarnedBadge # Importa i nuovi modelli

logger = logging.getLogger(__name__) # Inizializza il logger

# Nota: Non creiamo un serializer per RewardStudentSpecificAvailability direttamente,
# la sua gestione avverrà tramite il RewardSerializer.

class WalletSerializer(serializers.ModelSerializer):
    """ Serializer per il modello Wallet (generalmente sola lettura tramite API). """
    student_info = StudentSerializer(source='student', read_only=True) # Mostra info studente

    class Meta:
        model = Wallet
        fields = ['student', 'student_info', 'current_points']
        read_only_fields = ['student', 'student_info', 'current_points'] # Il saldo è gestito internamente


class PointTransactionSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare le transazioni di punti. """
    class Meta:
        model = PointTransaction
        fields = ['id', 'wallet', 'points_change', 'reason', 'timestamp']
        read_only_fields = fields # Le transazioni sono create internamente


class RewardTemplateSerializer(serializers.ModelSerializer):
    """ Serializer per i RewardTemplate (globali e locali). """
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = RewardTemplate
        fields = [
            'id', 'creator', 'creator_username', 'scope', 'scope_display',
            'name', 'description', 'type', 'type_display', 'metadata', 'created_at'
        ]
        read_only_fields = ['creator', 'creator_username', 'scope', 'scope_display', 'type_display', 'created_at']
        # Admin può creare scope=GLOBAL, Docente può creare scope=LOCAL (logica nella view)

    def validate(self, data):
        # La logica per impostare creator e scope in base all'utente autenticato
        # verrà gestita nella ViewSet (perform_create).
        return data


class RewardSerializer(serializers.ModelSerializer):
    """ Serializer per le Reward specifiche create dai Docenti. """
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    availability_type_display = serializers.CharField(source='get_availability_type_display', read_only=True)
    # Campo per ricevere gli ID degli studenti specifici durante la creazione/aggiornamento
    # Il queryset verrà sovrascritto dalla ViewSet per filtrare per docente
    specific_student_ids = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), # Queryset base, la validazione specifica avverrà in validate()
        many=True,
        write_only=True, # Usato solo per input, non mostrato nell'output standard
        required=False, # Non richiesto se availability_type è ALL
        source='available_to_specific_students' # Collega a M2M
    )
    # Campo per OUTPUT (read-only) con gli ID degli studenti specifici
    available_to_specific_students = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True # Legge dalla relazione M2M 'available_to_specific_students'
    )
    # Opzionale: Mostrare le info complete degli studenti specifici (sola lettura)
    available_students_info = StudentSerializer(source='available_to_specific_students', many=True, read_only=True)
    class Meta:
        model = Reward
        fields = [
            'id', 'teacher', 'teacher_username', 'template', 'name', 'description',
            'type', 'type_display', 'cost_points', 'availability_type', 'availability_type_display',
            'specific_student_ids', # Input per studenti specifici
            'available_to_specific_students', # Output ID studenti specifici
            'available_students_info', # Output info complete studenti (opzionale)
            'metadata', 'is_active', 'created_at'
        ]
        read_only_fields = ['teacher', 'teacher_username', 'type_display', 'availability_type_display', 'available_to_specific_students', 'available_students_info', 'created_at']

    def validate(self, data):
        availability_type = data.get('availability_type', self.instance.availability_type if self.instance else None)
        specific_students = data.get('available_to_specific_students') # source='available_to_specific_students'

        if availability_type == Reward.AvailabilityType.SPECIFIC_STUDENTS and not specific_students:
            raise serializers.ValidationError({
                'specific_student_ids': "Se la disponibilità è 'Specific Students', è necessario fornire almeno un ID studente."
            })
        if availability_type == Reward.AvailabilityType.ALL_STUDENTS and specific_students:
             raise serializers.ValidationError({
                'specific_student_ids': "Non fornire ID studenti specifici se la disponibilità è 'All Students'."
            })

        # Validazione aggiuntiva: assicurarsi che gli studenti specificati appartengano al docente
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            # Questo non dovrebbe accadere se la view passa il contesto correttamente
            raise serializers.ValidationError("Contesto della richiesta mancante per la validazione.")

        user = request.user
        if isinstance(user, User) and user.is_teacher:
            if specific_students: # Se sono stati forniti studenti specifici
                teacher_student_ids = set(user.students.values_list('id', flat=True))
                for student in specific_students:
                    if student.pk not in teacher_student_ids:
                        raise serializers.ValidationError({
                            'specific_student_ids': f"Lo studente con ID {student.pk} non appartiene a questo docente."
                        })
        else:
            # Se l'utente non è un docente, non dovrebbe poter specificare studenti
            if specific_students:
                 raise serializers.ValidationError({
                    'specific_student_ids': "Solo i docenti possono specificare studenti."
                })

        return data


    def create(self, validated_data):
        # La logica per impostare il 'teacher' e validare gli studenti specifici
        # rispetto al docente verrà gestita nella ViewSet (perform_create).
        # Il campo M2M 'available_to_specific_students' viene gestito automaticamente
        # da DRF se 'specific_student_ids' è nel validated_data.
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Gestione M2M per 'available_to_specific_students'
        # DRF gestisce l'aggiornamento M2M se il campo è presente in validated_data.
        # Se availability_type cambia da SPECIFIC a ALL, potremmo voler pulire la M2M.
        availability_type = validated_data.get('availability_type', instance.availability_type)
        if availability_type == Reward.AvailabilityType.ALL_STUDENTS:
             # Se si passa a ALL, assicuriamoci che la M2M sia vuota
             validated_data['available_to_specific_students'] = []

        return super().update(instance, validated_data)


class RewardPurchaseSerializer(serializers.ModelSerializer):
    """ Serializer per la creazione e visualizzazione degli acquisti di ricompense. """
    student_info = StudentSerializer(source='student', read_only=True)
    reward_info = RewardSerializer(source='reward', read_only=True) # Mostra dettagli ricompensa
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    delivered_by_username = serializers.CharField(source='delivered_by.username', read_only=True, allow_null=True)

    class Meta:
        model = RewardPurchase
        fields = [
            'id', 'student', 'student_info', 'reward',
            'reward_info', # Assicura che i dettagli della ricompensa siano inclusi
            'points_spent', 'purchased_at', 'status', 'status_display',
            'delivered_by', 'delivered_by_username', 'delivered_at',
            'delivery_notes' # Assicura che le note di consegna siano incluse
        ]
        read_only_fields = [
            'student', 'student_info', 'reward_info', 'points_spent', 'purchased_at',
            'status', 'status_display', 'delivered_by', 'delivered_by_username', 'delivered_at'
            # 'reward' è scrivibile solo in fase di creazione (nella view)
            # 'delivery_notes' è modificabile dal docente (nella view di consegna)
        ]

    # La logica di acquisto (controllo punti, disponibilità ricompensa, creazione transazione)
    # verrà gestita nella ViewSet (perform_create).


# --- Serializer Specifico per Dashboard Studente ---

class StudentWalletDashboardSerializer(serializers.Serializer):
    """
    Serializer per le informazioni del wallet nella dashboard studente.
    Combina i punti correnti con le transazioni recenti.
    """
    current_points = serializers.IntegerField(read_only=True)
    # Usa PointTransactionSerializer per le transazioni recenti
    recent_transactions = PointTransactionSerializer(many=True, read_only=True)

    # Nota: Questo non è un ModelSerializer perché aggrega dati da Wallet e PointTransaction.
    # La view dovrà costruire l'oggetto dati da passare a questo serializer.


# --- Serializers per Gamification (Badge) ---

class BadgeSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare le definizioni dei Badge. """
    trigger_type_display = serializers.CharField(source='get_trigger_type_display', read_only=True)
    # Usa SerializerMethodField per costruire manualmente l'URL completo
    image_url = serializers.SerializerMethodField()

    def get_image_url(self, obj):
        # DEBUGGING: Log per capire cosa succede
        logger.debug(f"Serializing image for Badge ID: {obj.id}")
        logger.debug(f"  obj.image value: {obj.image}")
        request = self.context.get('request')
        logger.debug(f"  request in context: {'Present' if request else 'Missing'}")
        if obj.image and request:
            image_full_url = request.build_absolute_uri(obj.image.url)
            logger.debug(f"  Generated image_url: {image_full_url}")
            return image_full_url
        else:
            logger.debug(f"  Condition (obj.image and request) is False, returning None.")
            return None
    class Meta:
        model = Badge
        fields = [
            'id', 'name', 'description', 'image', 'image_url', # Manteniamo 'image' per ora, aggiungiamo image_url
            'trigger_type', 'trigger_type_display', 'trigger_condition',
            'is_active', 'created_at'
        ]
        # read_only_fields = fields # Rimosso temporaneamente per non bloccare 'image'


class EarnedBadgeSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare i Badge guadagnati da uno studente. """
    # Includi i dettagli del badge guadagnato
    badge = BadgeSerializer(read_only=True)
    # Opzionale: includere info studente se la view non è già filtrata per studente
    # student_info = StudentSerializer(source='student', read_only=True)

    class Meta:
        model = EarnedBadge
        fields = ['id', 'student', 'badge', 'earned_at']
        read_only_fields = fields # Questi record sono creati dalla logica interna


class SimpleBadgeSerializer(serializers.ModelSerializer):
    """ Serializer semplificato per i Badge, usato per le notifiche. """
    # Aggiunto image (che ora è ImageField) - Manteniamo per confronto
    image = serializers.ImageField(read_only=True)
    # Aggiungiamo anche image_url qui per coerenza se necessario in futuro
    image_url = serializers.SerializerMethodField()

    # Aggiunto metodo mancante per generare l'URL
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    class Meta:
        model = Badge
        # Sostituito image_url con image, aggiunto image_url
        fields = ['id', 'name', 'description', 'image', 'image_url']
        # read_only_fields = fields # Rimosso temporaneamente