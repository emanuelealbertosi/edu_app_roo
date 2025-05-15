from rest_framework import serializers
from django.conf import settings
import logging # Assicurati che sia presente, dovrebbe esserlo già
from urllib.parse import urlparse # AGGIUNTO PER LA GESTIONE DEGLI URL DEGLI ALLEGATI
from .models import (
    UDATemplate, UDATemplateTopic, UDATemplateContent,
    UDA, UDATopic, UDAContent, Course, UDASubject
)
from lezioni.models import Topic, Subject, Lesson # Importa i modelli Topic, Subject e Lesson
from apps.education.models import QuizTemplate # Importa il modello QuizTemplate
# Potrebbe essere necessario importare serializer da altre app se si fa nesting profondo
# from lezioni.serializers import TopicSerializer, LessonSerializer, SubjectSerializer # Esempio
# from apps.education.serializers import QuizSerializer # Esempio
from django.core.files.uploadedfile import UploadedFile
import logging

logger = logging.getLogger(__name__)

class LenientFileField(serializers.FileField):
    def to_internal_value(self, data):
        # Caso 1: File caricato valido
        if isinstance(data, UploadedFile):
            return super().to_internal_value(data)

        # Caso 2: Valori che indicano "cancellazione" o "nessun file fornito"
        if data is None or data == '':
            if self.allow_empty_file:
                return None
            else:
                self.fail('empty')
        
        if data is False: # Da ClearableFileInput
            return super().to_internal_value(data)

        # Caso 3: 'data' è una stringa (URL inviato dal client)
        # La lasciamo passare; la validazione a livello di serializer deciderà.
        if isinstance(data, str):
            logger.info(
                f"LenientFileField received a string value: '{str(data)[:100]}'. Passing it to serializer for validation."
            )
            return data # Restituisce la stringa stessa

        # Caso 4: Altri tipi di dati inattesi
        logger.warning(
            f"LenientFileField received unexpected data type for a file field: "
            f"Type: {type(data)}, Value: '{str(data)[:100]}'."
        )
        if self.allow_empty_file:
            return None
        else:
            # Se il file è richiesto e arriva un tipo inatteso, è un errore.
            # Usiamo 'invalid' che è una chiave standard.
            self.fail('invalid')

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

class LessonIdField(serializers.PrimaryKeyRelatedField): # Definizione spostata qui
    def __init__(self, **kwargs):
        if 'queryset' not in kwargs:
            # Imposta il queryset di default se non fornito, anche se è buona pratica passarlo esplicitamente.
            kwargs['queryset'] = Lesson.objects.all()
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        pk_value = None
        if isinstance(data, Lesson):
            pk_value = data.pk # Estrai il PK dall'istanza Lesson
        elif isinstance(data, dict) and 'id' in data:
            pk_value = data.get('id') # Estrai il PK dal dizionario
        else:
            # Assumi che 'data' sia già un PK o un valore che super() può gestire (es. None)
            pk_value = data

        # Passa il pk_value (che dovrebbe essere un ID o None) al metodo to_internal_value del genitore.
        # super().to_internal_value() poi recupererà l'istanza del modello o gestirà None.
        return super().to_internal_value(pk_value)

class QuizTemplateIdField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        if 'queryset' not in kwargs:
            kwargs['queryset'] = QuizTemplate.objects.all()
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        pk_value = None
        if isinstance(data, QuizTemplate):
            pk_value = data.pk
        elif isinstance(data, dict) and 'id' in data:
            pk_value = data.get('id')
        else:
            pk_value = data
        return super().to_internal_value(pk_value)

