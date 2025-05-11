from rest_framework import serializers
from .models import (
    UDATemplate, UDATemplateTopic, UDATemplateContent,
    UDA, UDATopic, UDAContent, Course, UDASubject
)
from lezioni.models import Topic, Subject # Importa i modelli Topic e Subject
# Potrebbe essere necessario importare serializer da altre app se si fa nesting profondo
# from lezioni.serializers import TopicSerializer, LessonSerializer, SubjectSerializer # Esempio
# from apps.education.serializers import QuizSerializer # Esempio

class CourseSerializer(serializers.ModelSerializer):
   # uda_count = serializers.IntegerField(read_only=True) # Esempio per contare le UDA associate
   # udas = UDASerializer(many=True, read_only=True) # Esempio per mostrare UDA annidate

   class Meta:
       model = Course
       fields = [
           'id', 'teacher', 'name', 'description',
           'created_at', 'updated_at',
           # 'uda_count', 'udas' # Esempio
       ]
       read_only_fields = ['id', 'teacher', 'created_at', 'updated_at']

   def create(self, validated_data):
       # Imposta il teacher automaticamente sull'utente loggato
       validated_data['teacher'] = self.context['request'].user
       return super().create(validated_data)

class UDATemplateTopicSerializer(serializers.ModelSerializer):
    # Serializer di base, potrebbe non essere necessario esporlo direttamente
    # se gestito tramite il ManyToManyField nel UDATemplateSerializer
    class Meta:
        model = UDATemplateTopic
        fields = ['topic'] # O ['id', 'topic'] a seconda delle necessità

class UDATemplateContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UDATemplateContent
        fields = [
            'id', 'content_type', 'lesson', 'quiz_template', # Modificato da quiz
            'note_template_title', 'note_template_content',
            'activity_template_title', 'activity_template_description',
            'order'
        ]
        # read_only_fields = ['id'] # L'ID è implicitamente read-only alla creazione

    def validate(self, data):
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"[UDATemplateContentSerializer VALIDATE] Received data: {data}")

        content_type = data.get('content_type')
        lesson = data.get('lesson')
        quiz_template = data.get('quiz_template') # Modificato da quiz
        note_template_title = data.get('note_template_title')
        activity_template_title = data.get('activity_template_title')

        logger.warning(f"[UDATemplateContentSerializer VALIDATE] Validating content_type: {content_type}, quiz_template value: {quiz_template}, condition (not quiz_template): {not quiz_template}")

        if content_type == 'LESSON' and not lesson:
            logger.error(f"[UDATemplateContentSerializer VALIDATE] LESSON validation failed for data: {data}")
            raise serializers.ValidationError({'lesson': "Lesson is required for content type LESSON."})
        # content_type nel modello è stato aggiornato a QUIZ_TEMPLATE
        if content_type == 'QUIZ_TEMPLATE' and not quiz_template:
            logger.error(f"[UDATemplateContentSerializer VALIDATE] QUIZ_TEMPLATE validation failed for data: {data}. quiz_template value was: {quiz_template}")
            raise serializers.ValidationError({'quiz_template': "Quiz template is required for content type QUIZ_TEMPLATE."})
        if content_type == 'NOTE_TEMPLATE' and not note_template_title:
            logger.error(f"[UDATemplateContentSerializer VALIDATE] NOTE_TEMPLATE validation failed for data: {data}")
            raise serializers.ValidationError({'note_template_title': "Note template title is required for content type NOTE_TEMPLATE."})
        if content_type == 'ACTIVITY_TEMPLATE' and not activity_template_title:
            raise serializers.ValidationError({'activity_template_title': "Activity template title is required for content type ACTIVITY_TEMPLATE."})
        
        # Assicurarsi che solo i campi rilevanti per il content_type siano forniti
        # (Questa logica può essere espansa o gestita diversamente)
        if content_type != 'LESSON':
            data.pop('lesson', None)
        if content_type != 'QUIZ_TEMPLATE': # Modificato
            data.pop('quiz_template', None) # Modificato
        if content_type != 'NOTE_TEMPLATE':
            data.pop('note_template_title', None)
            data.pop('note_template_content', None)
        if content_type != 'ACTIVITY_TEMPLATE':
            data.pop('activity_template_title', None)
            data.pop('activity_template_description', None)
            
        return data

