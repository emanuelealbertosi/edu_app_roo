import logging
import io
import re
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
import markdown as md_parser # Rinominato per evitare conflitti
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from django.db import transaction, models # Aggiunto models
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
from .models import QuizAttempt, EarnedBadge # Assicurati che QuizAttempt e EarnedBadge siano importati
from apps.rewards.serializers import SimpleBadgeSerializer # Importa il serializer per i badge

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
            q["order"] = i # Ordine 0-based
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
            q["order"] = i # Ordine 0-based
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

        created_questions = QuestionTemplate.objects.bulk_create(questions_to_create)
        question_map = {(q.text, q.order): q for q in created_questions}

        for q_data in parsed_questions:
             question_obj = question_map.get((q_data['text'], q_data['order']))
             if not question_obj:
                 logger.warning(f"Domanda template '{q_data['text'][:50]}...' (ordine {q_data['order']}) non trovata dopo bulk_create.")
                 continue

             for opt_data in q_data['options']:
                 option_template = AnswerOptionTemplate(
                     question_template=question_obj,
                     text=opt_data['text'],
                     is_correct=opt_data['is_correct'],
                     order=opt_data['order']
                 )
                 options_to_create.append(option_template)

        if options_to_create:
            AnswerOptionTemplate.objects.bulk_create(options_to_create)

        logger.info(f"Creato QuizTemplate '{quiz_template.title}' (ID: {quiz_template.id}) con {len(created_questions)} domande da {uploaded_file.name}")
        return QuizTemplateSerializer(quiz_template, context=self.context).data


# --- Assignment Serializers ---

class QuizAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer per assegnare Quiz a Studenti. """
    # Permette di specificare quiz o template, ma non entrambi
    quiz = serializers.PrimaryKeyRelatedField(
        queryset=Quiz.objects.all(), required=False, allow_null=True
    )
    student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), required=True
    )
    quiz_template_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True,
        help_text="ID del QuizTemplate da cui creare e assegnare un'istanza di Quiz."
    )
    quiz_title = serializers.CharField(source='quiz.title', read_only=True) # Titolo del quiz assegnato

    # Rimosso __init__ e validazione complessa, gestita nella view

    class Meta:
        model = QuizAssignment
        fields = [
            'id', 'quiz', 'quiz_title', 'student', 'assigned_by', 'assigned_at', 'due_date', # Aggiunto assigned_by
            'quiz_template_id' # Campo per input
        ]
        read_only_fields = ['id', 'assigned_at', 'quiz_title']


class QuizAssignActionSerializer(serializers.Serializer):
   """
   Serializer specifico per l'azione di assegnazione quiz da template.
   Non è un ModelSerializer.
   """
   student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all(), required=True)
   quiz_template_id = serializers.IntegerField(required=True)
   due_date = serializers.DateTimeField(required=False, allow_null=True)

   def validate_quiz_template_id(self, value):
       if not QuizTemplate.objects.filter(pk=value).exists():
           raise ValidationError("Quiz Template non trovato.")
       return value


class PathwayAssignActionSerializer(serializers.Serializer):
    """
    Serializer specifico per l'azione di assegnazione percorso da template.
    Non è un ModelSerializer.
    """
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all(), required=True)
    # pathway_template_id = serializers.IntegerField(required=True) # Rimosso, l'ID viene dall'URL
    due_date = serializers.DateTimeField(required=False, allow_null=True) # Aggiunto per coerenza con Quiz


class PathwayAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer per assegnare Percorsi a Studenti. """
    pathway = serializers.PrimaryKeyRelatedField(
        queryset=Pathway.objects.all(), required=False, allow_null=True
    )
    student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), required=True
    )
    pathway_template_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True,
        help_text="ID del PathwayTemplate da cui creare e assegnare un'istanza di Pathway."
    )
    pathway_title = serializers.CharField(source='pathway.title', read_only=True)

    # Rimosso __init__ e validazione complessa, gestita nella view

    class Meta:
        model = PathwayAssignment
        fields = '__all__' # Aggiunto per specificare i campi


