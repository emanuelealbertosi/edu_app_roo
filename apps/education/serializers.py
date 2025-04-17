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

        # Filtra le domande assicurandosi che abbiano testo effettivo (non solo spazi bianchi)
        questions = [q for q in questions if q.get("text") and q.get("text").strip()]
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
        creator: User = self.context['request'].user

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
             logger.error(f"Errore estrazione testo da {uploaded_file.name} (template): {e}", exc_info=True)
             raise ValidationError(f"Errore lettura file {file_ext} (template).")


        if not text or text.isspace():
             raise ValidationError(f"Contenuto testuale non valido da {uploaded_file.name} (template).")

        try:
            parsed_questions = self._parse_quiz_text(text)
        except ValidationError as e:
             raise e
        except Exception as e:
             logger.error(f"Errore parsing testo da {uploaded_file.name} (template): {e}", exc_info=True)
             raise ValidationError("Errore analisi contenuto file (template).")


        quiz_template = QuizTemplate.objects.create(
            teacher=creator, # Associa il docente creatore
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

        logger.info(f"Creato QuizTemplate '{quiz_template.title}' (ID: {quiz_template.id}) con {len(created_question_templates)} domande da {uploaded_file.name}")
        return QuizTemplateSerializer(quiz_template, context=self.context).data


# --- Serializers per Assegnazione ---

class QuizAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer per assegnare Quiz a Studenti. """
    # Permette di specificare il template da cui creare il quiz
    quiz_template_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True,
        help_text="ID del QuizTemplate da cui creare e assegnare il quiz."
    )
    # Permette di specificare un quiz esistente
    quiz_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True,
        help_text="ID di un Quiz esistente da assegnare."
    )
    student_id = serializers.IntegerField(write_only=True, required=True)
    due_date = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = QuizAssignment
        fields = ['id', 'quiz', 'quiz_template_id', 'quiz_id', 'student', 'student_id', 'assigned_by', 'assigned_at', 'due_date']
        read_only_fields = ['id', 'quiz', 'student', 'assigned_by', 'assigned_at']

    def validate(self, data):
        if not data.get('quiz_template_id') and not data.get('quiz_id'):
            raise ValidationError("È necessario fornire 'quiz_template_id' o 'quiz_id'.")
        if data.get('quiz_template_id') and data.get('quiz_id'):
            raise ValidationError("Fornire solo 'quiz_template_id' o 'quiz_id', non entrambi.")
        return data

    # create non è necessario qui, la logica è nella view


class QuizAssignActionSerializer(serializers.Serializer):
   """
   Serializer specifico per l'azione di assegnazione, usato per validare l'input
   prima di chiamare la logica di creazione/assegnazione nella view.
   """
   # Modificato per accettare una lista di ID studente
   student_ids = serializers.ListField(
       child=serializers.IntegerField(),
       required=True,
       allow_empty=False,
       help_text="Lista degli ID degli studenti a cui assegnare il quiz."
   )
   quiz_template_id = serializers.PrimaryKeyRelatedField(queryset=QuizTemplate.objects.all(), required=False, allow_null=True)
   quiz_id = serializers.PrimaryKeyRelatedField(queryset=Quiz.objects.all(), required=False, allow_null=True)
   due_date = serializers.DateTimeField(required=False, allow_null=True)

   def validate(self, data):
       if not data.get('quiz_template_id') and not data.get('quiz_id'):
           raise ValidationError("È necessario fornire 'quiz_template_id' o 'quiz_id'.")
       if data.get('quiz_template_id') and data.get('quiz_id'):
           raise ValidationError("Fornire solo 'quiz_template_id' o 'quiz_id', non entrambi.")

       # Verifica ownership del quiz esistente se fornito
       quiz = data.get('quiz_id')
       user = self.context['request'].user
       if quiz and not user.is_staff and quiz.teacher != user:
            raise ValidationError("Non puoi assegnare un quiz che non hai creato.")

       # Verifica ownership del template se fornito
       template = data.get('quiz_template_id')
       if template and not user.is_staff and template.teacher != user:
            raise ValidationError("Non puoi usare un template di quiz che non hai creato.")

       # Convalida gli ID studente e convertili in oggetti Student
       student_ids = data.get('student_ids', [])
       students = Student.objects.filter(id__in=student_ids)
       if len(students) != len(student_ids):
           found_ids = set(students.values_list('id', flat=True))
           missing_ids = [sid for sid in student_ids if sid not in found_ids]
           raise ValidationError(f"Uno o più ID studente non trovati: {missing_ids}")

       # Sostituisci student_ids con la lista di oggetti Student validati
       data['students'] = list(students)

       return data


class PathwayAssignActionSerializer(serializers.Serializer):
    """ Serializer per validare l'azione di assegnazione di un percorso da template. """
    student_id = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all(), required=True)
    # Non serve pathway_template_id qui perché è nell'URL
    due_date = serializers.DateTimeField(required=False, allow_null=True)
    # Aggiunto student per poterlo usare nella view dopo la validazione
    student = serializers.SerializerMethodField()

    def get_student(self, obj):
        # Questo metodo non verrà mai chiamato perché non serializziamo un oggetto
        # Ma lo definiamo per coerenza e per poter accedere a validated_data['student_id']
        return Student.objects.get(pk=obj.get('student_id'))

    def validate_student_id(self, value):
        # Aggiunge l'oggetto student validato ai dati
        self.context['validated_student'] = value
        return value


class PathwayAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer per assegnare Percorsi a Studenti. """
    pathway_template_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True,
        help_text="ID del PathwayTemplate da cui creare e assegnare il percorso."
    )
    # Aggiunto pathway_id per assegnare percorsi esistenti (se necessario in futuro)
    pathway_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True,
        help_text="ID di un Pathway esistente da assegnare."
    )
    student_id = serializers.IntegerField(write_only=True, required=True)
    # Rimosso due_date perché non è nel modello PathwayAssignment
    # due_date = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = PathwayAssignment
        # Rimosso due_date dai fields
        fields = ['id', 'pathway', 'pathway_template_id', 'pathway_id', 'student', 'student_id', 'assigned_by', 'assigned_at']
        read_only_fields = ['id', 'pathway', 'student', 'assigned_by', 'assigned_at']

    def validate(self, data):
        # Aggiornato per usare pathway_id
        if not data.get('pathway_template_id') and not data.get('pathway_id'):
            raise ValidationError("È necessario fornire 'pathway_template_id' o 'pathway_id'.")
        if data.get('pathway_template_id') and data.get('pathway_id'):
            raise ValidationError("Fornire solo 'pathway_template_id' o 'pathway_id', non entrambi.")
        return data


# --- Serializers per Visualizzazione Dettagli Assegnazioni ---

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
    # Campo per ricevere l'ID della domanda in input
    question_id = serializers.IntegerField(write_only=True, help_text="ID della domanda a cui si sta rispondendo.")
    # Campo per visualizzare i dettagli della domanda (sola lettura)
    question = serializers.PrimaryKeyRelatedField(read_only=True) # Reso read_only

    class Meta:
        model = StudentAnswer
        fields = [
            'id', 'quiz_attempt', 'question', 'question_id', # Aggiunto question_id
            'selected_answers', 'is_correct', 'score'
        ]
        read_only_fields = [
            'id', 'quiz_attempt', 'question', # Aggiunto question alla lista read_only
            'is_correct', 'score'
        ]


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
    # Aggiungi la soglia di completamento dai metadati del quiz
    completion_threshold = serializers.SerializerMethodField()
    # Aggiungi conteggi domande
    total_questions = serializers.SerializerMethodField()
    correct_answers_count = serializers.SerializerMethodField()

    class Meta(QuizAttemptSerializer.Meta): # Eredita Meta dal genitore
        # Aggiungi i nuovi campi ai fields ereditati
        fields = QuizAttemptSerializer.Meta.fields + [
            'student_answers', 'quiz_details', 'completion_threshold',
            'total_questions', 'correct_answers_count' # Aggiunti campi conteggio
        ]
        read_only_fields = QuizAttemptSerializer.Meta.read_only_fields + [
            'student_answers', 'quiz_details', 'completion_threshold',
            'total_questions', 'correct_answers_count' # Aggiunti campi conteggio
        ]

    def get_completion_threshold(self, obj: QuizAttempt) -> float | None:
        """ Recupera la soglia di completamento dai metadati del quiz associato. """
        # Accedi ai metadati tramite l'oggetto quiz relazionato
        # Cerca la chiave corretta 'completion_threshold'
        threshold = obj.quiz.metadata.get('completion_threshold')
        try:
            # Prova a convertire in float, gestisci None o valori non validi
            # Il valore 1 probabilmente rappresenta 100%, quindi moltiplichiamo per 100
            # Se il valore è già una percentuale (es. 75), questa logica andrebbe rivista.
            # Assumiamo per ora che 1 significhi 100%.
            if threshold is not None:
                threshold_float = float(threshold)
                # Se il valore è <= 1, assumiamo sia una frazione (es. 1 o 0.75)
                return threshold_float * 100 if threshold_float <= 1 else threshold_float
            else:
                return None
        except (ValueError, TypeError):
            logger.warning(f"Valore non valido per completion_threshold nei metadati del Quiz {obj.quiz.id}: {threshold}")
            return None

    def get_total_questions(self, obj: QuizAttempt) -> int:
        """ Restituisce il numero totale di domande nel quiz associato. """
        return obj.quiz.questions.count()

    def get_correct_answers_count(self, obj: QuizAttempt) -> int:
        """ Restituisce il numero di risposte corrette date in questo tentativo. """
        # Assicurati che student_answers sia prefetched o usa .all() se necessario
        # return obj.student_answers.filter(is_correct=True).count() # Questo potrebbe fare N+1 query se non prefetched
        # Alternativa: conta direttamente sul DB
        return StudentAnswer.objects.filter(quiz_attempt=obj, is_correct=True).count()


class PathwayProgressSerializer(serializers.ModelSerializer):
    """ Serializer per il progresso dello studente in un percorso. """
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    pathway_title = serializers.CharField(source='pathway.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PathwayProgress
        fields = [
            'id', 'pathway', 'pathway_title', 'student', 'student_name', 'status', 'status_display',
            'last_completed_quiz_order', 'completed_at', 'points_earned'
        ]
        read_only_fields = fields # Tutti i campi sono di sola lettura per questo serializer


# --- Serializers per Dashboard Studente ---

class SimpleQuizAttemptSerializer(serializers.ModelSerializer):
    """ Serializer minimale per l'ultimo tentativo nella dashboard. """
    class Meta:
        model = QuizAttempt
        fields = ['id', 'status', 'score', 'completed_at']


