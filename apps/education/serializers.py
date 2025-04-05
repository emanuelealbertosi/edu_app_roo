import logging
import io
import re
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
import markdown as md_parser # Rinominato per evitare conflitti
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.core.files.uploadedfile import UploadedFile

from .models import (
    QuizTemplate, QuestionTemplate, AnswerOptionTemplate,
    Quiz, Question, AnswerOption, Pathway, PathwayQuiz,
    QuizAttempt, StudentAnswer, PathwayProgress, QuestionType,
    QuizAssignment, PathwayAssignment, # Importa Assignment mancanti
    PathwayTemplate, PathwayQuizTemplate # Importa i nuovi modelli Template
)
from apps.users.serializers import UserSerializer, StudentSerializer # Per info utente/studente
from apps.users.models import User, Student # Aggiunto per associazione docente e studente
from .models import QuizAttempt # Assicurati che QuizAttempt sia importato

logger = logging.getLogger(__name__)

# --- Template Serializers ---

class AnswerOptionTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOptionTemplate
        fields = ['id', 'text', 'is_correct', 'order']


class QuestionTemplateSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionTemplateSerializer(
        many=True,
        source='answer_option_templates', # Usa related_name
        read_only=True
    )
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)

    class Meta:
        model = QuestionTemplate
        fields = [
            'id', 'quiz_template', 'text', 'question_type', 'question_type_display',
            'order', 'metadata', 'answer_options'
        ]
        read_only_fields = ['quiz_template']


class QuizTemplateSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(source='admin.username', read_only=True, allow_null=True)
    teacher_username = serializers.CharField(source='teacher.username', read_only=True, allow_null=True)

    class Meta:
        model = QuizTemplate
        fields = [
            'id', 'admin', 'admin_username', 'teacher', 'teacher_username',
            'title', 'description', 'metadata', 'created_at'
        ]
        read_only_fields = ['admin', 'admin_username', 'teacher', 'teacher_username', 'created_at']

class PathwayQuizTemplateSerializer(serializers.ModelSerializer):
    """ Serializer per la relazione M2M PathwayTemplate-QuizTemplate. """
    quiz_template_title = serializers.CharField(source='quiz_template.title', read_only=True)
    quiz_template_id = serializers.IntegerField(source='quiz_template.id', read_only=True)

    class Meta:
        model = PathwayQuizTemplate
        fields = ['id', 'quiz_template_id', 'quiz_template_title', 'order']


class PathwayTemplateSerializer(serializers.ModelSerializer):
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    quiz_template_details = PathwayQuizTemplateSerializer(source='pathwayquiztemplate_set', many=True, read_only=True)

    class Meta:
        model = PathwayTemplate
        fields = [
            'id', 'teacher', 'teacher_username', 'title', 'description',
            'metadata', 'created_at', 'quiz_template_details'
        ]
        read_only_fields = ['teacher', 'teacher_username', 'created_at', 'quiz_template_details']



# --- Concrete Serializers ---

class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ['id', 'text', 'is_correct', 'order']


class QuestionSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionSerializer(
        many=True,
        read_only=True
    )
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)

    class Meta:
        model = Question
        fields = [
            'id', 'quiz', 'text', 'question_type', 'question_type_display',
            'order', 'metadata', 'answer_options'
        ]
        read_only_fields = ['quiz']


class QuizSerializer(serializers.ModelSerializer):
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id', 'teacher', 'teacher_username', 'source_template', 'title', 'description',
            'metadata', 'created_at', 'available_from', 'available_until'
        ]
        read_only_fields = ['teacher', 'teacher_username', 'created_at']
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True, 'allow_null': True}
        }

# --- Pathway Serializers (Definiti prima di quelli che li usano) ---

class PathwayQuizSerializer(serializers.ModelSerializer):
    """ Serializer per la relazione M2M Pathway-Quiz (usato nested in Pathway). """
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    quiz_id = serializers.IntegerField(source='quiz.id', read_only=True)

    class Meta:
        model = PathwayQuiz
        fields = ['id', 'quiz_id', 'quiz_title', 'order']