class UDATemplateSerializer(serializers.ModelSerializer):
    contents = UDATemplateContentSerializer(many=True, required=False)
    # topics = TopicSerializer(many=True, read_only=True) # Esempio se si vuole mostrare i dettagli del topic
    topic_ids = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        many=True,
        write_only=True,
        source='topics', # Mappa a topics nel modello
        required=False
    )
    # Per mostrare i nomi dei topic in lettura
    topics_display = serializers.StringRelatedField(many=True, source='topics', read_only=True)


    class Meta:
        model = UDATemplate
        fields = [
            'id', 'teacher', 'name', 'description', 'subject', 
            'topics_display', 'topic_ids', 'contents', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'teacher', 'created_at', 'updated_at']

    def create(self, validated_data):
        contents_data = validated_data.pop('contents', [])
        topics_data = validated_data.pop('topics', []) # Gestito da topic_ids
        
        # Imposta il teacher automaticamente sull'utente loggato
        validated_data['teacher'] = self.context['request'].user
        
        template = UDATemplate.objects.create(**validated_data)
        
        if topics_data: # topics_data sarà popolato da 'source' in topic_ids
             template.topics.set(topics_data)

        import logging
        logger = logging.getLogger(__name__)

        for content_data in contents_data:
            logger.warning(f"[UDATemplateSerializer CREATE] Attempting to create UDATemplateContent with data: {content_data}")
            UDATemplateContent.objects.create(uda_template=template, **content_data)
        return template

    def update(self, instance, validated_data):
        contents_data = validated_data.pop('contents', None)
        topics_data = validated_data.pop('topics', None)

        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.subject = validated_data.get('subject', instance.subject)
        instance.save()

        if topics_data is not None:
            instance.topics.set(topics_data)
        
        if contents_data is not None:
            # Logica per aggiornare i contenuti:
            # Si può cancellare e ricreare, o fare un matching più complesso
            instance.contents.all().delete() # Semplice: cancella e ricrea
            
            import logging # Assicurati che logging sia importato se non già fatto sopra nel file
            logger = logging.getLogger(__name__)

            for content_data in contents_data:
                logger.warning(f"[UDATemplateSerializer UPDATE] Attempting to create UDATemplateContent with data: {content_data}")
                UDATemplateContent.objects.create(uda_template=instance, **content_data)
        
        return instance


class UDATopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = UDATopic
        fields = ['topic']

class UDAContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UDAContent
        fields = [
            'id', 'content_type', 'lesson', 'quiz_template', # Modificato da quiz
            'note_title', 'note_content',
            'activity_title', 'activity_description', 'activity_attachment_url', 'activity_completed',
            'teacher_marked_completed', # Aggiunto come da piano
            'order'
        ]
        # read_only_fields = ['id']

    def validate(self, data):
        content_type = data.get('content_type')
        lesson = data.get('lesson')
        quiz_template = data.get('quiz_template') # Modificato da quiz
        note_title = data.get('note_title')
        activity_title = data.get('activity_title')

        # Validazione simile a UDATemplateContentSerializer, adattata per UDAContent
        if content_type == 'LESSON' and not lesson:
            raise serializers.ValidationError({'lesson': "Lesson is required for content type LESSON."})
        # content_type nel modello è stato aggiornato a QUIZ_TEMPLATE
        if content_type == 'QUIZ' and not quiz_template: # MODIFICATO QUIZ_TEMPLATE a QUIZ
            raise serializers.ValidationError({'quiz_template': "Quiz template is required for content type QUIZ."}) # MODIFICATO
        if content_type == 'NOTE' and not note_title:
            raise serializers.ValidationError({'note_title': "Note title is required for content type NOTE."})
        if content_type == 'ACTIVITY' and not activity_title:
            raise serializers.ValidationError({'activity_title': "Activity title is required for content type ACTIVITY."})

        # Assicurarsi che solo i campi rilevanti per il content_type siano forniti
        if content_type != 'LESSON':
            data.pop('lesson', None)
        if content_type != 'QUIZ': # MODIFICATO QUIZ_TEMPLATE a QUIZ
            data.pop('quiz_template', None) # Modificato
        if content_type != 'NOTE':
            data.pop('note_title', None)
            data.pop('note_content', None)
        if content_type != 'ACTIVITY':
            data.pop('activity_title', None)
            data.pop('activity_description', None)
            data.pop('activity_attachment_url', None)
            data.pop('activity_completed', None)
            # teacher_marked_completed è applicabile a tutti i tipi di UDAContent, quindi non lo rimuoviamo qui.
            
        return data