class UDATemplateContentSerializer(serializers.ModelSerializer):
    quiz_template = QuizTemplateIdField(allow_null=True, required=False)
    lesson = LessonIdField(allow_null=True, required=False) # Ora LessonIdField è definito

    class Meta:
        model = UDATemplateContent
        fields = [
            'id', 'content_type', 'lesson', 'quiz_template', # quiz_template ora usa QuizTemplateIdField
            'note_template_title', 'note_template_content',
            'activity_template_title', 'activity_template_description',
            'order', 'estimated_hours' # Aggiunto
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


# La definizione di LessonIdField è stata spostata più in alto.

class UDATopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = UDATopic
        fields = ['topic']

class UDAContentSerializer(serializers.ModelSerializer):
    # Logger specifico per questo serializer, se non già definito a livello di modulo
    # import logging # Assicurati sia importato
    # logger = logging.getLogger(__name__) # Assicurati sia definito

    lesson = LessonIdField(allow_null=True, required=False, queryset=Lesson.objects.all()) # LessonIdField è definito prima
    quiz_template = QuizTemplateIdField(allow_null=True, required=False) # QuizTemplateIdField è definito prima
    # Usa il LenientFileField personalizzato
    activity_attachment_url = LenientFileField(required=False, allow_null=True, use_url=True, allow_empty_file=True)

    class Meta:
        model = UDAContent
        fields = [
            'id', 'content_type', 'lesson', 'quiz_template', # quiz_template ora usa QuizTemplateIdField
            'note_title', 'note_content',
            'activity_title', 'activity_description', 'activity_attachment_url', 'activity_completed',
            'teacher_marked_completed', # Aggiunto come da piano
            'order', 'estimated_hours' # Aggiunto
        ]
        # read_only_fields = ['id']

    def validate(self, data):
        # Assicurati che logger sia accessibile qui
        logger.info(f"[UDAContentSerializer.validate] Input data to validate: {data}")

        content_type = data.get('content_type')
        if self.instance and 'content_type' not in data and hasattr(self.instance, 'content_type'):
            content_type = self.instance.content_type
        
        lesson = data.get('lesson')
        quiz_template = data.get('quiz_template') # Modificato da quiz
        note_title = data.get('note_title')
        activity_title = data.get('activity_title')

        # La gestione di activity_attachment_url vuoto è ora delegata al FileField
        # con allow_empty_file=True, quindi la normalizzazione esplicita qui non è più necessaria.

        # Validazione simile a UDATemplateContentSerializer, adattata per UDAContent
        if content_type == 'LESSON' and not lesson:
            raise serializers.ValidationError({'lesson': "Lesson is required for content type LESSON."})
        # Validazione per UDAContent di tipo QUIZ
        if content_type == 'QUIZ' and not quiz_template:
            raise serializers.ValidationError({'quiz_template': "Quiz template is required for content type QUIZ."})
        if content_type == 'NOTE':
            # Richiesto in creazione o se si tenta di svuotarlo in aggiornamento
            if not self.instance and not data.get('note_title'):
                raise serializers.ValidationError({'note_title': "Note title is required for content type NOTE."})
            elif self.instance and 'note_title' in data and not data.get('note_title'):
                raise serializers.ValidationError({'note_title': "Note title cannot be empty if provided for content type NOTE."})

        if content_type == 'ACTIVITY':
            # Richiesto in creazione o se si tenta di svuotarlo in aggiornamento
            if not self.instance and not data.get('activity_title'):
                raise serializers.ValidationError({'activity_title': "Activity title is required for content type ACTIVITY."})
            elif self.instance and 'activity_title' in data and not data.get('activity_title'):
                raise serializers.ValidationError({'activity_title': "Activity title cannot be empty if provided for content type ACTIVITY."})

        # Assicurarsi che solo i campi rilevanti per il content_type siano forniti
        if content_type != 'LESSON':
            data.pop('lesson', None)
        if content_type != 'QUIZ': # Coerente con il content_type 'QUIZ' per UDAContent
            data.pop('quiz_template', None)
        if content_type != 'NOTE':
            data.pop('note_title', None)
            data.pop('note_content', None)
        # Log specifico prima del blocco condizionale per i campi ACTIVITY
        logger.info(f"[UDAContentSerializer.validate] Checking condition for ACTIVITY fields. Current content_type: '{content_type}'. 'activity_description' in data: {'activity_description' in data}")

        if content_type != 'ACTIVITY':
            logger.info(f"[UDAContentSerializer.validate] Condition content_type != 'ACTIVITY' is TRUE. Popping ACTIVITY fields.")
            data.pop('activity_title', None)
            if 'activity_description' in data:
                logger.info(f"[UDAContentSerializer.validate] Popping 'activity_description'. Current data: {data}")
                data.pop('activity_description', None)
                logger.info(f"[UDAContentSerializer.validate] Data after popping 'activity_description': {data}")
            else:
                logger.info(f"[UDAContentSerializer.validate] 'activity_description' not in data to pop for ACTIVITY block.")
            data.pop('activity_attachment_url', None)
            data.pop('activity_completed', None)
        else:
            logger.info(f"[UDAContentSerializer.validate] Condition content_type != 'ACTIVITY' is FALSE. Skipping pop for ACTIVITY fields.")
            # teacher_marked_completed è applicabile a tutti i tipi di UDAContent, quindi non lo rimuoviamo qui.
        
        logger.info(f"[UDAContentSerializer.validate] Output data after validation logic: {data}")
        return data

    def validate_activity_attachment_url(self, value):
        # 'value' è il risultato di LenientFileField.to_internal_value()
        # Può essere UploadedFile, None, False, o una stringa URL.
        logger.info(f"-------------------- [validate_activity_attachment_url] START --------------------")
        logger.info(f"[validate_activity_attachment_url] Received value: '{str(value)[:200]}', type: {type(value)}")
        logger.info(f"[validate_activity_attachment_url] Initial self.instance: {self.instance}")
        logger.info(f"[validate_activity_attachment_url] self.initial_data: {str(getattr(self, 'initial_data', 'N/A'))[:200]}")
        logger.info(f"[validate_activity_attachment_url] self.partial: {getattr(self, 'partial', 'N/A')}")

        if isinstance(value, str): # È una stringa URL
            current_instance = self.instance
            content_id_from_initial_data = None

            # Controlla se initial_data è un dizionario prima di tentare .get('id')
            initial_data_dict = getattr(self, 'initial_data', None)
            if isinstance(initial_data_dict, dict):
                content_id_from_initial_data = initial_data_dict.get('id')

            # Se self.instance è None, ma abbiamo un ID nei dati iniziali (suggerendo un aggiornamento nested)
            # e stiamo facendo una PATCH (self.partial è True), proviamo a caricare l'istanza.
            if current_instance is None and content_id_from_initial_data is not None and getattr(self, 'partial', False):
                logger.info(f"[validate_activity_attachment_url] self.instance is None, but found id {content_id_from_initial_data} in initial_data during a partial update. Attempting to fetch instance.")
                try:
                    current_instance = UDAContent.objects.get(pk=content_id_from_initial_data)
                    logger.info(f"[validate_activity_attachment_url] Fetched instance: {current_instance}")
                except UDAContent.DoesNotExist:
                    logger.warning(f"[validate_activity_attachment_url] UDAContent with id {content_id_from_initial_data} not found.")
                    # current_instance rimane None, la logica successiva gestirà questo come una creazione o errore.
            
            instance_has_attachment = False
            existing_attachment_fieldfile = None

            if current_instance: # Usa l'istanza (originale o appena recuperata)
                logger.info(f"[validate_activity_attachment_url] current_instance.pk: {getattr(current_instance, 'pk', 'N/A')}")
                existing_attachment_fieldfile = getattr(current_instance, 'activity_attachment_url', None)
                logger.info(f"[validate_activity_attachment_url] current_instance.activity_attachment_url (FieldFile object): {existing_attachment_fieldfile}")
                if existing_attachment_fieldfile and existing_attachment_fieldfile.name:
                    instance_has_attachment = True
                    logger.info(f"[validate_activity_attachment_url] Instance has existing attachment. Name: '{existing_attachment_fieldfile.name}'")
                    # Log dell'URL dell'allegato esistente, se possibile
                    try:
                        logger.info(f"[validate_activity_attachment_url] Instance attachment URL: '{existing_attachment_fieldfile.url}'")
                    except Exception as e_url:
                        logger.warning(f"[validate_activity_attachment_url] Could not get .url for existing attachment on current_instance: {e_url}")
                else:
                    logger.info(f"[validate_activity_attachment_url] current_instance has no attachment or attachment name is empty.")
            else:
                logger.info(f"[validate_activity_attachment_url] current_instance is None (even after attempting fetch).")

            if instance_has_attachment: # L'istanza (recuperata o originale) ha un allegato
                # existing_attachment_fieldfile è il FieldFile dell'allegato esistente
                existing_file_name = existing_attachment_fieldfile.name
                
                media_url = getattr(settings, 'MEDIA_URL', '/media/')
                
                normalized_input_path = value
                if normalized_input_path.startswith(media_url):
                    normalized_input_path = normalized_input_path[len(media_url):]
                
                normalized_input_path = normalized_input_path.lstrip('/')
                normalized_existing_file_name = existing_file_name.lstrip('/')

                logger.info(f"[validate_activity_attachment_url] Comparing normalized input path '{normalized_input_path}' with existing file name '{normalized_existing_file_name}' (original input: '{value}', MEDIA_URL: '{media_url}')")

                if normalized_input_path == normalized_existing_file_name:
                    logger.info(f"[validate_activity_attachment_url] Paths match. Returning existing FieldFile to indicate no change.")
                    # Restituisce il FieldFile dall'istanza corrente (recuperata o originale)
                    return existing_attachment_fieldfile
                else:
                    logger.warning(f"Normalized input path '{normalized_input_path}' (from input '{value}') does not match existing file name '{normalized_existing_file_name}'. Validation failed.")
                    # Usiamo un messaggio di errore più specifico o quello standard del campo
                    # Per coerenza con l'errore originale, potremmo usare 'invalid_file' se disponibile, o 'invalid'
                    error_message = self.fields['activity_attachment_url'].error_messages.get('invalid_file', self.fields['activity_attachment_url'].error_messages['invalid'])
                    raise serializers.ValidationError(error_message)
            else:
                # Nessuna istanza valida con allegato preesistente trovata (o l'istanza è nuova),
                # ma abbiamo ricevuto una stringa URL.
                # Tentiamo di risolvere l'URL in un percorso relativo a MEDIA_ROOT.
                media_url_setting = getattr(settings, 'MEDIA_URL', '/media/')
                if not isinstance(media_url_setting, str) or not media_url_setting:
                    media_url_setting = '/media/' # Default robusto
                
                # Normalizza media_url_setting per iniziare e finire con '/' se non è solo '/'
                if not media_url_setting.startswith('/'):
                    media_url_setting = '/' + media_url_setting
                if not media_url_setting.endswith('/') and len(media_url_setting) > 1:
                    media_url_setting += '/'

                path_to_assign = None

                if value.startswith('http://') or value.startswith('https://'):
                    parsed_url = urlparse(value)
                    path_from_url = parsed_url.path # es. '/media/uda_attachments/file.pdf'
                    if path_from_url.startswith(media_url_setting):
                        path_to_assign = path_from_url[len(media_url_setting):] # es. 'uda_attachments/file.pdf'
                    else:
                        logger.warning(f"URL '{value}' path part '{path_from_url}' does not start with MEDIA_URL '{media_url_setting}'.")
                        raise serializers.ValidationError(f"Attachment URL does not match the expected media path structure (MEDIA_URL: {media_url_setting}).")
                elif value.startswith(media_url_setting): # URL relativo al dominio, es. /media/file.pdf
                    path_to_assign = value[len(media_url_setting):]
                elif not value.startswith('/') and ('/' in value or '.' in value): # Percorso presunto relativo, es. uda_attachments/file.pdf
                    # Questa condizione è per i percorsi che non iniziano con '/' ma sembrano percorsi di file
                    path_to_assign = value
                else:
                    logger.warning(f"Value '{value}' is not a recognized URL or relative path for an attachment.")
                    raise serializers.ValidationError("Invalid format for attachment path/URL.")

                if path_to_assign:
                    # path_to_assign è ora un percorso relativo a MEDIA_ROOT.
                    # Django FileField si aspetta questo tipo di stringa per l'assegnazione.
                    # Non è strettamente necessario verificare l'esistenza del file qui,
                    # poiché il sistema di storage di Django lo gestirà.
                    # Se il file non esiste a quel percorso, l'assegnazione al modello fallirà.
                    logger.info(f"Attachment URL/path '{value}' resolved to relative path '{path_to_assign}' for assignment.")
                    return path_to_assign # Restituisce il percorso relativo per l'assegnazione al FileField
                else:
                    # Questo non dovrebbe essere raggiunto se la logica sopra è completa, ma per sicurezza.
                    pk_for_log = getattr(current_instance, 'pk', 'N/A')
                    if current_instance is None and content_id_from_initial_data is not None:
                         pk_for_log = f"N/A (initial_data id: {content_id_from_initial_data})"
                    logger.warning(f"Instance (PK: {pk_for_log}) has no pre-existing attachment, and failed to resolve string URL/path '{value}' to a relative path.")
                    raise serializers.ValidationError("Cannot assign attachment from URL/path string: failed to resolve to a relative file path.")
            logger.info(f"-------------------- [validate_activity_attachment_url] END (string URL/path handled) --------------------")
        
        logger.info(f"-------------------- [validate_activity_attachment_url] END (value not a string or already returned) --------------------")
        return value # Per UploadedFile, None, False (valori che LenientFileField potrebbe passare direttamente)

    def update(self, instance, validated_data):
        # Assicurati che logger sia accessibile qui. Se definito a livello di modulo, è ok.
        # Se no: import logging; logger = logging.getLogger(__name__)
        logger.info(f"[UDAContentSerializer.update] Called for instance ID: {instance.pk if instance else 'None'}")
        logger.info(f"[UDAContentSerializer.update] Instance activity_description BEFORE super().update: '{instance.activity_description if instance else 'N/A'}'")
        logger.info(f"[UDAContentSerializer.update] Validated_data: {validated_data}")

        # Chiamata al metodo update della classe base (ModelSerializer)
        updated_instance = super().update(instance, validated_data)

        logger.info(f"[UDAContentSerializer.update] Instance activity_description AFTER super().update: '{updated_instance.activity_description if updated_instance else 'N/A'}'")
        logger.info(f"[UDAContentSerializer.update] Update complete for instance ID: {updated_instance.pk if updated_instance else 'None'}")
        return updated_instance

class UDASerializer(serializers.ModelSerializer):
   contents = UDAContentSerializer(many=True, required=False)
   # topics = TopicSerializer(many=True, read_only=True) # Esempio
   topic_ids = serializers.PrimaryKeyRelatedField(
       queryset=Topic.objects.all(),
       many=True,
       # write_only=True, # Rimosso per includere nella lettura
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
       # write_only=True, # Rimosso per includerlo nella lettura
       required=False, # Come da modello UDA, course è opzionale
       allow_null=True
   )
   # Forniamo campi separati per nome corso e autore per la lettura
   course_name = serializers.CharField(source='course.name', read_only=True, allow_null=True)
   course_teacher_username = serializers.CharField(source='course.teacher.username', read_only=True, allow_null=True)

   subject_ids = serializers.PrimaryKeyRelatedField(
       queryset=Subject.objects.all(),
       many=True,
       # write_only=True, # Rimosso per includere nella lettura
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
           'course_id', 'course_name', 'course_teacher_username', 'order_in_course', # Modificato da course_display
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
                   'estimated_hours': template_content.estimated_hours, # Aggiunto
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
       subject_data = validated_data.pop('subjects', None)

       # Aggiorna i campi dell'istanza UDA principale
       instance.title = validated_data.get('title', instance.title)
       instance.description = validated_data.get('description', instance.description)
       instance.start_date = validated_data.get('start_date', instance.start_date)
       instance.end_date = validated_data.get('end_date', instance.end_date)
       instance.status = validated_data.get('status', instance.status)
       instance.course = validated_data.get('course', instance.course)
       instance.order_in_course = validated_data.get('order_in_course', instance.order_in_course)
       # source_template non è modificabile dopo la creazione
       instance.save()

       if topics_data is not None:
           instance.topics.set(topics_data)
       
       if subject_data is not None:
           instance.subjects.set(subject_data)

       if contents_data is not None:
           existing_contents_map = {content.id: content for content in instance.contents.all()}
           processed_existing_content_ids = set()

           for item_data in contents_data:
               item_id = item_data.get('id', None)
               content_serializer_context = self.context

               if item_id is not None and item_id in existing_contents_map:
                   content_instance = existing_contents_map[item_id]
                   processed_existing_content_ids.add(item_id)
                   
                   logger.info(f"[UDASerializer.update] Updating existing UDAContent (ID: {item_id}) for UDA (ID: {instance.id})")
                   content_serializer = UDAContentSerializer(
                       content_instance, data=item_data, partial=True, context=content_serializer_context
                   )
                   if content_serializer.is_valid(raise_exception=True):
                       content_serializer.save()
               else:
                   # Nessun ID fornito o ID non corrispondente a un contenuto esistente.
                   # Potrebbe essere una creazione o un aggiornamento di un elemento esistente
                   # identificato tramite URL dell'allegato (se il frontend non invia l'ID).
                   
                   # Rimuovi 'id' se presente, dato che potrebbe essere un ID non valido o per creazione
                   potential_invalid_id = item_data.pop('id', None)
                   if potential_invalid_id is not None:
                       logger.info(f"[UDASerializer.update] Popped id '{potential_invalid_id}' from item_data as it was not in existing_contents_map or was None.")

                   found_match_by_url = False
                   attachment_url_from_item = item_data.get('activity_attachment_url')

                   if isinstance(attachment_url_from_item, str) and item_data.get('content_type') == 'ACTIVITY':
                       logger.info(f"[UDASerializer.update] No ID for item, but activity_attachment_url string found: {attachment_url_from_item}. Trying to match with existing unprocessed contents for UDA (ID: {instance.id}).")
                       
                       # Normalizza l'URL in arrivo
                       media_url_prefix = getattr(settings, 'MEDIA_URL', '/media/')
                       normalized_input_url = attachment_url_from_item
                       if normalized_input_url.startswith(media_url_prefix):
                           normalized_input_url = normalized_input_url[len(media_url_prefix):]
                       normalized_input_url = normalized_input_url.lstrip('/')

                       for existing_id, existing_content_instance in existing_contents_map.items():
                           if existing_id in processed_existing_content_ids:
                               continue # Già processato

                           if existing_content_instance.content_type == 'ACTIVITY' and existing_content_instance.activity_attachment_url:
                               existing_file_name = existing_content_instance.activity_attachment_url.name
                               normalized_existing_file_name = existing_file_name.lstrip('/')
                               
                               logger.debug(f"[UDASerializer.update] Comparing normalized input URL '{normalized_input_url}' with existing file name '{normalized_existing_file_name}' for content ID {existing_id}")
                               if normalized_input_url == normalized_existing_file_name:
                                   logger.info(f"[UDASerializer.update] Matched by URL. Updating existing UDAContent (ID: {existing_id}) for UDA (ID: {instance.id}) using URL match.")
                                   processed_existing_content_ids.add(existing_id)
                                   
                                   content_serializer = UDAContentSerializer(
                                       existing_content_instance, data=item_data, partial=True, context=content_serializer_context
                                   )
                                   if content_serializer.is_valid(raise_exception=True):
                                       content_serializer.save()
                                   found_match_by_url = True
                                   break
                       if not found_match_by_url:
                           logger.info(f"[UDASerializer.update] No match by URL found for '{attachment_url_from_item}'. Proceeding to create new content for UDA (ID: {instance.id}).")

                   if not found_match_by_url:
                       logger.info(f"[UDASerializer.update] Creating new UDAContent for UDA (ID: {instance.id}) with data: {item_data}")
                       content_serializer = UDAContentSerializer(
                           data=item_data, context=content_serializer_context
                       )
                       if content_serializer.is_valid(raise_exception=True):
                           content_serializer.save(uda=instance)
           
           # Elimina i contenuti che erano presenti ma non sono stati inviati/abbinati nell'aggiornamento
           ids_to_delete = set(existing_contents_map.keys()) - processed_existing_content_ids
           if ids_to_delete:
               logger.info(f"[UDASerializer.update] Deleting UDAContents with IDs: {ids_to_delete} from UDA (ID: {instance.id}) as they were not in the update payload.")
               UDAContent.objects.filter(id__in=ids_to_delete, uda=instance).delete()
       
       return instance