class PathwaySerializer(serializers.ModelSerializer):
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    quiz_details = PathwayQuizSerializer(source='pathwayquiz_set', many=True, read_only=True)

    class Meta:
        model = Pathway
        fields = [
            'id', 'teacher', 'teacher_username', 'source_template', 'title', 'description',
            'metadata', 'created_at', 'quiz_details'
        ]
        read_only_fields = ['teacher', 'teacher_username', 'created_at', 'quiz_details']


# --- Serializer per Upload Quiz ---

ALLOWED_UPLOAD_EXTENSIONS = ['.pdf', '.docx', '.md']

class QuizUploadSerializer(serializers.Serializer):
    """
    Serializer per gestire l'upload di file (PDF, DOCX, MD) per creare quiz.
    """
    file = serializers.FileField(required=True, help_text="File del quiz (.pdf, .docx, .md)")
    title = serializers.CharField(max_length=255, required=True, help_text="Titolo del nuovo quiz")

    def validate_file(self, value: UploadedFile):
        if not hasattr(value, 'name') or not value.name:
             raise ValidationError("Nome del file mancante o non valido.")
        parts = value.name.split('.')
        if len(parts) < 2:
            raise ValidationError("Il file non ha un'estensione.")
        ext = '.' + parts[-1].lower()
        if ext not in ALLOWED_UPLOAD_EXTENSIONS:
            raise ValidationError(f"Tipo di file non supportato: {ext}. Sono permessi: {', '.join(ALLOWED_UPLOAD_EXTENSIONS)}")
        return value

    def _extract_text_from_pdf(self, file_obj: io.BytesIO) -> str:
        try:
            reader = PdfReader(file_obj)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            if not text:
                 logger.warning("Nessun testo estratto dal PDF.")
            return text
        except Exception as e:
            logger.error(f"Errore estrazione testo PDF: {e}", exc_info=True)
            raise ValidationError(f"Impossibile leggere il file PDF. Errore: {e}")

    def _extract_text_from_docx(self, file_obj: io.BytesIO) -> str:
        try:
            document = DocxDocument(file_obj)
            text = "\n".join([para.text for para in document.paragraphs if para.text])
            if not text:
                 logger.warning("Nessun testo estratto dal DOCX.")
            return text
        except Exception as e:
            logger.error(f"Errore estrazione testo DOCX: {e}", exc_info=True)
            raise ValidationError(f"Impossibile leggere il file DOCX. Errore: {e}")

    def _extract_text_from_md(self, file_obj: io.BytesIO) -> str:
        try:
            md_content = file_obj.read().decode('utf-8')
            html = md_parser.markdown(md_content)
            text = re.sub('<[^<]+?>', '', html).strip()
            if not text:
                 logger.warning("Nessun testo estratto dal Markdown.")
            return text
        except Exception as e:
            logger.error(f"Errore estrazione testo Markdown: {e}", exc_info=True)
            raise ValidationError(f"Impossibile leggere il file Markdown. Errore: {e}")

    def _parse_quiz_text(self, text: str) -> list[dict]:
        questions = []
        current_question = None
        question_start_re = re.compile(r"^\s*(?:(\d+)\s*[.)])?\s*(.*)", re.MULTILINE)
        option_re = re.compile(r"^\s*([A-Z])\s*[.)]\s*(.*)", re.MULTILINE)
        empty_line_re = re.compile(r"^\s*$")
        lines = text.splitlines()
        question_counter = 0

        for line in lines:
            if empty_line_re.match(line):
                continue

            line_stripped = line.strip()
            question_match = question_start_re.match(line)
            option_match = option_re.match(line_stripped)
            is_likely_question_start = question_match and question_match.group(1)
            is_likely_option = option_match

            if is_likely_question_start:
                if current_question:
                    questions.append(current_question)
                question_number = int(question_match.group(1))
                question_text = question_match.group(2).strip()
                question_counter = question_number
                current_question = {
                    "text": question_text, "order": question_number, "options": [],
                    "type": QuestionType.MULTIPLE_CHOICE_SINGLE
                }
            elif is_likely_option and current_question:
                option_letter = option_match.group(1)
                option_text = option_match.group(2).strip()
                current_question["options"].append({
                    "text": option_text, "order": len(current_question["options"]) + 1, "is_correct": False
                })
            elif current_question:
                 if current_question["options"] and not is_likely_question_start:
                     current_question["options"][-1]["text"] += " " + line_stripped
                 else:
                     if current_question["options"] or not current_question["text"]:
                         if current_question["text"]:
                             questions.append(current_question)
                         question_counter += 1
                         current_question = {
                             "text": line_stripped, "order": question_counter, "options": [],
                             "type": QuestionType.MULTIPLE_CHOICE_SINGLE
                         }
                     else:
                        current_question["text"] += " " + line_stripped
            elif not current_question and line_stripped:
                 question_counter += 1
                 current_question = {
                     "text": line_stripped, "order": question_counter, "options": [],
                     "type": QuestionType.MULTIPLE_CHOICE_SINGLE
                 }

        if current_question:
            questions.append(current_question)

        questions = [q for q in questions if q.get("text")]
        questions.sort(key=lambda q: q.get("order", float('inf')))
        for i, q in enumerate(questions):
            q["order"] = i + 1
            if not q["options"]:
                q["type"] = QuestionType.OPEN_ANSWER_MANUAL

        if not questions:
             raise ValidationError("Nessuna domanda valida trovata nel file.")

        return questions


    @transaction.atomic
    def create(self, validated_data):
        uploaded_file: UploadedFile = validated_data['file']
        title = validated_data['title']
        teacher: User = self.context['request'].user

        file_content = io.BytesIO(uploaded_file.read())
        file_ext = '.' + uploaded_file.name.split('.')[-1].lower()

        text = ""
        try:
            if file_ext == '.pdf':
                text = self._extract_text_from_pdf(file_content)
            elif file_ext == '.docx':
                text = self._extract_text_from_docx(file_content)
            elif file_ext == '.md':
                text = self._extract_text_from_md(file_content)
            else:
                raise ValidationError("Tipo di file non gestito internamente.")
        except ValidationError as e:
             raise e
        except Exception as e:
             logger.error(f"Errore estrazione testo da {uploaded_file.name}: {e}", exc_info=True)
             raise ValidationError(f"Errore lettura file {file_ext}.")


        if not text or text.isspace():
             raise ValidationError(f"Contenuto testuale non valido da {uploaded_file.name}.")

        try:
            parsed_questions = self._parse_quiz_text(text)
        except ValidationError as e:
             raise e
        except Exception as e:
             logger.error(f"Errore parsing testo da {uploaded_file.name}: {e}", exc_info=True)
             raise ValidationError("Errore analisi contenuto file.")


        quiz = Quiz.objects.create(
            teacher=teacher,
            title=title,
            description=f"Quiz generato automaticamente da {uploaded_file.name}",
            metadata={
                'source_file': uploaded_file.name,
                'generation_method': 'auto_upload'
            }
        )

        questions_to_create = []
        options_to_create = []

        for q_data in parsed_questions:
            question = Question(
                quiz=quiz,
                text=q_data['text'],
                question_type=q_data['type'],
                order=q_data['order'],
                metadata={}
            )
            questions_to_create.append(question)

        created_questions = Question.objects.bulk_create(questions_to_create)
        question_map = {(q.text, q.order): q for q in created_questions}

        for q_data in parsed_questions:
             question_obj = question_map.get((q_data['text'], q_data['order']))
             if not question_obj:
                 logger.warning(f"Domanda '{q_data['text'][:50]}...' (ordine {q_data['order']}) non trovata dopo bulk_create.")
                 continue

             for opt_data in q_data['options']:
                 option = AnswerOption(
                     question=question_obj,
                     text=opt_data['text'],
                     is_correct=opt_data['is_correct'],
                     order=opt_data['order']
                 )
                 options_to_create.append(option)

        if options_to_create:
            AnswerOption.objects.bulk_create(options_to_create)

        logger.info(f"Creato Quiz '{quiz.title}' (ID: {quiz.id}) con {len(created_questions)} domande da {uploaded_file.name}")
        return QuizSerializer(quiz, context=self.context).data