# Rimosso serializer duplicato ed errato

class QuizAssignmentDetailSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare gli studenti a cui è assegnato un quiz specifico. """
    student_id = serializers.IntegerField(source='student.id')
    student_full_name = serializers.CharField(source='student.full_name')
    student_code = serializers.CharField(source='student.student_code')
    student_username = serializers.CharField(source='student.student_code') # CORRETTO: Usa student_code come username
    assigned_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    due_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M", allow_null=True)

    class Meta:
        model = QuizAssignment
        fields = ['id', 'student_id', 'student_full_name', 'student_username', 'student_code', 'assigned_at', 'due_date'] # student_username ora punta a student_code


class PathwayAssignmentDetailSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare gli studenti a cui è assegnato un percorso specifico. """
    student_id = serializers.IntegerField(source='student.id')
    student_full_name = serializers.CharField(source='student.full_name')
    student_code = serializers.CharField(source='student.student_code')
    student_username = serializers.CharField(source='student.student_code') # Aggiunto username (che punta a code)
    assigned_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = PathwayAssignment
        # Aggiunto fields per includere i campi definiti sopra
        fields = ['id', 'student_id', 'student_full_name', 'student_username', 'student_code', 'assigned_at']
        fields = ['id', 'student_id', 'student_full_name', 'student_username', 'student_code', 'assigned_at'] # Assicurati che student_id sia qui


# --- Attempt & Progress Serializers ---

class StudentAnswerSerializer(serializers.ModelSerializer):
    """ Serializer per inviare/visualizzare le risposte dello studente. """
    # Rende question scrivibile per l'invio della risposta
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())

    class Meta:
        model = StudentAnswer
        fields = [
            'id', 'quiz_attempt', 'question', 'selected_options', 'answer_text',
            'is_correct', 'points_awarded'
        ]
        read_only_fields = ['id', 'quiz_attempt', 'is_correct', 'points_awarded']


class QuizAttemptSerializer(serializers.ModelSerializer):
    """ Serializer base per i tentativi di quiz. """
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    # Aggiungiamo i badge guadagnati
    newly_earned_badges = SimpleBadgeSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'quiz', 'quiz_title', 'student', 'student_name', 'status', 'status_display',
            'score', 'started_at', 'completed_at', 'newly_earned_badges' # Corretto start_time->started_at, end_time->completed_at
        ]
        read_only_fields = [
            'id', 'quiz', 'quiz_title', 'student', 'student_name', 'status', 'status_display',
            'score', 'started_at', 'completed_at', 'newly_earned_badges' # Corretto start_time->started_at, end_time->completed_at
        ]

    def to_representation(self, instance):
        """ Arrotonda lo score a 2 decimali se non è None. """
        representation = super().to_representation(instance)
        score = representation.get('score')
        if score is not None:
            try:
                representation['score'] = round(float(score), 2)
            except (ValueError, TypeError):
                representation['score'] = None # O 0.0, a seconda di come vuoi gestire errori
        return representation


class QuizAttemptDetailSerializer(QuizAttemptSerializer):
    """ Serializer dettagliato per un tentativo, include risposte date e info aggiuntive. """
    # Eredita i campi da QuizAttemptSerializer
    student_answers = StudentAnswerSerializer(many=True, read_only=True)
    # Potremmo aggiungere qui i dettagli del quiz se necessario
    quiz_details = QuizSerializer(source='quiz', read_only=True)
    # Calcola il numero di risposte corrette
    correct_answers_count = serializers.SerializerMethodField()

    class Meta(QuizAttemptSerializer.Meta): # Eredita Meta dal genitore
        fields = QuizAttemptSerializer.Meta.fields + [
            'student_answers', 'quiz_details', 'correct_answers_count'
        ]
        # read_only_fields sono ereditati e vanno bene

    def get_correct_answers_count(self, obj: QuizAttempt) -> int:
        """ Conta le risposte corrette per questo tentativo. """
        return obj.student_answers.filter(is_correct=True).count()