class StudentQuizDashboardSerializer(QuizSerializer):
    """ Serializer per i quiz nella dashboard studente, include stato ultimo tentativo. """
    latest_attempt = serializers.SerializerMethodField()

    class Meta(QuizSerializer.Meta):
        fields = QuizSerializer.Meta.fields + ['latest_attempt']

    def get_latest_attempt(self, obj):
        # Recupera lo studente dal contesto della richiesta
        student = self.context['request'].user
        if not isinstance(student, Student):
            return None # O solleva un errore se lo studente non è nel contesto

        latest = obj.attempts.filter(student=student).order_by('-started_at').first()
        if latest:
            return SimpleQuizAttemptSerializer(latest).data
        return None


class SimplePathwayProgressSerializer(serializers.ModelSerializer):
    """ Serializer minimale per l'ultimo progresso nella dashboard. """
    class Meta:
        model = PathwayProgress
        fields = ['id', 'status', 'last_completed_quiz_order', 'completed_at']


class StudentPathwayDashboardSerializer(PathwaySerializer):
    """ Serializer per i percorsi nella dashboard studente, include stato ultimo progresso. """
    latest_progress = serializers.SerializerMethodField()

    class Meta(PathwaySerializer.Meta):
        fields = PathwaySerializer.Meta.fields + ['latest_progress']

    def get_latest_progress(self, obj):
        student = self.context['request'].user
        if not isinstance(student, Student):
            return None

        latest = obj.progresses.filter(student=student).order_by('-id').first() # Usa ID o un timestamp se disponibile
        if latest:
            return SimplePathwayProgressSerializer(latest).data
        return None


