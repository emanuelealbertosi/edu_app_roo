from rest_framework import serializers
from .models import Subject, Topic, Lesson, LessonContent, LessonAssignment
# Potrebbe essere necessario importare il serializer dello Studente se vogliamo dati annidati
# from apps.users.serializers import StudentSerializer # Esempio, verificare path corretto

class SubjectSerializer(serializers.ModelSerializer):
    # Potremmo aggiungere campi extra o personalizzare la rappresentazione qui
    class Meta:
        model = Subject
        fields = ['id', 'name', 'description', 'creator', 'created_at', 'updated_at']
        read_only_fields = ['creator', 'created_at', 'updated_at'] # Il creator viene impostato nella view

class TopicSerializer(serializers.ModelSerializer):
    # Mostra il nome della materia invece dell'ID per leggibilità
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = Topic
        # Includiamo subject (ID) per la scrittura, subject_name per la lettura
        fields = ['id', 'name', 'description', 'subject', 'subject_name', 'creator', 'created_at', 'updated_at']
        read_only_fields = ['creator', 'created_at', 'updated_at', 'subject_name'] # Il creator viene impostato nella view

class LessonContentSerializer(serializers.ModelSerializer):
    # Potremmo aggiungere validazione specifica per tipo di contenuto
    # (es. 'file' obbligatorio se type='pdf', 'html_content' se type='html')
    class Meta:
        model = LessonContent
        fields = ['id', 'lesson', 'content_type', 'html_content', 'file', 'url', 'title', 'order', 'created_at']
        read_only_fields = ['lesson', 'created_at'] # Lesson viene impostata nella view annidata

class LessonSerializer(serializers.ModelSerializer):
    # Serializer annidato per i contenuti, in sola lettura per la lista/dettaglio
    contents = LessonContentSerializer(many=True, read_only=True)
    # Mostra nome argomento e materia per leggibilità
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    subject_name = serializers.CharField(source='topic.subject.name', read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'topic', 'topic_name', 'subject_name',
            'creator', 'created_at', 'updated_at', 'is_published', 'contents'
        ]
        read_only_fields = ['creator', 'created_at', 'updated_at', 'topic_name', 'subject_name', 'contents']

# Serializer per la creazione/aggiornamento di Lesson (senza 'contents' annidato in scrittura)
class LessonWriteSerializer(serializers.ModelSerializer):
     class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'topic', 'is_published']
        # 'creator' verrà impostato nella view

class LessonAssignmentSerializer(serializers.ModelSerializer):
    # Mostra informazioni rilevanti sulla lezione e sullo studente
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    # Assumendo che Student abbia 'unique_identifier' o 'username'
    student_identifier = serializers.CharField(source='student.unique_identifier', read_only=True, default='N/A')
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)

    class Meta:
        model = LessonAssignment
        fields = [
            'id', 'lesson', 'student', 'assigned_by', 'assigned_at', 'viewed_at',
            'lesson_title', 'student_identifier', 'assigned_by_username'
        ]
        read_only_fields = ['assigned_by', 'assigned_at', 'viewed_at', 'lesson_title', 'student_identifier', 'assigned_by_username']
        # 'lesson' e 'student' sono scrivibili per la creazione

# Serializer specifico per l'azione di assegnazione bulk
class BulkLessonAssignSerializer(serializers.Serializer):
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="Lista degli ID degli studenti a cui assegnare la lezione."
    )
    # lesson_id verrà preso dall'URL