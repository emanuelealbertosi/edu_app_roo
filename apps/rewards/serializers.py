from rest_framework import serializers
from .models import (
    Wallet, PointTransaction, RewardTemplate, Reward,
    RewardStudentSpecificAvailability, RewardPurchase
)
from apps.users.models import Student, UserRole # Import Student for validation/representation
from apps.users.serializers import StudentSerializer # Potentially useful for nested data

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
    specific_student_ids = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), # Queryset base, verrà filtrato nella view
        many=True,
        write_only=True, # Usato solo per input, non mostrato nell'output standard
        required=False, # Non richiesto se availability_type è ALL
        source='available_to_specific_students' # Collega a M2M
    )
    # Opzionale: Mostrare gli studenti specifici a cui è disponibile (sola lettura)
    available_students_info = StudentSerializer(source='available_to_specific_students', many=True, read_only=True)

    class Meta:
        model = Reward
        fields = [
            'id', 'teacher', 'teacher_username', 'template', 'name', 'description',
            'type', 'type_display', 'cost_points', 'availability_type', 'availability_type_display',
            'specific_student_ids', # Input per studenti specifici
            'available_students_info', # Output (opzionale)
            'metadata', 'is_active', 'created_at'
        ]
        read_only_fields = ['teacher', 'teacher_username', 'type_display', 'availability_type_display', 'available_students_info', 'created_at']

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
        # Questa logica è meglio gestirla nella ViewSet (get_serializer_context o perform_create/update)
        # per avere accesso all'utente autenticato (request.user).

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
            'id', 'student', 'student_info', 'reward', 'reward_info', 'points_spent',
            'purchased_at', 'status', 'status_display', 'delivered_by', 'delivered_by_username',
            'delivered_at', 'delivery_notes'
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