class PathwayProgressSerializer(serializers.ModelSerializer):
    """ Serializer per il progresso dello studente in un percorso. """
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    pathway_title = serializers.CharField(source='pathway.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PathwayProgress
        fields = [
            'id', 'pathway', 'pathway_title', 'student', 'student_name', 'status', 'status_display',
            'completed_quizzes', 'start_time', 'end_time', 'points_earned'
        ]
        read_only_fields = fields # Tutti i campi sono di sola lettura qui


# --- Serializers per Dashboard Studente ---

class SimpleQuizAttemptSerializer(serializers.ModelSerializer):
    """ Serializer minimale per l'ultimo tentativo, usato nella dashboard. """
    class Meta:
        model = QuizAttempt
        fields = ['id', 'status', 'score', 'end_time']


class StudentQuizDashboardSerializer(QuizSerializer):
    """ Serializer per i quiz nella dashboard studente, include stato ultimo tentativo. """
    latest_attempt = SimpleQuizAttemptSerializer(read_only=True) # Campo annotato dalla view

    class Meta(QuizSerializer.Meta): # Eredita Meta da QuizSerializer
        fields = QuizSerializer.Meta.fields + ['latest_attempt']

    def get_latest_attempt(self, obj):
        # Questo metodo non è più necessario se usiamo l'annotazione nella view
        # Se non usiamo l'annotazione, dovremmo implementarlo qui
        # request = self.context.get('request')
        # if request and hasattr(request, 'user') and isinstance(request.user, Student):
        #     attempt = obj.attempts.filter(student=request.user).order_by('-start_time').first()
        #     if attempt:
        #         return SimpleQuizAttemptSerializer(attempt).data
        return None


class SimplePathwayProgressSerializer(serializers.ModelSerializer):
    """ Serializer minimale per l'ultimo progresso, usato nella dashboard. """
    class Meta:
        model = PathwayProgress
        fields = ['id', 'status', 'end_time']


class StudentPathwayDashboardSerializer(PathwaySerializer):
    """ Serializer per i percorsi nella dashboard studente, include stato ultimo progresso. """
    latest_progress = SimplePathwayProgressSerializer(read_only=True) # Campo annotato dalla view

    class Meta(PathwaySerializer.Meta): # Eredita Meta da PathwaySerializer
        fields = PathwaySerializer.Meta.fields + ['latest_progress']

    def get_latest_progress(self, obj):
        # Metodo non necessario se usiamo l'annotazione nella view
        # request = self.context.get('request')
        # if request and hasattr(request, 'user') and isinstance(request.user, Student):
        #     progress = obj.progresses.filter(student=request.user).order_by('-start_time').first()
        #     if progress:
        #         return SimplePathwayProgressSerializer(progress).data
        return None


# --- Serializers per Svolgimento Percorso ---

class NextPathwayQuizSerializer(serializers.ModelSerializer):
    """ Serializer per restituire il prossimo quiz da svolgere in un percorso. """
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description'] # Info base del quiz


class PathwayAttemptDetailSerializer(PathwaySerializer):
    """
    Serializer per la vista di dettaglio di un percorso durante lo svolgimento.
    Include informazioni sul prossimo quiz da fare.
    """
    next_quiz = serializers.SerializerMethodField()
    progress_status = serializers.CharField(source='latest_progress.get_status_display', read_only=True, default='Non iniziato') # Aggiunto stato progresso

    class Meta(PathwaySerializer.Meta):
        fields = PathwaySerializer.Meta.fields + ['next_quiz', 'progress_status']

    def get_next_quiz(self, obj: Pathway) -> dict | None:
        """ Determina il prossimo quiz non completato nel percorso per lo studente corrente. """
        student = self.context['request'].user
        if not isinstance(student, Student):
            return None # O solleva errore?

        # Trova l'ordine dell'ultimo quiz completato (con successo) in questo percorso
        last_completed_quiz_order = QuizAttempt.objects.filter(
            student=student,
            quiz__pathwayquiz__pathway=obj, # Filtra per tentativi di quiz in questo percorso
            status=QuizAttempt.AttemptStatus.COMPLETED,
            # Aggiungere controllo score >= soglia se necessario
        ).aggregate(max_order=models.Max('quiz__pathwayquiz__order'))['max_order']

        next_order = 0 if last_completed_quiz_order is None else last_completed_quiz_order + 1

        # Trova il prossimo PathwayQuiz in ordine
        next_pathway_quiz = obj.pathwayquiz_set.filter(order=next_order).select_related('quiz').first()

        if next_pathway_quiz:
            return NextPathwayQuizSerializer(next_pathway_quiz.quiz).data
        else:
            # Se non c'è un prossimo quiz, il percorso potrebbe essere completato
            # (o c'è un problema con l'ordine)
            return None


# --- Serializers per Vista Gestione Studenti (Docente) ---

class StudentQuizAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare i quiz assegnati a uno studente. """
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    quiz_description = serializers.CharField(source='quiz.description', read_only=True, allow_null=True)
    assigned_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    due_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M", allow_null=True)

    class Meta:
        model = QuizAssignment
        fields = ['id', 'quiz', 'quiz_title', 'quiz_description', 'assigned_at', 'due_date']
        read_only_fields = fields


class StudentPathwayAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare i percorsi assegnati a uno studente. """
    pathway_title = serializers.CharField(source='pathway.title', read_only=True)
    pathway_description = serializers.CharField(source='pathway.description', read_only=True, allow_null=True)
    assigned_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = PathwayAssignment
        fields = ['id', 'pathway', 'pathway_title', 'pathway_description', 'assigned_at']
        read_only_fields = fields


# --- Serializer per Statistiche Template Quiz ---

class QuizTemplateStatsSerializer(serializers.Serializer):
    """ Serializer per le statistiche aggregate di un QuizTemplate. """
    template_id = serializers.IntegerField(read_only=True)
    template_title = serializers.CharField(read_only=True)
    total_instances_created = serializers.IntegerField(read_only=True, default=0)
    total_assignments = serializers.IntegerField(read_only=True, default=0)
    total_attempts = serializers.IntegerField(read_only=True, default=0)
    average_score = serializers.FloatField(read_only=True, allow_null=True) # Media punteggi tentativi completati
    completion_rate = serializers.FloatField(read_only=True, allow_null=True) # Percentuale tentativi completati sul totale

    def to_representation(self, instance):
        """ Arrotonda i float a 2 decimali se non sono None. """
        representation = super().to_representation(instance)
        avg_score = representation.get('average_score')
        comp_rate = representation.get('completion_rate')
        if avg_score is not None:
            try: representation['average_score'] = round(float(avg_score), 2)
            except (ValueError, TypeError): representation['average_score'] = None
        if comp_rate is not None:
            try: representation['completion_rate'] = round(float(comp_rate) * 100, 1) # Mostra come percentuale
            except (ValueError, TypeError): representation['completion_rate'] = None
        return representation

# --- Serializer per Statistiche Template Percorsi ---

class PathwayTemplateStatsSerializer(serializers.Serializer):
    """ Serializer per le statistiche aggregate di un PathwayTemplate. """
    template_id = serializers.IntegerField(read_only=True)
    template_title = serializers.CharField(read_only=True)
    total_instances_created = serializers.IntegerField(read_only=True, default=0)
    total_assignments = serializers.IntegerField(read_only=True, default=0)
    total_progress_started = serializers.IntegerField(read_only=True, default=0) # Numero di studenti che hanno iniziato
    total_progress_completed = serializers.IntegerField(read_only=True, default=0) # Numero di studenti che hanno completato
    completion_rate = serializers.FloatField(read_only=True, allow_null=True) # Percentuale completati su iniziati

    def to_representation(self, instance):
        """ Arrotonda i float a 1 decimale se non sono None. """
        representation = super().to_representation(instance)
        comp_rate = representation.get('completion_rate')
        if comp_rate is not None:
            try: representation['completion_rate'] = round(float(comp_rate) * 100, 1) # Mostra come percentuale
            except (ValueError, TypeError): representation['completion_rate'] = None
        return representation