# --- Serializer per Upload Quiz Template ---

class QuizTemplateUploadSerializer(serializers.Serializer):
    """
    Serializer per gestire l'upload di file (PDF, DOCX, MD) per creare QuizTemplate.
    """
    file = serializers.FileField(required=True, help_text="File del quiz template (.pdf, .docx, .md)")
    title = serializers.CharField(max_length=255, required=True, help_text="Titolo del nuovo quiz template")

    def validate_file(self, value: UploadedFile):
        if not hasattr(value, 'name') or not value.name:
             raise ValidationError("Nome del file mancante o non valido.")
        parts = value.name.split('.')
        if len(parts) < 2:
            raise ValidationError("Il file non ha un'estensione.")
        ext = '.' + parts[-1].lower()
        if ext not in ALLOWED_UPLOAD_EXTENSIONS:
            raise ValidationError(f"Tipo di file non supportato: {ext}. Sono permessi: {', '.join(ALLOWED_UPLOAD_EXTENSIONS)}")
        return value

    def _extract_text_from_pdf(self, file_obj: io.BytesIO) -> str:
        try:
            reader = PdfReader(file_obj)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            if not text:
                 logger.warning("Nessun testo estratto dal PDF (template).")
            return text
        except Exception as e:
            logger.error(f"Errore estrazione testo PDF (template): {e}", exc_info=True)
            raise ValidationError(f"Impossibile leggere il file PDF (template). Errore: {e}")

    def _extract_text_from_docx(self, file_obj: io.BytesIO) -> str:
        try:
            document = DocxDocument(file_obj)
            text = "\n".join([para.text for para in document.paragraphs if para.text])
            if not text:
                 logger.warning("Nessun testo estratto dal DOCX (template).")
            return text
        except Exception as e:
            logger.error(f"Errore estrazione testo DOCX (template): {e}", exc_info=True)
            raise ValidationError(f"Impossibile leggere il file DOCX (template). Errore: {e}")

    def _extract_text_from_md(self, file_obj: io.BytesIO) -> str:
        try:
            md_content = file_obj.read().decode('utf-8')
            html = md_parser.markdown(md_content)
            text = re.sub('<[^<]+?>', '', html).strip()
            if not text:
                 logger.warning("Nessun testo estratto dal Markdown (template).")
            return text
        except Exception as e:
            logger.error(f"Errore estrazione testo Markdown (template): {e}", exc_info=True)
            raise ValidationError(f"Impossibile leggere il file Markdown (template). Errore: {e}")

    def _parse_quiz_text(self, text: str) -> list[dict]:
        questions = []
        current_question = None
        question_start_re = re.compile(r"^\s*(?:(\d+)\s*[.)])?\s*(.*)", re.MULTILINE)
        option_re = re.compile(r"^\s*([A-Z])\s*[.)]\s*(.*)", re.MULTILINE)
        empty_line_re = re.compile(r"^\s*$")
        lines = text.splitlines()
        question_counter = 0

        for line in lines:
            if empty_line_re.match(line):
                continue

            line_stripped = line.strip()
            question_match = question_start_re.match(line)
            option_match = option_re.match(line_stripped)
            is_likely_question_start = question_match and question_match.group(1)
            is_likely_option = option_match

            if is_likely_question_start:
                if current_question:
                    questions.append(current_question)
                question_number = int(question_match.group(1))
                question_text = question_match.group(2).strip()
                question_counter = question_number
                current_question = {
                    "text": question_text, "order": question_number, "options": [],
                    "type": QuestionType.MULTIPLE_CHOICE_SINGLE
                }
            elif is_likely_option and current_question:
                option_letter = option_match.group(1)
                option_text = option_match.group(2).strip()
                current_question["options"].append({
                    "text": option_text, "order": len(current_question["options"]) + 1, "is_correct": False
                })
            elif current_question:
                 if current_question["options"] and not is_likely_question_start:
                     current_question["options"][-1]["text"] += " " + line_stripped
                 else:
                     if current_question["options"] or not current_question["text"]:
                         if current_question["text"]:
                             questions.append(current_question)
                         question_counter += 1
                         current_question = {
                             "text": line_stripped, "order": question_counter, "options": [],
                             "type": QuestionType.MULTIPLE_CHOICE_SINGLE
                         }
                     else:
                        current_question["text"] += " " + line_stripped
            elif not current_question and line_stripped:
                 question_counter += 1
                 current_question = {
                     "text": line_stripped, "order": question_counter, "options": [],
                     "type": QuestionType.MULTIPLE_CHOICE_SINGLE
                 }

        if current_question:
            questions.append(current_question)

        questions = [q for q in questions if q.get("text")]
        questions.sort(key=lambda q: q.get("order", float('inf')))
        for i, q in enumerate(questions):
            q["order"] = i + 1
            if not q["options"]:
                q["type"] = QuestionType.OPEN_ANSWER_MANUAL

        if not questions:
             raise ValidationError("Nessuna domanda valida trovata nel file (template). Verifica la formattazione.")

        return questions


    @transaction.atomic
    def create(self, validated_data):
        uploaded_file: UploadedFile = validated_data['file']
        title = validated_data['title']
        teacher: User = self.context['request'].user

        if not isinstance(teacher, User) or not teacher.is_teacher:
             raise ValidationError("Solo i docenti possono caricare template di quiz.")

        file_content = io.BytesIO(uploaded_file.read())
        file_ext = '.' + uploaded_file.name.split('.')[-1].lower()

        text = ""
        try:
            if file_ext == '.pdf':
                text = self._extract_text_from_pdf(file_content)
            elif file_ext == '.docx':
                text = self._extract_text_from_docx(file_content)
            elif file_ext == '.md':
                text = self._extract_text_from_md(file_content)
            else:
                raise ValidationError("Tipo di file non gestito internamente (template).")
        except ValidationError as e:
             raise e
        except Exception as e:
             logger.error(f"Errore estrazione testo (template) da {uploaded_file.name}: {e}", exc_info=True)
             raise ValidationError(f"Errore lettura file {file_ext} (template).")


        if not text or text.isspace():
             raise ValidationError(f"Contenuto testuale non valido da {uploaded_file.name} (template).")

        try:
            parsed_questions = self._parse_quiz_text(text)
        except ValidationError as e:
             raise e
        except Exception as e:
             logger.error(f"Errore parsing testo (template) da {uploaded_file.name}: {e}", exc_info=True)
             raise ValidationError("Errore analisi contenuto file (template).")


        quiz_template = QuizTemplate.objects.create(
            teacher=teacher,
            title=title,
            description=f"Template generato automaticamente da {uploaded_file.name}",
            metadata={
                'source_file': uploaded_file.name,
                'generation_method': 'auto_upload'
            }
        )

        questions_to_create = []
        options_to_create = []

        for q_data in parsed_questions:
            question_template = QuestionTemplate(
                quiz_template=quiz_template,
                text=q_data['text'],
                question_type=q_data['type'],
                order=q_data['order'],
                metadata={}
            )
            questions_to_create.append(question_template)

        created_question_templates = QuestionTemplate.objects.bulk_create(questions_to_create)
        question_template_map = {(qt.text, qt.order): qt for qt in created_question_templates}

        for q_data in parsed_questions:
             question_template_obj = question_template_map.get((q_data['text'], q_data['order']))
             if not question_template_obj:
                 logger.warning(f"Domanda template '{q_data['text'][:50]}...' (ordine {q_data['order']}) non trovata dopo bulk_create.")
                 continue

             for opt_data in q_data['options']:
                 option_template = AnswerOptionTemplate(
                     question_template=question_template_obj,
                     text=opt_data['text'],
                     is_correct=opt_data['is_correct'],
                     order=opt_data['order']
                 )
                 options_to_create.append(option_template)

        if options_to_create:
            AnswerOptionTemplate.objects.bulk_create(options_to_create)

        logger.info(f"Creato QuizTemplate '{quiz_template.title}' (ID: {quiz_template.id}) con {len(created_question_templates)} domande da {uploaded_file.name} per docente {teacher.id}")
        return QuizTemplateSerializer(quiz_template, context=self.context).data


