import logging
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from .models import (
    Wallet, PointTransaction, RewardTemplate, Reward,
    RewardAvailability, RewardPurchase, Badge, EarnedBadge
)
from django.db.models import Sum # Aggiunto per Sum
from apps.users.models import User, Student, UserRole # Import Student
from apps.student_groups.models import StudentGroup
# Importa i serializer base per Studente e Gruppo
from apps.users.serializers import StudentSerializer, StudentBasicSerializer
try:
    # Usa lo stesso serializer base definito in education (o creane uno qui se preferisci)
    from apps.education.serializers import StudentGroupBasicSerializer
except ImportError:
    # Fallback se non trovato
    class StudentGroupBasicSerializer(serializers.ModelSerializer):
        class Meta:
            model = StudentGroup
            fields = ['id', 'name']
            read_only_fields = fields

logger = logging.getLogger(__name__)

class WalletSerializer(serializers.ModelSerializer):
    """ Serializer per il modello Wallet (generalmente sola lettura tramite API). """
    student_info = StudentSerializer(source='student', read_only=True)

    class Meta:
        model = Wallet
        fields = ['student', 'student_info', 'current_points']
        read_only_fields = ['student', 'student_info', 'current_points']


class PointTransactionSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare le transazioni di punti. """
    class Meta:
        model = PointTransaction
        fields = ['id', 'wallet', 'points_change', 'reason', 'timestamp']
        read_only_fields = fields


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


class RewardSerializer(serializers.ModelSerializer):
    """ Serializer per le Reward specifiche create dai Docenti. """
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    description = serializers.CharField(allow_blank=True, allow_null=True, required=False, style={'base_template': 'textarea.html'}) # Permetti blank/null
    # Rimossi availability_type e availability_type_display

    class Meta:
        model = Reward
        fields = [
            'id', 'teacher', 'teacher_username', 'template', 'name', 'description',
            'type', 'type_display', 'cost_points',
            # Campi rimossi: 'availability_type', 'availability_type_display',
            'metadata', 'is_active', 'created_at'
        ]
        read_only_fields = ['teacher', 'teacher_username', 'type_display', 'created_at']

    # Validazione e create/update non gestiscono più la disponibilità direttamente


class RewardPurchaseSerializer(serializers.ModelSerializer):
    """ Serializer per la creazione e visualizzazione degli acquisti di ricompense. """
    student_info = StudentSerializer(source='student', read_only=True)
    reward_info = RewardSerializer(source='reward', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    delivered_by_username = serializers.CharField(source='delivered_by.username', read_only=True, allow_null=True)

    class Meta:
        model = RewardPurchase
        fields = [
            'id', 'student', 'student_info', 'reward', 'reward_info',
            'points_spent', 'purchased_at', 'status', 'status_display',
            'delivered_by', 'delivered_by_username', 'delivered_at',
            'delivery_notes'
        ]
        read_only_fields = [
            'student', 'student_info', 'reward_info', 'points_spent', 'purchased_at',
            'status', 'status_display', 'delivered_by', 'delivered_by_username', 'delivered_at'
        ]


# --- Serializers per Disponibilità Ricompense ---

class RewardAvailabilitySerializer(serializers.ModelSerializer):
    """ Serializer per VISUALIZZARE un record RewardAvailability esistente. """
    reward = RewardSerializer(read_only=True)
    student = StudentBasicSerializer(read_only=True, allow_null=True)
    group = StudentGroupBasicSerializer(read_only=True, allow_null=True)

    class Meta:
        model = RewardAvailability
        fields = [
            'id',
            'reward',
            'student',
            'group',
            'made_available_at',
        ]
        read_only_fields = fields


class MakeRewardAvailableSerializer(serializers.Serializer):
    """ Serializer per l'AZIONE di rendere disponibile una Ricompensa a uno Studente o Gruppo. """
    # reward_id verrà preso dall'URL nella view action
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), # Validazione ownership nella view
        required=False,
        allow_null=True,
        help_text="ID dello Studente a cui rendere disponibile (alternativo a group_id)."
    )
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=StudentGroup.objects.all(), # Validazione ownership nella view
        required=False,
        allow_null=True,
        help_text="ID del Gruppo a cui rendere disponibile (alternativo a student_id)."
    )
    # made_available_at viene impostato automaticamente

    def validate(self, attrs):
        student_id = attrs.get('student_id')
        group_id = attrs.get('group_id')

        if not student_id and not group_id:
            raise ValidationError("È necessario specificare 'student_id' o 'group_id'.")
        if student_id and group_id:
            raise ValidationError("Specificare solo 'student_id' o 'group_id', non entrambi.")
        return attrs

    def create(self, validated_data):
        reward = self.context['reward'] # Preso dal contesto passato dalla view
        student = validated_data.get('student_id')
        group = validated_data.get('group_id')
        teacher = self.context['request'].user

        # Verifica ownership
        if reward.teacher != teacher:
             raise ValidationError("Non puoi gestire la disponibilità di una ricompensa che non hai creato.")
        # Verifica che il docente che assegna sia il docente dello studente
        if student and student.teacher != teacher:
             raise ValidationError("Non puoi rendere disponibile una ricompensa a uno studente che non gestisci.")
        if group and group.teacher != teacher:
             raise ValidationError("Non puoi rendere disponibile a un gruppo che non hai creato.")

        # Controlla duplicati
        availability_exists = RewardAvailability.objects.filter(
            reward=reward,
            student=student,
            group=group
        ).exists()

        if availability_exists:
            target_type = "studente" if student else "gruppo"
            target_id = student.id if student else group.id
            raise ValidationError(f"Questa ricompensa è già disponibile per questo {target_type} (ID: {target_id}).")

        # Crea record disponibilità
        availability = RewardAvailability.objects.create(
            reward=reward,
            student=student,
            group=group,
            made_available_at=timezone.now()
        )
        return availability

    def to_representation(self, instance):
        # Usa il serializer di visualizzazione per l'output
        return RewardAvailabilitySerializer(instance, context=self.context).data