class UDASerializer(serializers.ModelSerializer):
   contents = UDAContentSerializer(many=True, required=False)
   # topics = TopicSerializer(many=True, read_only=True) # Esempio
   topic_ids = serializers.PrimaryKeyRelatedField(
       queryset=Topic.objects.all(),
       many=True,
       write_only=True,
       source='topics',
       required=False
   )
   topics_display = serializers.StringRelatedField(many=True, source='topics', read_only=True)
   source_template_id = serializers.PrimaryKeyRelatedField(
       queryset=UDATemplate.objects.all(),
       source='source_template',
       required=False,
       allow_null=True
   )
   course_id = serializers.PrimaryKeyRelatedField(
       queryset=Course.objects.all(),
       source='course', # Mappa al campo 'course' del modello UDA
       write_only=True,
       required=False, # Come da modello UDA, course è opzionale
       allow_null=True
   )
   # Per la lettura, potremmo voler serializzare l'intero oggetto Course o solo alcuni campi.
   # Per ora, usiamo StringRelatedField per una rappresentazione semplice.
   # In alternativa, si potrebbe usare un CourseSerializer nested (read_only=True).
   course_display = serializers.StringRelatedField(source='course', read_only=True)

   subject_ids = serializers.PrimaryKeyRelatedField(
       queryset=Subject.objects.all(),
       many=True,
       write_only=True,
       source='subjects', # Mappa a subjects nel modello UDA
       required=False
   )
   subjects_display = serializers.StringRelatedField(many=True, source='subjects', read_only=True)


   class Meta:
       model = UDA
       fields = [
           'id', 'teacher', 'source_template_id', 'title', 'description',
           'start_date', 'end_date',
           'subjects_display', 'subject_ids', # Sostituisce 'subject'
           'course_id', 'course_display', 'order_in_course',
           'topics_display', 'topic_ids', 'status', 'contents',
           'created_at', 'updated_at'
       ]
       read_only_fields = ['id', 'teacher', 'created_at', 'updated_at']

   def create(self, validated_data):
       contents_data = validated_data.pop('contents', [])
       topics_data = validated_data.pop('topics', []) # Gestito da topic_ids
       subject_data = validated_data.pop('subjects', []) # Gestito da subject_ids
       
       validated_data['teacher'] = self.context['request'].user
       
       uda = UDA.objects.create(**validated_data)

       if topics_data:
           uda.topics.set(topics_data)
       
       if subject_data: # Aggiunto per gestire le materie
           uda.subjects.set(subject_data)

       # Se source_template è fornito e i contenuti non sono forniti esplicitamente,
       # copia i contenuti dal template
       source_template = validated_data.get('source_template')
       if source_template and not contents_data:
           for template_content in source_template.contents.all():
               content_data = {
                   'content_type': (
                       'QUIZ' if template_content.content_type == 'QUIZ_TEMPLATE'
                       else 'NOTE' if template_content.content_type == 'NOTE_TEMPLATE'
                       else 'ACTIVITY' if template_content.content_type == 'ACTIVITY_TEMPLATE'
                       else template_content.content_type # Mantiene LESSON o altri tipi
                   ),
                   'lesson': template_content.lesson,
                   'quiz_template': template_content.quiz_template,
                   'note_title': template_content.note_template_title,
                   'note_content': template_content.note_template_content,
                   'activity_title': template_content.activity_template_title,
                   'activity_description': template_content.activity_template_description,
                   'order': template_content.order,
                   # teacher_marked_completed di default è False per i nuovi UDAContent
                   # activity_attachment_url e activity_completed non vengono copiati di default
               }
               # Rimuovi chiavi None prima di creare UDAContent
               content_data_cleaned = {k: v for k, v in content_data.items() if v is not None}
               UDAContent.objects.create(uda=uda, **content_data_cleaned)
       else:
           for content_data in contents_data:
               UDAContent.objects.create(uda=uda, **content_data)
       return uda

   def update(self, instance, validated_data):
       contents_data = validated_data.pop('contents', None)
       topics_data = validated_data.pop('topics', None)
       subject_data = validated_data.pop('subjects', None) # Aggiunto per gestire le materie

       instance.title = validated_data.get('title', instance.title)
       instance.description = validated_data.get('description', instance.description)
       instance.start_date = validated_data.get('start_date', instance.start_date)
       instance.end_date = validated_data.get('end_date', instance.end_date)
       # instance.subject = validated_data.get('subject', instance.subject) # Rimosso
       instance.status = validated_data.get('status', instance.status)
       instance.course = validated_data.get('course', instance.course) # Gestisce l'associazione al corso
       instance.order_in_course = validated_data.get('order_in_course', instance.order_in_course)
       # source_template non dovrebbe essere modificabile dopo la creazione
       instance.save()

       if topics_data is not None:
           instance.topics.set(topics_data)
       
       if subject_data is not None: # Aggiunto per gestire le materie
           instance.subjects.set(subject_data)

       if contents_data is not None:
           instance.contents.all().delete() # Semplice: cancella e ricrea
           for content_data in contents_data:
               UDAContent.objects.create(uda=instance, **content_data)
       
       return instance