# --- Serializers per Assegnazione ---

class QuizAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer per assegnare Quiz a Studenti. """
    # Dichiarazione esplicita dei campi per controllo in __init__
    quiz = serializers.PrimaryKeyRelatedField(
        queryset=Quiz.objects.all(),
        required=True, # Default, modificato in __init__
        allow_null=False # Default, modificato in __init__
    )
    student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.filter(is_active=True),
        required=True
    )
    quiz_template_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True,
        help_text="ID del QuizTemplate da cui creare e assegnare un nuovo Quiz."
    )
    # Campi read-only
    student_username = serializers.CharField(source='student.unique_identifier', read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        initial_data = kwargs.get('data', {})
        if initial_data and initial_data.get('quiz_template_id'):
            if 'quiz' in self.fields:
                self.fields['quiz'].required = False
                self.fields['quiz'].allow_null = True

    class Meta:
        model = QuizAssignment
        # Includi tutti i campi dichiarati sopra + quelli del modello gestiti automaticamente
        fields = [
            'id', 'student', 'student_username', 'quiz', 'quiz_title',
            'assigned_at', 'due_date', 'quiz_template_id'
        ]
        read_only_fields = ['assigned_at', 'student_username', 'quiz_title']
        extra_kwargs = {
        }

    def validate(self, attrs):
        """ Assicura che sia fornito quiz o quiz_template_id, ma non entrambi. """
        quiz = attrs.get('quiz')
        quiz_template_id = attrs.get('quiz_template_id')

        if not quiz and not quiz_template_id:
            raise ValidationError("È necessario fornire 'quiz' (ID del quiz esistente) o 'quiz_template_id'.")
        if quiz and quiz_template_id:
            raise ValidationError("Fornire 'quiz' o 'quiz_template_id', non entrambi.")

        return attrs

# --- Serializer Specifico per Azione Assegnazione Quiz da Template ---

class QuizAssignActionSerializer(serializers.Serializer):
   """
   Serializer specifico per validare i dati dell'azione 'assign_student' del QuizViewSet
   quando si assegna da un template. Non eredita da ModelSerializer.
   """
   student = serializers.PrimaryKeyRelatedField(
       queryset=Student.objects.filter(is_active=True),
       required=True,
       help_text="ID dello studente a cui assegnare il quiz."
   )
   quiz_template_id = serializers.IntegerField(
       required=True,
       allow_null=False, # Deve essere fornito per questa azione
       help_text="ID del QuizTemplate da cui creare e assegnare un nuovo Quiz."
   )
   due_date = serializers.DateTimeField(
       required=False,
       allow_null=True,
       help_text="Optional deadline for the quiz assignment."
   )

   def validate_quiz_template_id(self, value):
       """Verifica che il template esista."""
       try:
           QuizTemplate.objects.get(pk=value)
       except QuizTemplate.DoesNotExist:
           raise ValidationError(f"QuizTemplate con ID {value} non trovato.")
       return value

# --- Serializer Specifico per Azione Assegnazione Percorso da Template ---

class PathwayAssignActionSerializer(serializers.Serializer):
    """
    Serializer specifico per validare i dati dell'azione 'assign_student_pathway'
    quando si assegna da un template. Non eredita da ModelSerializer.
    """
    student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.filter(is_active=True),
        required=True,
        help_text="ID dello studente a cui assegnare il percorso."
    )
    pathway_template_id = serializers.IntegerField(
        required=True,
        allow_null=False, # Deve essere fornito per questa azione
        help_text="ID del PathwayTemplate da cui creare e assegnare un nuovo Percorso."
    )

    def validate_pathway_template_id(self, value):
        """Verifica che il template esista."""
        try:
            PathwayTemplate.objects.get(pk=value)
        except PathwayTemplate.DoesNotExist:
            raise ValidationError(f"PathwayTemplate con ID {value} non trovato.")
        return value


class PathwayAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer per assegnare Percorsi a Studenti. """
    # Dichiarazione esplicita del campo pathway per poterlo modificare in __init__
    pathway = serializers.PrimaryKeyRelatedField(
        queryset=Pathway.objects.all(),
        required=True, # Default a True, modificato in __init__ se necessario
        allow_null=False, # Default a False, modificato in __init__ se necessario
        help_text="ID del Percorso esistente da assegnare (alternativo a pathway_template_id)."
    )
    # Campo student è obbligatorio di default
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.filter(is_active=True))
    pathway_template_id = serializers.IntegerField(write_only=True, required=False, allow_null=True,
                                                   help_text="ID del PathwayTemplate da cui creare e assegnare un nuovo Percorso.")
    student_username = serializers.CharField(source='student.unique_identifier', read_only=True)
    pathway_title = serializers.CharField(source='pathway.title', read_only=True)

    def __init__(self, *args, **kwargs):
        # Esegui l'init standard del serializer
        super().__init__(*args, **kwargs)

        # Controlla se pathway_template_id è nei dati iniziali
        initial_data = kwargs.get('data', {})
        if initial_data and initial_data.get('pathway_template_id'):
            # Se pathway_template_id è fornito, rendi pathway non obbligatorio
            if 'pathway' in self.fields:
                self.fields['pathway'].required = False
                self.fields['pathway'].allow_null = True

    class Meta:
        model = PathwayAssignment
        # 'pathway' è dichiarato sopra, quindi deve essere incluso qui
        fields = [
            'id', 'student', 'student_username', 'pathway', 'pathway_title',
            'assigned_at', 'pathway_template_id'
        ]
        read_only_fields = ['assigned_at', 'student_username', 'pathway_title']
        extra_kwargs = {
        }

    def validate(self, attrs):
        """ Validazione custom per gestire pathway vs pathway_template_id. """
        initial_pathway = self.initial_data.get('pathway')
        pathway_template_id = attrs.get('pathway_template_id')

        if not initial_pathway and not pathway_template_id:
            raise ValidationError("È necessario fornire 'pathway' (ID del percorso esistente) o 'pathway_template_id'.")
        if initial_pathway and pathway_template_id:
            raise ValidationError("Fornire 'pathway' o 'pathway_template_id', non entrambi.")

        if initial_pathway:
            try:
                pathway_instance = Pathway.objects.get(pk=initial_pathway)
                attrs['pathway'] = pathway_instance
            except Pathway.DoesNotExist:
                raise ValidationError({'pathway': f"Percorso con ID {initial_pathway} non trovato."})
            except (TypeError, ValueError):
                 raise ValidationError({'pathway': "L'ID del percorso deve essere un numero intero."})

        if pathway_template_id and 'pathway' not in attrs:
             attrs['pathway'] = None

        return attrs


