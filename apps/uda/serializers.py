from rest_framework import serializers
from django.conf import settings
import logging
from urllib.parse import urlparse
from .models import (
    UDATemplate, UDATemplateTopic, UDATemplateContent,
    UDA, UDATopic, UDAContent, Course, UDASubject,
    CourseGroup, UdaGroup
)
from lezioni.models import Topic, Subject, Lesson
from apps.education.models import QuizTemplate
from django.core.files.uploadedfile import UploadedFile
import logging

logger = logging.getLogger(__name__)

class CourseGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseGroup
        fields = ['id', 'name', 'teacher']
        read_only_fields = ['id', 'teacher']

class UdaGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UdaGroup
        fields = ['id', 'name', 'teacher']
        read_only_fields = ['id', 'teacher']


class CourseSerializer(serializers.ModelSerializer):
    group = CourseGroupSerializer(read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=CourseGroup.objects.all(),
        source='group',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Course
        fields = [
            'id', 'teacher', 'teacher_username', 'name', 'description',
            'created_at', 'updated_at', 'group', 'group_id'
        ]
        read_only_fields = ['id', 'teacher', 'created_at', 'updated_at', 'teacher_username', 'group']

    teacher_username = serializers.CharField(source='teacher.username', read_only=True)

    def create(self, validated_data):
        validated_data['teacher'] = self.context['request'].user
        group = validated_data.get('group')
        if group and group.teacher != validated_data['teacher']:
            raise serializers.ValidationError("Cannot assign to a group that does not belong to the teacher.")
        return super().create(validated_data)

    def update(self, instance, validated_data):
        group = validated_data.get('group')
        if group and group.teacher != instance.teacher:
            raise serializers.ValidationError("Cannot assign to a group that does not belong to the teacher.")
        return super().update(instance, validated_data)

class UDATemplateTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = UDATemplateTopic
        fields = ['topic']

class LessonIdField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        if 'queryset' not in kwargs:
            kwargs['queryset'] = Lesson.objects.all()
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        pk_value = None
        if isinstance(data, Lesson):
            pk_value = data.pk
        elif isinstance(data, dict) and 'id' in data:
            pk_value = data.get('id')
        else:
            pk_value = data
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
    lesson = LessonIdField(allow_null=True, required=False)

    class Meta:
        model = UDATemplateContent
        fields = [
            'id', 'content_type', 'lesson', 'quiz_template',
            'note_template_title', 'note_template_content',
            'activity_template_title', 'activity_template_description',
            'order', 'estimated_hours'
        ]

    def validate(self, data):
        content_type = data.get('content_type')
        lesson = data.get('lesson')
        quiz_template = data.get('quiz_template')
        note_template_title = data.get('note_template_title')
        activity_template_title = data.get('activity_template_title')

        if content_type == 'LESSON' and not lesson:
            raise serializers.ValidationError({'lesson': "Lesson is required for content type LESSON."})
        if content_type == 'QUIZ_TEMPLATE' and not quiz_template:
            raise serializers.ValidationError({'quiz_template': "Quiz template is required for content type QUIZ_TEMPLATE."})
        if content_type == 'NOTE_TEMPLATE' and not note_template_title:
            raise serializers.ValidationError({'note_template_title': "Note template title is required for content type NOTE_TEMPLATE."})
        if content_type == 'ACTIVITY_TEMPLATE' and not activity_template_title:
            raise serializers.ValidationError({'activity_template_title': "Activity template title is required for content type ACTIVITY_TEMPLATE."})
        
        if content_type != 'LESSON':
            data.pop('lesson', None)
        if content_type != 'QUIZ_TEMPLATE':
            data.pop('quiz_template', None)
        if content_type != 'NOTE_TEMPLATE':
            data.pop('note_template_title', None)
            data.pop('note_template_content', None)
        if content_type != 'ACTIVITY_TEMPLATE':
            data.pop('activity_template_title', None)
            data.pop('activity_template_description', None)
            
        return data

class UDATemplateSerializer(serializers.ModelSerializer):
    contents = UDATemplateContentSerializer(many=True, required=False)
    topic_ids = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        many=True,
        write_only=True,
        source='topics',
        required=False
    )
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
        topics_data = validated_data.pop('topics', [])
        validated_data['teacher'] = self.context['request'].user
        template = UDATemplate.objects.create(**validated_data)
        if topics_data:
             template.topics.set(topics_data)
        for content_data in contents_data:
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
            instance.contents.all().delete()
            for content_data in contents_data:
                UDATemplateContent.objects.create(uda_template=instance, **content_data)
        return instance

class UDATopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = UDATopic
        fields = ['topic']

class UDAContentSerializer(serializers.ModelSerializer):
    lesson = LessonIdField(allow_null=True, required=False, queryset=Lesson.objects.all())
    quiz_template = QuizTemplateIdField(allow_null=True, required=False)

    lesson_title = serializers.SerializerMethodField()
    quiz_title = serializers.SerializerMethodField()

    class Meta:
        model = UDAContent
        fields = [
            'id', 'content_type', 'lesson', 'quiz_template',
            'note_title', 'note_content',
            'activity_title', 'activity_description', 'activity_completed',
            'teacher_marked_completed',
            'order', 'estimated_hours', 'actual_hours',
            'lesson_title', 'quiz_title'
        ]

    def get_lesson_title(self, obj):
        if obj.content_type == 'LESSON' and obj.lesson:
            return obj.lesson.title
        return None

    def get_quiz_title(self, obj):
        if obj.content_type == 'QUIZ' and obj.quiz_template:
            return obj.quiz_template.title
        return None

    def validate(self, data):
        content_type = data.get('content_type')
        if self.instance and 'content_type' not in data and hasattr(self.instance, 'content_type'):
            content_type = self.instance.content_type
        
        lesson = data.get('lesson')
        quiz_template = data.get('quiz_template')
        note_title = data.get('note_title')
        activity_title = data.get('activity_title')

        if content_type == 'LESSON' and not lesson:
            raise serializers.ValidationError({'lesson': "Lesson is required for content type LESSON."})
        if content_type == 'QUIZ' and not quiz_template:
            raise serializers.ValidationError({'quiz_template': "Quiz template is required for content type QUIZ."})
        if content_type == 'NOTE':
            if not self.instance and not data.get('note_title'):
                raise serializers.ValidationError({'note_title': "Note title is required for content type NOTE."})
            elif self.instance and 'note_title' in data and not data.get('note_title'):
                raise serializers.ValidationError({'note_title': "Note title cannot be empty if provided for content type NOTE."})

        if content_type == 'ACTIVITY':
            if not self.instance and not data.get('activity_title'):
                raise serializers.ValidationError({'activity_title': "Activity title is required for content type ACTIVITY."})
            elif self.instance and 'activity_title' in data and not data.get('activity_title'):
                raise serializers.ValidationError({'activity_title': "Activity title cannot be empty if provided for content type ACTIVITY."})

        if content_type != 'LESSON':
            data.pop('lesson', None)
        if content_type != 'QUIZ':
            data.pop('quiz_template', None)
        if content_type != 'NOTE':
            data.pop('note_title', None)
            data.pop('note_content', None)
        
        if content_type != 'ACTIVITY':
            data.pop('activity_title', None)
            data.pop('activity_description', None)
            data.pop('activity_completed', None)
        
        return data

    def create(self, validated_data):
        lesson = validated_data.get('lesson')
        if lesson and lesson.estimated_hours is not None and validated_data.get('content_type') == 'LESSON':
            if 'estimated_hours' not in validated_data or validated_data.get('estimated_hours') is None:
                validated_data['estimated_hours'] = lesson.estimated_hours
        return super().create(validated_data)

    def update(self, instance, validated_data):
        lesson = validated_data.get('lesson')
        if lesson and lesson.estimated_hours is not None and validated_data.get('content_type') == 'LESSON':
            if 'estimated_hours' not in validated_data or validated_data.get('estimated_hours') is None:
                validated_data['estimated_hours'] = lesson.estimated_hours
        

        return super().update(instance, validated_data)


class UDASubjectSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='subject.id')
    name = serializers.CharField(source='subject.name')

    class Meta:
        model = UDASubject
        fields = ['id', 'name']

class UDASerializer(serializers.ModelSerializer):
    group = UdaGroupSerializer(read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=UdaGroup.objects.all(),
        source='group',
        write_only=True,
        required=False,
        allow_null=True
    )
    contents = UDAContentSerializer(many=True, required=False)
    subjects = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(),
        many=True,
        required=False
    )
    topics = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        many=True,
        required=False
    )
    total_estimated_hours = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    total_lesson_estimated_hours = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)
    lesson_count = serializers.IntegerField(read_only=True)
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source='course',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = UDA
        fields = [
            'id', 'teacher', 'source_template', 'title', 'description',
            'knowledge_html', 'skills_html', 'competences_html', 'prerequisites_html',
            'is_civic_education', 'didactic_strategies_html', 'materials_tools_html',
            'assessment_type_html', 'evaluation_html', 'key_and_citizenship_competences_html',
            'other_involved_subjects_text', 'export_specific_annotations_html',
            'start_date', 'end_date', 'subjects', 'topics',
            'course', 'course_id', 'order_in_course', 'status', 'group', 'group_id',
            'created_at', 'updated_at', 'contents', 'total_estimated_hours',
            'total_lesson_estimated_hours', 'lesson_count'
        ]
        read_only_fields = ['id', 'teacher', 'created_at', 'updated_at']

    def create(self, validated_data):
        contents_data = validated_data.pop('contents', [])
        subjects_data = validated_data.pop('subjects', None)
        topics_data = validated_data.pop('topics', None)
        
        validated_data['teacher'] = self.context['request'].user
        
        course = validated_data.pop('course', None)
        uda = UDA.objects.create(course=course, **validated_data)
        
        if subjects_data is not None:
            uda.subjects.set(subjects_data)
        if topics_data is not None:
            uda.topics.set(topics_data)

        for content_data in contents_data:
            UDAContent.objects.create(uda=uda, **content_data)
            
        return uda

    def update(self, instance, validated_data):
        contents_data = validated_data.pop('contents', None)
        subjects_data = validated_data.pop('subjects', None)
        topics_data = validated_data.pop('topics', None)

        # instance = super().update(instance, validated_data)
        # La gestione manuale del corso non è necessaria, super().update gestisce l'assegnazione.
        instance = super().update(instance, validated_data)

        if subjects_data is not None:
            instance.subjects.set(subjects_data)
        if topics_data is not None:
            instance.topics.set(topics_data)

        if contents_data is not None:
            content_mapping = {item.id: item for item in instance.contents.all()}
            
            for content_data in contents_data:
                content_id = content_data.get('id')
                content = content_mapping.get(content_id)
                
                if content: # Aggiorna contenuto esistente
                    # Rimuovi l'ID dai dati per evitare problemi con il serializer
                    content_data.pop('id', None)
                    # Crea un'istanza del serializer per l'aggiornamento
                    content_serializer = UDAContentSerializer(
                        instance=content, 
                        data=content_data, 
                        partial=True, # Usa partial=True per aggiornamenti parziali
                        context=self.context
                    )
                    if content_serializer.is_valid(raise_exception=True):
                        content_serializer.save()
                else: # Crea nuovo contenuto
                    UDAContent.objects.create(uda=instance, **content_data)

            # Opzionale: rimuovi i contenuti che non sono più presenti nei dati inviati
            sent_content_ids = {item.get('id') for item in contents_data if item.get('id')}
            for content_id, content_item in content_mapping.items():
                if content_id not in sent_content_ids:
                    content_item.delete()

        return instance