# --- Serializer per Dettaglio Tentativo Percorso ---

class NextPathwayQuizSerializer(serializers.ModelSerializer):
    """ Serializer per rappresentare il prossimo quiz da fare in un percorso. """
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description'] # Campi essenziali del quiz


class PathwayAttemptDetailSerializer(PathwaySerializer):
    """
    Serializer per visualizzare i dettagli di un percorso per uno studente specifico,
    includendo lo stato di avanzamento e il prossimo quiz da fare.
    """
    progress = serializers.SerializerMethodField()
    next_quiz = serializers.SerializerMethodField()

    class Meta(PathwaySerializer.Meta):
        fields = PathwaySerializer.Meta.fields + ['progress', 'next_quiz']

    def get_progress(self, obj: Pathway) -> dict | None:
        """ Recupera il progresso dello studente corrente per questo percorso. """
        student = self.context['request'].user
        if not isinstance(student, Student):
            return None
        progress = obj.progresses.filter(student=student).first()
        if progress:
            return PathwayProgressSerializer(progress).data
        return None

    def get_next_quiz(self, obj: Pathway) -> dict | None:
        """ Determina il prossimo quiz non completato nel percorso per lo studente corrente. """
        student = self.context['request'].user
        if not isinstance(student, Student):
            return None

        progress = obj.progresses.filter(student=student).first()
        last_completed_order = progress.last_completed_quiz_order if progress else -1

        # Trova il PathwayQuiz con l'ordine successivo
        next_pathway_quiz = obj.pathwayquiz_set.filter(order__gt=last_completed_order).order_by('order').first()

        if next_pathway_quiz:
            # Verifica se lo studente ha già completato *questo specifico* quiz (anche fuori dal percorso)
            # Questa logica potrebbe essere complessa. Per ora, assumiamo che se è il prossimo nell'ordine,
            # lo studente debba farlo (o rifarlo se fallito e permesso).
            # La logica di "start_attempt" gestirà se può effettivamente iniziarlo.
            return NextPathwayQuizSerializer(next_pathway_quiz.quiz).data
        return None # Nessun quiz successivo (percorso completato o vuoto)


# --- Serializers per Visualizzazione Assegnazioni Studente (dal punto di vista del Docente) ---

class StudentQuizAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare i quiz assegnati a uno studente. """
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    assigned_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    due_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M", allow_null=True)

    class Meta:
        model = QuizAssignment
        fields = ['id', 'quiz', 'quiz_title', 'assigned_at', 'due_date']


class StudentPathwayAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare i percorsi assegnati a uno studente. """
    pathway_title = serializers.CharField(source='pathway.title', read_only=True)
    assigned_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = PathwayAssignment
        fields = ['id', 'pathway', 'pathway_title', 'assigned_at']


# --- Serializers per Statistiche Template (Docente) ---

class QuizTemplateStatsSerializer(serializers.Serializer):
    """ Serializer per le statistiche aggregate di un QuizTemplate. """
    template_id = serializers.IntegerField()
    template_title = serializers.CharField()
    total_instances_created = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    total_attempts = serializers.IntegerField()
    average_score = serializers.FloatField(allow_null=True)
    completed_attempts = serializers.IntegerField()
    # Potremmo aggiungere pass_rate se necessario

    def to_representation(self, instance):
        # Arrotonda average_score se non è null
        representation = super().to_representation(instance)
        avg_score = representation.get('average_score')
        if avg_score is not None:
            representation['average_score'] = round(avg_score, 2)
        return representation


class PathwayTemplateStatsSerializer(serializers.Serializer):
    """ Serializer per le statistiche aggregate di un PathwayTemplate. """
    template_id = serializers.IntegerField()
    template_title = serializers.CharField()
    total_instances_created = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    total_progress_started = serializers.IntegerField()
    total_progress_completed = serializers.IntegerField()
    completion_rate = serializers.FloatField(allow_null=True)

    def to_representation(self, instance):
        # Formatta completion_rate come percentuale se non è null
        representation = super().to_representation(instance)
        rate = representation.get('completion_rate')
        if rate is not None:
            representation['completion_rate'] = f"{rate * 100:.1f}%" # Es. "75.0%"
        return representation