# --- Serializers per Svolgimento e Risultati ---

class StudentAnswerSerializer(serializers.ModelSerializer):
    """ Serializer per inviare/visualizzare le risposte dello studente. """
    question_text = serializers.CharField(source='question.text', read_only=True)
    question_type = serializers.CharField(source='question.question_type', read_only=True)

    class Meta:
        model = StudentAnswer
        fields = [
            'id', 'quiz_attempt', 'question', 'question_text', 'question_type',
            'selected_answers', 'is_correct', 'score', 'answered_at'
        ]
        read_only_fields = ['quiz_attempt', 'question', 'question_text', 'question_type', 'is_correct', 'score', 'answered_at']

    def validate_selected_answers(self, value):
        return value


class QuizAttemptSerializer(serializers.ModelSerializer):
    """ Serializer base per i tentativi di quiz. """
    student_info = StudentSerializer(source='student', read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'student', 'student_info', 'quiz', 'quiz_title',
            'started_at', 'completed_at', 'score', 'status', 'status_display'
        ]
        read_only_fields = ['student', 'student_info', 'quiz', 'quiz_title', 'started_at', 'completed_at', 'score', 'status', 'status_display']


class QuizAttemptDetailSerializer(QuizAttemptSerializer):
    """ Serializer dettagliato per un tentativo, include le risposte date. """
    student_answers = StudentAnswerSerializer(many=True, read_only=True)

    class Meta(QuizAttemptSerializer.Meta):
        fields = QuizAttemptSerializer.Meta.fields + ['student_answers']


