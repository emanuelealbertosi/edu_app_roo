from django.utils.text import get_valid_filename
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from .models import Subject, Topic, Lesson, LessonContent, LessonAssignment
from apps.users.models import Student # Importa Student
from apps.student_groups.models import StudentGroup # Importa StudentGroup
# Importa User model per UserSummarySerializer
from apps.users.models import User
# Importa i serializer base per Studente e Gruppo
from apps.users.serializers import StudentBasicSerializer
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

# --- Serializer per Riepilogo Utente ---
# (Se un serializer simile esiste già in apps/users/serializers.py, importalo invece di definirlo qui)
class UserSummarySerializer(serializers.ModelSerializer):
    """ Serializer minimale per mostrare nome/cognome/username utente. """
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']
        read_only_fields = fields # Questo serializer è solo per la lettura

class SubjectSerializer(serializers.ModelSerializer):
    # Aggiungiamo UserSummarySerializer per il creatore
    creator = UserSummarySerializer(read_only=True)
    class Meta:
        model = Subject
        fields = ['id', 'name', 'description', 'creator', 'created_at', 'updated_at']
        read_only_fields = ['creator', 'created_at', 'updated_at']

class TopicSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    # Aggiungiamo UserSummarySerializer per il creatore
    creator = UserSummarySerializer(read_only=True)
    class Meta:
        model = Topic
        fields = ['id', 'name', 'description', 'subject', 'subject_name', 'creator', 'created_at', 'updated_at']
        read_only_fields = ['creator', 'created_at', 'updated_at', 'subject_name']

class LessonContentSerializer(serializers.ModelSerializer):
    def _sanitize_filename(self, validated_data):
        uploaded_file = validated_data.get('file')
        if uploaded_file:
            original_name = uploaded_file.name
            safe_name = get_valid_filename(original_name)
            uploaded_file.name = safe_name
        return validated_data

    def create(self, validated_data):
        validated_data = self._sanitize_filename(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data = self._sanitize_filename(validated_data)
        return super().update(instance, validated_data)

    class Meta:
        model = LessonContent
        fields = ['id', 'lesson', 'content_type', 'html_content', 'file', 'url', 'title', 'order', 'created_at']
        read_only_fields = ['lesson', 'created_at']

class LessonSerializer(serializers.ModelSerializer):
    contents = LessonContentSerializer(many=True, read_only=True)
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_name = serializers.CharField(source='topic.subject.name', read_only=True)
    # Specifica UserSummarySerializer per il campo creator
    creator = UserSummarySerializer(read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'topic', 'topic_name', 'subject_name',
            'creator', 'created_at', 'updated_at', 'is_published', 'contents'
        ]
        read_only_fields = ['creator', 'created_at', 'updated_at', 'topic_name', 'subject_name', 'contents']

class LessonWriteSerializer(serializers.ModelSerializer):
     class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'topic', 'is_published']
        read_only_fields = ['id']

# --- Serializer per Assegnazioni Lezioni (MODIFICATO) ---

class LessonAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer per VISUALIZZARE un'assegnazione Lezione esistente (a Studente o Gruppo). """
    lesson = LessonSerializer(read_only=True) # Mostra dettagli lezione
    student = StudentBasicSerializer(read_only=True, allow_null=True) # Dettagli studente (se applicabile)
    group = StudentGroupBasicSerializer(read_only=True, allow_null=True) # Dettagli gruppo (se applicabile)
    # Usiamo UserSummarySerializer anche per assigned_by per coerenza
    assigned_by = UserSummarySerializer(read_only=True)
    # assigned_by_username non è più necessario se usiamo il serializer annidato
    # assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True, default='N/A')

    class Meta:
        model = LessonAssignment
        fields = [
            'id',
            'lesson',
            'student', # Mantenuto per compatibilità, ma sarà sempre null nelle nuove assegnazioni
            'group',
            'assigned_by', # Ora è un oggetto UserSummary
            # 'assigned_by_username', # Rimosso
            'assigned_at',
            'viewed_at',
        ]
        # Questo serializer è principalmente per la lettura dei dati di un'assegnazione esistente
        read_only_fields = fields


class AssignLessonSerializer(serializers.Serializer):
    """ Serializer per l'AZIONE di assegnare una Lezione esistente a un Gruppo. """
    # lesson_id verrà preso dall'URL nella view action
    # student_id rimosso, si assegna solo a gruppi
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=StudentGroup.objects.all(), # La view verificherà l'accesso al gruppo
        required=True, # Ora è obbligatorio
        allow_null=False,
        help_text="ID del Gruppo a cui assegnare la lezione."
    )
    # assigned_at e assigned_by vengono impostati automaticamente (assigned_by nel create)

    # validate non è più necessario per controllare student_id vs group_id
    # def validate(self, attrs):
    #     group_id = attrs.get('group_id')
    #     # Il campo è già required=True, quindi non serve controllare se è vuoto
    #     # La view controllerà se l'utente ha accesso a questo group_id
    #     return attrs

    def create(self, validated_data):
        lesson = self.context['lesson'] # Preso dal contesto passato dalla view
        group = validated_data['group_id'] # Ora è obbligatorio e si chiama group_id
        assigning_user = self.context['request'].user # Utente che sta eseguendo l'azione

        # I controlli di permesso (accesso al gruppo) sono fatti nella view prima di chiamare il serializer
        # Rimuoviamo i controlli di ownership obsoleti

        # Controlla duplicati (solo per gruppo ora)
        assignment_exists = LessonAssignment.objects.filter(
            lesson=lesson,
            group=group,
            student=None # Assicurati di controllare solo assegnazioni a gruppo
        ).exists()

        if assignment_exists:
            raise ValidationError(f"Questa lezione è già assegnata a questo gruppo (ID: {group.id}).")

        # Crea assegnazione impostando assigned_by
        assignment = LessonAssignment.objects.create(
            lesson=lesson,
            student=None, # Non assegniamo più a studenti singoli direttamente
            group=group,
            assigned_by=assigning_user, # Imposta chi ha assegnato
            assigned_at=timezone.now()
        )
        return assignment

    def to_representation(self, instance):
        # Usa il serializer di visualizzazione per l'output
        return LessonAssignmentSerializer(instance, context=self.context).data

# Rimosso BulkLessonAssignSerializer perché obsoleto con l'introduzione dei gruppi
# L'assegnazione bulk può essere re-implementata se necessario, gestendo sia studenti che gruppi.