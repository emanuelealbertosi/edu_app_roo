from django.utils.text import get_valid_filename
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from .models import Subject, Topic, Lesson, LessonContent, LessonAssignment
from apps.users.models import Student # Importa Student
from apps.student_groups.models import StudentGroup # Importa StudentGroup
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

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'description', 'creator', 'created_at', 'updated_at']
        read_only_fields = ['creator', 'created_at', 'updated_at']

class TopicSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)

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
    # assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True) # Campo rimosso dal modello

    class Meta:
        model = LessonAssignment
        fields = [
            'id',
            'lesson',
            'student',
            'group',
            # 'assigned_by', # Campo rimosso dal modello
            # 'assigned_by_username', # Campo rimosso dal modello
            'assigned_at',
            'viewed_at',
            # Aggiungere eventuali altri campi rilevanti dal modello LessonAssignment
        ]
        # Questo serializer è principalmente per la lettura dei dati di un'assegnazione esistente
        read_only_fields = fields


class AssignLessonSerializer(serializers.Serializer):
    """ Serializer per l'AZIONE di assegnare una Lezione esistente a uno Studente o a un Gruppo. """
    # lesson_id verrà preso dall'URL nella view action, non serve qui
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), # Validazione ownership nella view
        required=False,
        allow_null=True,
        help_text="ID dello Studente a cui assegnare (alternativo a group_id)."
    )
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=StudentGroup.objects.all(), # Validazione ownership nella view
        required=False,
        allow_null=True,
        help_text="ID del Gruppo a cui assegnare (alternativo a student_id)."
    )
    # assigned_at e assigned_by vengono impostati automaticamente nella view

    def validate(self, attrs):
        student_id = attrs.get('student_id')
        group_id = attrs.get('group_id')

        if not student_id and not group_id:
            raise ValidationError("È necessario specificare 'student_id' o 'group_id'.")
        if student_id and group_id:
            raise ValidationError("Specificare solo 'student_id' o 'group_id', non entrambi.")

        # Validazione ownership sarà fatta nel metodo create/view
        return attrs

    def create(self, validated_data):
        lesson = self.context['lesson'] # Preso dal contesto passato dalla view
        student = validated_data.get('student_id')
        group = validated_data.get('group_id')
        teacher = self.context['request'].user

        # Verifica ownership
        if lesson.creator != teacher:
             raise ValidationError("Non puoi assegnare una lezione che non hai creato.")
        if student and student.user_id != teacher.id:
             raise ValidationError("Non puoi assegnare a uno studente non associato a te.")
        if group and group.teacher != teacher:
             raise ValidationError("Non puoi assegnare a un gruppo che non hai creato.")

        # Controlla duplicati
        assignment_exists = LessonAssignment.objects.filter(
            lesson=lesson,
            student=student,
            group=group
        ).exists()

        if assignment_exists:
            target_type = "studente" if student else "gruppo"
            target_id = student.id if student else group.id
            raise ValidationError(f"Questa lezione è già assegnata a questo {target_type} (ID: {target_id}).")

        # Crea assegnazione
        assignment = LessonAssignment.objects.create(
            lesson=lesson,
            student=student,
            group=group,
            # assigned_by=teacher, # Campo rimosso dal modello
            assigned_at=timezone.now()
        )
        return assignment

    def to_representation(self, instance):
        # Usa il serializer di visualizzazione per l'output
        return LessonAssignmentSerializer(instance, context=self.context).data

# Rimosso BulkLessonAssignSerializer perché obsoleto con l'introduzione dei gruppi
# L'assegnazione bulk può essere re-implementata se necessario, gestendo sia studenti che gruppi.