class PathwayProgressSerializer(serializers.ModelSerializer):
    """ Serializer per il progresso dello studente in un percorso. """
    student_info = StudentSerializer(source='student', read_only=True)
    pathway_title = serializers.CharField(source='pathway.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PathwayProgress
        fields = [
            'id', 'student', 'student_info', 'pathway', 'pathway_title',
            'last_completed_quiz_order', 'completed_at', 'status', 'status_display'
        ]
        read_only_fields = fields


# --- Serializers per Dashboard Studente ---

class SimpleQuizAttemptSerializer(serializers.ModelSerializer):
    """ Serializer semplificato per l'ultimo tentativo, usato nella dashboard. """
    class Meta:
        model = QuizAttempt
        fields = ['id', 'score', 'status', 'completed_at']


class StudentQuizDashboardSerializer(QuizSerializer):
    """ Serializer per i quiz nella dashboard studente, include stato ultimo tentativo. """
    latest_attempt = serializers.SerializerMethodField()
    attempts_count = serializers.SerializerMethodField()

    class Meta(QuizSerializer.Meta):
        fields = QuizSerializer.Meta.fields + ['latest_attempt', 'attempts_count']

    def get_latest_attempt(self, obj):
        student = self.context.get('student')
        if student:
            latest = obj.attempts.filter(student=student).order_by('-started_at').first()
            if latest:
                return SimpleQuizAttemptSerializer(latest).data
        return None

    def get_attempts_count(self, obj):
        student = self.context.get('student')
        if student:
            return obj.attempts.filter(student=student).count()
        return 0


class SimplePathwayProgressSerializer(serializers.ModelSerializer):
    """ Serializer semplificato per l'ultimo progresso, usato nella dashboard. """
    class Meta:
        model = PathwayProgress
        fields = ['id', 'last_completed_quiz_order', 'status', 'completed_at']


class StudentPathwayDashboardSerializer(PathwaySerializer):
    """ Serializer per i percorsi nella dashboard studente, include stato ultimo progresso. """
    latest_progress = serializers.SerializerMethodField()
    total_quizzes = serializers.IntegerField(source='quizzes.count', read_only=True) # Conteggio quiz nel percorso

    class Meta(PathwaySerializer.Meta):
        fields = PathwaySerializer.Meta.fields + ['latest_progress', 'total_quizzes']

    def get_latest_progress(self, obj):
        student = self.context.get('student')
        if student:
            latest = obj.progresses.filter(student=student).first()
            if latest:
                return SimplePathwayProgressSerializer(latest).data
        return None


# --- Serializer per Svolgimento Percorso ---

class NextPathwayQuizSerializer(serializers.ModelSerializer):
    """ Serializer per restituire il prossimo quiz da svolgere in un percorso. """
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description']


class PathwayAttemptDetailSerializer(PathwaySerializer):
    """ Serializer per visualizzare i dettagli di un percorso durante lo svolgimento. """
    current_progress = SimplePathwayProgressSerializer(read_only=True)
    next_quiz = NextPathwayQuizSerializer(read_only=True)

    class Meta(PathwaySerializer.Meta):
        fields = PathwaySerializer.Meta.fields + ['current_progress', 'next_quiz']