# --- Serializer Specifico per Dashboard Studente ---

class StudentWalletDashboardSerializer(serializers.Serializer):
    """
    Serializer per le informazioni del wallet nella dashboard studente.
    Combina i punti correnti con le transazioni recenti.
    """
    current_points = serializers.IntegerField(read_only=True)
    total_earned_points = serializers.SerializerMethodField()
    recent_transactions = serializers.SerializerMethodField()

    def get_total_earned_points(self, obj: Wallet):
        # obj è l'istanza del Wallet
        # Calcola la somma di tutte le transazioni di punti positive per questo portafoglio
        # Assicurati che PointTransaction abbia un related_name al Wallet, es. 'transactions'
        # o usa il default 'pointtransaction_set'
        total_earned = obj.transactions.filter(points_change__gt=0).aggregate(total=Sum('points_change'))['total']
        return total_earned if total_earned is not None else 0

    def get_recent_transactions(self, obj: Wallet):
        # obj è l'istanza del Wallet
        # Recupera le ultime N transazioni, ad esempio 5
        transactions = obj.transactions.order_by('-timestamp')[:5]
        # Serializzale usando PointTransactionSerializer
        # È importante passare il contesto se PointTransactionSerializer ne avesse bisogno (es. per request)
        # In questo caso, PointTransactionSerializer è semplice e non sembra richiederlo.
        return PointTransactionSerializer(transactions, many=True, context=self.context).data


# --- Serializers per Gamification (Badge) ---

class BadgeSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare le definizioni dei Badge. """
    trigger_type_display = serializers.CharField(source='get_trigger_type_display', read_only=True)
    media_type = serializers.CharField(read_only=True) # Aggiunto da modello
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    is_earned = serializers.SerializerMethodField()

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url') and request:
            try:
                return request.build_absolute_uri(obj.file.url)
            except ValueError:
                logger.warning(f"Impossibile costruire URL assoluto per il file del badge {obj.id} ({obj.file.name})")
                return None
        return None

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and hasattr(obj.thumbnail, 'url') and request:
            try:
                return request.build_absolute_uri(obj.thumbnail.url)
            except ValueError:
                logger.warning(f"Impossibile costruire URL assoluto per il thumbnail del badge {obj.id} ({obj.thumbnail.name})")
                return None
        return None

    def get_is_earned(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
            student_instance = None
            if isinstance(user, Student): # Se l'utente loggato è già uno Studente
                student_instance = user
            # Rimosso il blocco elif hasattr(user, 'student_profile') perché
            # il modello Student non è direttamente collegato a User tramite un campo 'student_profile'.
            # La logica si affida al fatto che request.user sia un'istanza di Student.
            if student_instance: # student_instance è impostato solo se isinstance(user, Student) è True
                return EarnedBadge.objects.filter(student=student_instance, badge=obj).exists()
        return False

    class Meta:
        model = Badge
        fields = [
            'id', 'name', 'description',
            'file_url', 'media_type', 'thumbnail_url', # Campi media aggiornati
            'trigger_type', 'trigger_type_display', 'trigger_condition',
            'is_active', 'created_at',
            'is_earned' # Aggiunto flag
        ]
        # 'file' e 'thumbnail' (i campi FileField/ImageField) non sono inclusi direttamente
        # perché esponiamo solo gli URL.


class EarnedBadgeSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare i Badge guadagnati da uno studente. """
    # BadgeSerializer ora include 'is_earned', che sarà True in questo contesto.
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = EarnedBadge
        fields = ['id', 'student', 'badge', 'earned_at']
        read_only_fields = fields


class SimpleBadgeSerializer(serializers.ModelSerializer):
    """ Serializer semplificato per i Badge, usato per le notifiche o liste. """
    # Manteniamo questo semplice, ma potrebbe beneficiare di file_url e media_type
    # a seconda dell'uso. Per ora, aggiorniamo solo il riferimento al campo file.
    file_url = serializers.SerializerMethodField(method_name='get_file_url_for_simple')
    media_type = serializers.CharField(read_only=True)

    def get_file_url_for_simple(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url') and request:
             try:
                 return request.build_absolute_uri(obj.file.url)
             except ValueError:
                 return None
        return None

    class Meta:
        model = Badge
        fields = ['id', 'name', 'description', 'file_url', 'media_type']
# --- Serializers Specifici per Esportazione GDPR ---

class GDPRPointTransactionSerializer(serializers.ModelSerializer):
    """ Serializer per esportare le transazioni di punti per GDPR. """
    class Meta:
        model = PointTransaction
        fields = ['id', 'points_change', 'reason', 'timestamp'] # Escludiamo 'wallet' per evitare ridondanza
        read_only_fields = fields


class GDPRWalletSerializer(serializers.ModelSerializer):
    """ Serializer per esportare i dati del Wallet per GDPR, incluse tutte le transazioni. """
    transactions = GDPRPointTransactionSerializer(many=True, read_only=True, source='pointtransaction_set') # Usa related_name implicito o esplicito

    class Meta:
        model = Wallet
        fields = ['current_points', 'transactions']
        read_only_fields = fields


class GDPRRewardPurchaseSerializer(serializers.ModelSerializer):
    """ Serializer per esportare gli acquisti di ricompense per GDPR. """
    # Semplifichiamo le info sulla ricompensa per l'export
    reward_name = serializers.CharField(source='reward.name', read_only=True)
    reward_type = serializers.CharField(source='reward.get_type_display', read_only=True)
    delivered_by_username = serializers.CharField(source='delivered_by.username', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)


    class Meta:
        model = RewardPurchase
        fields = [
            'id',
            'reward', # Manteniamo l'ID per riferimento
            'reward_name',
            'reward_type',
            'points_spent',
            'purchased_at',
            'status',
            'status_display',
            'delivered_by', # Manteniamo l'ID per riferimento
            'delivered_by_username',
            'delivered_at',
            'delivery_notes'
        ]
        read_only_fields = fields