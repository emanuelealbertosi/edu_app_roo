import logging
from apps.student_groups.models import StudentGroupMembership # Assicurati che sia importato
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
    QuizAssignment, PathwayAssignment, # Importa Assignment
    PathwayTemplate, PathwayQuizTemplate # Importa i nuovi modelli Template
)
from apps.users.serializers import UserSerializer, StudentSerializer, StudentBasicSerializer # Usiamo StudentBasicSerializer
from apps.users.models import User, Student
from apps.student_groups.models import StudentGroup # Importa StudentGroup
# Importa il serializer base per StudentGroup se esiste, altrimenti creane uno semplice qui
try:
    from apps.student_groups.serializers import StudentGroupSerializer as BaseStudentGroupSerializer

    class StudentGroupBasicSerializer(BaseStudentGroupSerializer):
         class Meta(BaseStudentGroupSerializer.Meta):
              fields = ['id', 'name', 'teacher'] # Campi base
              read_only_fields = fields # Sola lettura in questo contesto
except ImportError:
    # Fallback se student_groups non è ancora pronto o non ha serializer
    class StudentGroupBasicSerializer(serializers.ModelSerializer):
        class Meta:
            model = StudentGroup
            fields = ['id', 'name'] # Info minime
            read_only_fields = fields


from .models import QuizAttempt, EarnedBadge # Assicurati che QuizAttempt e EarnedBadge siano importati
from apps.rewards.serializers import SimpleBadgeSerializer # Importa il serializer per i badge

logger = logging.getLogger(__name__)

# --- Template Serializers (Invariati) ---

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


# --- Concrete Serializers (Quiz, Question, Pathway - Invariati) ---

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


# --- Serializer per Upload Quiz (Invariato) ---

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
            # Semplice estrazione testo, potrebbe non gestire bene HTML complesso
            text = re.sub('<[^<]+?>', '', md_parser.markdown(md_content)).strip()
            if not text:
                 logger.warning("Nessun testo estratto dal Markdown.")
            return text
        except Exception as e:
            logger.error(f"Errore estrazione testo Markdown: {e}", exc_info=True)
            raise ValidationError(f"Impossibile leggere il file Markdown. Errore: {e}")

    def _parse_quiz_text(self, text: str) -> list[dict]:
        # Implementazione del parsing (mantenuta come prima)
        questions = []
        current_question = None
        # Regex per inizio domanda (numero opzionale seguito da punto/parentesi)
        question_start_re = re.compile(r"^\s*(?:(\d+)\s*[.)])?\s*(.*)", re.MULTILINE)
        # Regex per opzione (lettera maiuscola seguita da punto/parentesi)
        option_re = re.compile(r"^\s*([A-Z])\s*[.)]\s*(.*)", re.MULTILINE)
        empty_line_re = re.compile(r"^\s*$")
        lines = text.splitlines()
        question_counter = 0 # Contatore per domande senza numero esplicito

        for line in lines:
            if empty_line_re.match(line):
                continue # Salta righe vuote

            line_stripped = line.strip()
            question_match = question_start_re.match(line) # Controlla se inizia come domanda
            option_match = option_re.match(line_stripped) # Controlla se è un'opzione
            is_likely_question_start = question_match and question_match.group(1) # Ha un numero?
            is_likely_option = option_match # È formattata come opzione?

            # Logica di parsing migliorata
            if is_likely_question_start:
                # Probabile inizio di una nuova domanda numerata
                if current_question:
                    questions.append(current_question) # Salva la domanda precedente
                question_number = int(question_match.group(1))
                question_text = question_match.group(2).strip()
                question_counter = question_number # Aggiorna contatore se numerata
                current_question = {
                    "text": question_text, "order": question_number, "options": [],
                    "type": QuestionType.MULTIPLE_CHOICE_SINGLE # Default
                }
            elif is_likely_option and current_question:
                # Probabile opzione della domanda corrente
                option_letter = option_match.group(1)
                option_text = option_match.group(2).strip()
                current_question["options"].append({
                    "text": option_text, "order": len(current_question["options"]) + 1, "is_correct": False # is_correct da definire
                })
            elif current_question:
                 # Riga non vuota, non è inizio domanda numerata, non è opzione formattata
                 # Potrebbe essere continuazione testo domanda o testo opzione
                 if current_question["options"] and not is_likely_question_start:
                     # Se ci sono già opzioni, probabilmente è continuazione dell'ultima opzione
                     current_question["options"][-1]["text"] += " " + line_stripped
                 else:
                     # Altrimenti, è continuazione del testo della domanda
                     # O è una domanda non numerata che inizia qui
                     if current_question["options"] or not current_question["text"]:
                         # Se la domanda precedente aveva opzioni o testo vuoto, inizia nuova domanda non numerata
                         if current_question["text"]: # Salva la precedente se aveva testo
                             questions.append(current_question)
                         question_counter += 1
                         current_question = {
                             "text": line_stripped, "order": question_counter, "options": [],
                             "type": QuestionType.MULTIPLE_CHOICE_SINGLE
                         }
                     else:
                        # Altrimenti, aggiungi al testo della domanda corrente
                        current_question["text"] += " " + line_stripped
            elif not current_question and line_stripped:
                 # Prima riga non vuota del file, considerala la prima domanda (non numerata)
                 question_counter += 1
                 current_question = {
                     "text": line_stripped, "order": question_counter, "options": [],
                     "type": QuestionType.MULTIPLE_CHOICE_SINGLE
                 }

        if current_question: # Salva l'ultima domanda
            questions.append(current_question)

        # Post-processing
        questions = [q for q in questions if q.get("text")] # Rimuovi eventuali domande vuote
        questions.sort(key=lambda q: q.get("order", float('inf'))) # Ordina per numero/contatore
        for i, q in enumerate(questions):
            q["order"] = i # Riassegna ordine 0-based sequenziale
            if not q["options"]:
                q["type"] = QuestionType.OPEN_ANSWER_MANUAL # Se non ha opzioni, è aperta

        if not questions:
             raise ValidationError("Nessuna domanda valida trovata nel file. Verifica la formattazione.")

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
                # Questo non dovrebbe accadere grazie a validate_file
                raise ValidationError("Tipo di file non gestito internamente.")
        except ValidationError as e:
             raise e # Rilancia errori di validazione specifici
        except Exception as e:
             logger.error(f"Errore estrazione testo da {uploaded_file.name}: {e}", exc_info=True)
             raise ValidationError(f"Errore durante la lettura del file {file_ext}.")


        if not text or text.isspace():
             raise ValidationError(f"Nessun contenuto testuale valido estratto da {uploaded_file.name}.")

        try:
            parsed_questions = self._parse_quiz_text(text)
        except ValidationError as e:
             raise e # Rilancia errori di validazione specifici
        except Exception as e:
             logger.error(f"Errore durante il parsing del testo da {uploaded_file.name}: {e}", exc_info=True)
             raise ValidationError("Errore durante l'analisi del contenuto del file.")


        # Creazione Quiz
        quiz = Quiz.objects.create(
            teacher=teacher,
            title=title,
            description=f"Quiz generato automaticamente da {uploaded_file.name}",
            metadata={
                'source_file': uploaded_file.name,
                'generation_method': 'auto_upload'
            }
            # available_from/until possono essere impostati successivamente
        )

        # Creazione Domande e Opzioni (Bulk)
        questions_to_create = []
        options_to_create = []

        for q_data in parsed_questions:
            question = Question(
                quiz=quiz,
                text=q_data['text'],
                question_type=q_data['type'],
                order=q_data['order'],
                metadata={} # Eventuali metadati specifici della domanda
            )
            questions_to_create.append(question)

        # Crea le domande in blocco e ottieni gli oggetti creati
        created_questions = Question.objects.bulk_create(questions_to_create)

        # Mappa per recuperare gli ID delle domande appena create
        # Usiamo una tupla (testo, ordine) come chiave, sperando sia sufficientemente univoca
        question_map = {(q.text, q.order): q for q in created_questions}

        # Prepara le opzioni associandole alle domande corrette
        for q_data in parsed_questions:
             # Recupera l'oggetto Question corrispondente usando la mappa
             question_obj = question_map.get((q_data['text'], q_data['order']))
             if not question_obj:
                 logger.warning(f"Domanda '{q_data['text'][:50]}...' (ordine {q_data['order']}) non trovata dopo bulk_create. Impossibile aggiungere opzioni.")
                 continue # Salta le opzioni per questa domanda

             for opt_data in q_data['options']:
                 option = AnswerOption(
                     question=question_obj,
                     text=opt_data['text'],
                     is_correct=opt_data['is_correct'], # Assumendo che il parser possa determinarlo
                     order=opt_data['order']
                 )
                 options_to_create.append(option)

        # Crea le opzioni in blocco se ce ne sono
        if options_to_create:
            AnswerOption.objects.bulk_create(options_to_create)

        logger.info(f"Creato Quiz '{quiz.title}' (ID: {quiz.id}) con {len(created_questions)} domande da {uploaded_file.name}")
        # Restituisce i dati del quiz creato usando il serializer appropriato
        return QuizSerializer(quiz, context=self.context).data

# --- Serializer per Upload Quiz Template (Invariato) ---

class QuizTemplateUploadSerializer(serializers.Serializer):
    """
    Serializer per gestire l'upload di file (PDF, DOCX, MD) per creare QuizTemplate.
    """
    file = serializers.FileField(required=True, help_text="File del quiz template (.pdf, .docx, .md)")
    title = serializers.CharField(max_length=255, required=True, help_text="Titolo del nuovo quiz template")

    # Metodi validate_file, _extract_text_from_*, _parse_quiz_text sono identici a QuizUploadSerializer
    # Si potrebbe creare una classe base comune per evitare duplicazione
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
            text = re.sub('<[^<]+?>', '', md_parser.markdown(md_content)).strip()
            if not text:
                 logger.warning("Nessun testo estratto dal Markdown (template).")
            return text
        except Exception as e:
            logger.error(f"Errore estrazione testo Markdown (template): {e}", exc_info=True)
            raise ValidationError(f"Impossibile leggere il file Markdown (template). Errore: {e}")

    def _parse_quiz_text(self, text: str) -> list[dict]:
        # Stessa logica di parsing di QuizUploadSerializer
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
        # Chi crea il template? Admin o Docente? Assumiamo Docente per ora
        creator: User = self.context['request'].user
        if not hasattr(creator, 'role') or creator.role not in ['Admin', 'Docente']:
             raise ValidationError("Solo Admin o Docenti possono creare template.")

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


        # Creazione QuizTemplate
        quiz_template_data = {
            'title': title,
            'description': f"Template generato automaticamente da {uploaded_file.name}",
            'metadata': {
                'source_file': uploaded_file.name,
                'generation_method': 'auto_upload'
            }
        }
        if creator.role == 'Admin':
            quiz_template_data['admin'] = creator
        else: # Docente
            quiz_template_data['teacher'] = creator

        quiz_template = QuizTemplate.objects.create(**quiz_template_data)


        # Creazione QuestionTemplate e AnswerOptionTemplate (Bulk)
        question_templates_to_create = []
        option_templates_to_create = []

        for q_data in parsed_questions:
            question_template = QuestionTemplate(
                quiz_template=quiz_template,
                text=q_data['text'],
                question_type=q_data['type'],
                order=q_data['order'],
                metadata={}
            )
            question_templates_to_create.append(question_template)

        created_question_templates = QuestionTemplate.objects.bulk_create(question_templates_to_create)
        question_template_map = {(qt.text, qt.order): qt for qt in created_question_templates}

        for q_data in parsed_questions:
             question_template_obj = question_template_map.get((q_data['text'], q_data['order']))
             if not question_template_obj:
                 logger.warning(f"QuestionTemplate '{q_data['text'][:50]}...' (ordine {q_data['order']}) non trovato dopo bulk_create.")
                 continue

             for opt_data in q_data['options']:
                 option_template = AnswerOptionTemplate(
                     question_template=question_template_obj,
                     text=opt_data['text'],
                     is_correct=opt_data['is_correct'],
                     order=opt_data['order']
                 )
                 option_templates_to_create.append(option_template)

        if option_templates_to_create:
            AnswerOptionTemplate.objects.bulk_create(option_templates_to_create)

        logger.info(f"Creato QuizTemplate '{quiz_template.title}' (ID: {quiz_template.id}) con {len(created_question_templates)} domande da {uploaded_file.name}")
        return QuizTemplateSerializer(quiz_template, context=self.context).data


# --- Assignment Serializers (MODIFICATI E NUOVI) ---

class QuizAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare un'assegnazione Quiz esistente (a Studente o Gruppo). """
    quiz = QuizSerializer(read_only=True) # Mostra dettagli quiz
    student = StudentBasicSerializer(read_only=True, allow_null=True) # Dettagli studente (se applicabile)
    group = StudentGroupBasicSerializer(read_only=True, allow_null=True) # Dettagli gruppo (se applicabile)

    class Meta:
        model = QuizAssignment
        fields = [
            'id',
            'quiz',
            'student',
            'group',
            'assigned_at',
            # Aggiungere eventuali altri campi rilevanti dal modello QuizAssignment
        ]
        read_only_fields = fields # Questo serializer è solo per la lettura


class PathwayAssignmentSerializer(serializers.ModelSerializer):
    """ Serializer per visualizzare un'assegnazione Pathway esistente (a Studente o Gruppo). """
    pathway = PathwaySerializer(read_only=True) # Mostra dettagli percorso
    student = StudentBasicSerializer(read_only=True, allow_null=True) # Dettagli studente (se applicabile)
    group = StudentGroupBasicSerializer(read_only=True, allow_null=True) # Dettagli gruppo (se applicabile)

    class Meta:
        model = PathwayAssignment
        fields = [
            'id',
            'pathway',
            'student',
            'group',
            'assigned_at',
            # Aggiungere eventuali altri campi rilevanti dal modello PathwayAssignment
        ]
        read_only_fields = fields # Questo serializer è solo per la lettura


class AssignQuizSerializer(serializers.Serializer):
    """ Serializer per l'AZIONE di assegnare un Quiz esistente a uno Studente o a un Gruppo. """
    quiz_id = serializers.PrimaryKeyRelatedField(
        queryset=Quiz.objects.all(), # Il docente potrà assegnare solo i suoi quiz (verificato nella view)
        required=True,
        help_text="ID del Quiz da assegnare."
    )
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), # Il docente potrà assegnare solo ai suoi studenti (verificato nella view)
        required=False,
        allow_null=True,
        help_text="ID dello Studente a cui assegnare (alternativo a group_id)."
    )
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=StudentGroup.objects.all(), # Il docente potrà assegnare solo ai suoi gruppi (verificato nella view)
        required=False,
        allow_null=True,
        help_text="ID del Gruppo a cui assegnare (alternativo a student_id)."
    )
    # assigned_at viene impostato automaticamente nella view

    def validate(self, attrs):
        student_id = attrs.get('student_id')
        group_id = attrs.get('group_id')

        if not student_id and not group_id:
            raise ValidationError("È necessario specificare 'student_id' o 'group_id'.")
        if student_id and group_id:
            raise ValidationError("Specificare solo 'student_id' o 'group_id', non entrambi.")

        # Ulteriori validazioni (es. appartenenza studente/gruppo al docente) verranno fatte nella view
        # per avere accesso al request.user e al quiz/pathway specifico.

        return attrs

    def create(self, validated_data):
        quiz = validated_data['quiz_id']
        student = validated_data.get('student_id')
        group = validated_data.get('group_id')
        teacher = self.context['request'].user # Assumendo che il contesto contenga la request

        # Verifica ownership (il docente può assegnare solo i suoi quiz/studenti/gruppi)
        if quiz.teacher != teacher:
             raise ValidationError("Non puoi assegnare un quiz che non hai creato.")
        if student and student.user_id != teacher.id: # Assumendo Student.user_id è FK a Docente
             raise ValidationError("Non puoi assegnare a uno studente non associato a te.")
        if group and group.teacher != teacher:
             raise ValidationError("Non puoi assegnare a un gruppo che non hai creato.")

        # Controlla se l'assegnazione esiste già
        assignment_exists = QuizAssignment.objects.filter(
            quiz=quiz,
            student=student, # Sarà None se group è specificato
            group=group      # Sarà None se student è specificato
        ).exists()

        if assignment_exists:
            target_type = "studente" if student else "gruppo"
            target_id = student.id if student else group.id
            raise ValidationError(f"Questo quiz è già assegnato a questo {target_type} (ID: {target_id}).")

        # Crea l'assegnazione
        assignment = QuizAssignment.objects.create(
            quiz=quiz,
            student=student,
            group=group,
            assigned_at=timezone.now()
        )
        return assignment # Restituisce l'oggetto creato

    def to_representation(self, instance):
        # Usa il serializer di visualizzazione per l'output
        return QuizAssignmentSerializer(instance, context=self.context).data


class AssignPathwaySerializer(serializers.Serializer):
    """ Serializer per l'AZIONE di assegnare un Pathway esistente a uno Studente o a un Gruppo. """
    pathway_id = serializers.PrimaryKeyRelatedField(
        queryset=Pathway.objects.all(), # Verificato nella view
        required=True,
        help_text="ID del Percorso da assegnare."
    )
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), # Verificato nella view
        required=False,
        allow_null=True,
        help_text="ID dello Studente a cui assegnare (alternativo a group_id)."
    )
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=StudentGroup.objects.all(), # Verificato nella view
        required=False,
        allow_null=True,
        help_text="ID del Gruppo a cui assegnare (alternativo a student_id)."
    )

    def validate(self, attrs):
        student_id = attrs.get('student_id')
        group_id = attrs.get('group_id')

        if not student_id and not group_id:
            raise ValidationError("È necessario specificare 'student_id' o 'group_id'.")
        if student_id and group_id:
            raise ValidationError("Specificare solo 'student_id' o 'group_id', non entrambi.")
        return attrs

    def create(self, validated_data):
        pathway = validated_data['pathway_id']
        student = validated_data.get('student_id')
        group = validated_data.get('group_id')
        teacher = self.context['request'].user

        # Verifica ownership
        if pathway.teacher != teacher:
             raise ValidationError("Non puoi assegnare un percorso che non hai creato.")
        if student and student.user_id != teacher.id:
             raise ValidationError("Non puoi assegnare a uno studente non associato a te.")
        if group and group.teacher != teacher:
             raise ValidationError("Non puoi assegnare a un gruppo che non hai creato.")

        # Controlla duplicati
        assignment_exists = PathwayAssignment.objects.filter(
            pathway=pathway,
            student=student,
            group=group
        ).exists()

        if assignment_exists:
            target_type = "studente" if student else "gruppo"
            target_id = student.id if student else group.id
            raise ValidationError(f"Questo percorso è già assegnato a questo {target_type} (ID: {target_id}).")

        # Crea assegnazione
        assignment = PathwayAssignment.objects.create(
            pathway=pathway,
            student=student,
            group=group,
            assigned_at=timezone.now()
        )
        return assignment

    def to_representation(self, instance):
        return PathwayAssignmentSerializer(instance, context=self.context).data


# --- Serializer per Tentativi e Progressi ---

# Serializer minimali per FK in StudentAnswerSerializer
class BasicQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'order', 'question_type']
        read_only_fields = fields

class BasicQuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ['id', 'status', 'started_at']
        read_only_fields = fields

class StudentAnswerSerializer(serializers.ModelSerializer):
    """ Serializer per inviare/visualizzare le risposte dello studente. """
    # Specifichiamo esplicitamente i serializer per le FK per chiarezza
    question = BasicQuestionSerializer(read_only=True)
    quiz_attempt = BasicQuizAttemptSerializer(read_only=True)

    class Meta:
        model = StudentAnswer
        fields = [
            'id',
            'quiz_attempt', # Serializzato da BasicQuizAttemptSerializer
            'question',     # Serializzato da BasicQuestionSerializer
            'selected_answers', # Questo è il campo JSON che contiene la risposta effettiva
            'is_correct',   # Impostato dal backend
            'score',        # Impostato dal backend
            'answered_at'   # Impostato dal backend
        ]
        # Il frontend invia solo 'selected_answers' (implicito, non in read_only)
        # Gli altri campi sono gestiti dal backend o sono relazioni in sola lettura
        read_only_fields = ['id', 'quiz_attempt', 'question', 'is_correct', 'score', 'answered_at']

    # Rimuoviamo il metodo validate custom, la validazione del contenuto
    # di selected_answers viene fatta nella view submit_answer


class QuizAttemptSerializer(serializers.ModelSerializer):
    """ Serializer base per i tentativi di quiz. """
    student_username = serializers.CharField(source='student.unique_identifier', read_only=True) # O altro campo identificativo
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    score = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True, allow_null=True)
    earned_badges = SimpleBadgeSerializer(many=True, read_only=True) # Mostra i badge guadagnati

    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'student', 'student_username', 'quiz', 'quiz_title', 'status', 'status_display',
            'score', 'started_at', 'completed_at', 'earned_badges' # Corretto: start_time -> started_at, end_time -> completed_at
        ]
        read_only_fields = [
            'id', 'student', 'student_username', 'quiz', 'quiz_title', 'status', 'status_display',
            'score', 'started_at', 'completed_at', 'earned_badges' # Corretto: start_time -> started_at, end_time -> completed_at
        ]

    def to_representation(self, instance):
        """ Nasconde alcuni campi se il tentativo non è completato. """
        ret = super().to_representation(instance)
        if instance.status != QuizAttempt.AttemptStatus.COMPLETED:
            ret.pop('score', None)
            ret.pop('end_time', None)
            ret.pop('earned_badges', None)
        # Potremmo voler nascondere anche le risposte date se non completato
        return ret


class QuizAttemptDetailSerializer(QuizAttemptSerializer):
    """ Serializer dettagliato per un tentativo, include risposte date e info aggiuntive. """
    student_answers = StudentAnswerSerializer(many=True, read_only=True)
    quiz = QuizSerializer(read_only=True) # Dettagli completi del quiz
    total_questions = serializers.SerializerMethodField()
    correct_answers_count = serializers.SerializerMethodField()
    completion_threshold = serializers.SerializerMethodField() # Soglia superamento (se definita)

    class Meta(QuizAttemptSerializer.Meta): # Eredita Meta dal genitore
        fields = [f for f in QuizAttemptSerializer.Meta.fields if f != 'student_answers'] + [
            'student_answers',
            'total_questions',
            'correct_answers_count',
            'completion_threshold',
            # Aggiungere altri campi se necessario
        ]
        # read_only_fields ereditati e aggiunti implicitamente

    def get_completion_threshold(self, obj: QuizAttempt) -> float | None:
        """ Restituisce la soglia di completamento del quiz, se definita. """
        # Assumendo che la soglia sia nei metadati del Quiz
        return obj.quiz.metadata.get('completion_threshold_percent')

    def get_total_questions(self, obj: QuizAttempt) -> int:
        """ Restituisce il numero totale di domande nel quiz. """
        return obj.quiz.questions.count()

    def get_correct_answers_count(self, obj: QuizAttempt) -> int:
        """ Conta le risposte corrette date dallo studente in questo tentativo. """
        if obj.status != QuizAttempt.AttemptStatus.COMPLETED: # Corretto: usa AttemptStatus
            return 0 # O None?
        # Conta le StudentAnswer dove l'opzione scelta è corretta
        # o dove la risposta aperta è stata marcata corretta (se implementato)
        correct_count = 0
        # Itera sulle risposte dello studente per questo tentativo
        for sa in obj.student_answers.all().select_related('question'):
            # Controlla direttamente il campo 'is_correct' della risposta dello studente.
            # Questo campo viene popolato dalla logica di valutazione (automatica o manuale).
            if sa.is_correct is True:
                 correct_count += 1
        return correct_count


class PathwayProgressSerializer(serializers.ModelSerializer):
    """ Serializer per il progresso dello studente in un percorso. """
    student_username = serializers.CharField(source='student.unique_identifier', read_only=True)
    pathway_title = serializers.CharField(source='pathway.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    current_quiz_title = serializers.CharField(source='current_quiz.title', read_only=True, allow_null=True)

    class Meta:
        model = PathwayProgress
        fields = [
            'id', 'student', 'student_username', 'pathway', 'pathway_title', 'status', 'status_display',
            'current_quiz', 'current_quiz_title', 'completed_quizzes_count', 'start_time', 'completion_time'
        ]
        read_only_fields = fields


# --- Serializers per Dashboard Studente (Potrebbero necessitare aggiornamenti per gruppi) ---

class SimpleQuizAttemptSerializer(serializers.ModelSerializer):
    """ Serializer minimale per rappresentare un tentativo in una lista. """
    class Meta:
        model = QuizAttempt
        fields = ['id', 'status', 'score', 'completed_at'] # Corretto: end_time -> completed_at


class StudentQuizDashboardSerializer(QuizSerializer):
    """ Serializer per i quiz nella dashboard studente, include stato ultimo tentativo. """
    latest_attempt = serializers.SerializerMethodField()
    attempts_count = serializers.SerializerMethodField()
    # Aggiungere campo per indicare se assegnato direttamente o via gruppo?
    assignment_type = serializers.SerializerMethodField()

    class Meta(QuizSerializer.Meta):
        fields = QuizSerializer.Meta.fields + ['latest_attempt', 'attempts_count', 'assignment_type']

    def get_latest_attempt(self, obj):
        """ Recupera l'ultimo tentativo dello studente per questo quiz. """
        student = self.context.get('student') # Assumendo studente nel contesto
        if not student: return None
        attempt = obj.attempts.filter(student=student).order_by('-started_at').first() # Corretto: usa started_at
        return SimpleQuizAttemptSerializer(attempt).data if attempt else None

    def get_attempts_count(self, obj):
        """ Conta i tentativi dello studente per questo quiz. """
        student = self.context.get('student')
        if not student: return 0
        return obj.attempts.filter(student=student).count()

    def get_assignment_type(self, obj):
        """ Determina se il quiz è assegnato direttamente o tramite gruppo. """
        student = self.context.get('student')
        if not student: return "unknown"

        # Verifica assegnazione diretta
        direct_assignment = QuizAssignment.objects.filter(quiz=obj, student=student).exists()
        if direct_assignment:
            return "direct"

        # Verifica assegnazione tramite gruppo
        # Interroga direttamente la tabella ponte per trovare gli ID dei gruppi dello studente
        student_groups = StudentGroupMembership.objects.filter(student=student).values_list('group_id', flat=True)
        group_assignment = QuizAssignment.objects.filter(quiz=obj, group_id__in=student_groups).exists()
        if group_assignment:
            return "group"

        return "unassigned" # O altro stato se non dovrebbe apparire


class SimplePathwayProgressSerializer(serializers.ModelSerializer):
     """ Serializer minimale per rappresentare un progresso in una lista. """
     class Meta:
        model = PathwayProgress
        fields = ['id', 'status', 'completed_at'] # Corretto: completion_time -> completed_at


class StudentPathwayDashboardSerializer(PathwaySerializer):
    """ Serializer per i percorsi nella dashboard studente, include stato ultimo progresso. """
    latest_progress = serializers.SerializerMethodField()
    # Aggiungere campo per indicare se assegnato direttamente o via gruppo?
    assignment_type = serializers.SerializerMethodField()

    class Meta(PathwaySerializer.Meta):
        fields = PathwaySerializer.Meta.fields + ['latest_progress', 'assignment_type']

    def get_latest_progress(self, obj):
        """ Recupera l'ultimo progresso dello studente per questo percorso. """
        student = self.context.get('student')
        if not student: return None
        progress = obj.progresses.filter(student=student).order_by('-started_at').first() # Usa related_name corretto e campo corretto
        return SimplePathwayProgressSerializer(progress).data if progress else None

    def get_assignment_type(self, obj):
        """ Determina se il percorso è assegnato direttamente o tramite gruppo. """
        student = self.context.get('student')
        if not student: return "unknown"

        direct_assignment = PathwayAssignment.objects.filter(pathway=obj, student=student).exists()
        if direct_assignment:
            return "direct"

        student_groups = student.group_memberships.values_list('group_id', flat=True)
        group_assignment = PathwayAssignment.objects.filter(pathway=obj, group_id__in=student_groups).exists()
        if group_assignment:
            return "group"

        return "unassigned"


# --- NUOVO Serializer per Tentativi Quiz nella Dashboard Studente ---

class StudentQuizAttemptDashboardSerializer(serializers.ModelSerializer):
    """
    Serializer per i tentativi di quiz nella dashboard studente.
    Mostra le informazioni del quiz e lo stato specifico di questo tentativo.
    """
    # Campi dal Quiz associato (Ora letti direttamente dal dizionario fornito dalla view)
    quiz_id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    available_from = serializers.DateTimeField(read_only=True, allow_null=True) # Allow null
    available_until = serializers.DateTimeField(read_only=True, allow_null=True) # Allow null
    metadata = serializers.JSONField(read_only=True)
    teacher_username = serializers.CharField(read_only=True, allow_null=True) # Allow null

    # Campi specifici del tentativo
    attempt_id = serializers.IntegerField(read_only=True, allow_null=True) # ID del tentativo (può essere null per PENDING)
    status = serializers.CharField(read_only=True) # Stato del tentativo (es. PENDING, IN_PROGRESS, COMPLETED, FAILED)
    score = serializers.FloatField(read_only=True, allow_null=True)
    started_at = serializers.DateTimeField(read_only=True, allow_null=True) # Allow null
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)

    # Legge direttamente dal dizionario fornito dalla view
    assignment_type = serializers.CharField(read_only=True)

    class Meta:
        # Ripristinato Meta.model, necessario per DRF anche se lavoriamo su dict
        model = QuizAttempt
        fields = [
            'attempt_id', 'quiz_id', 'title', 'description', 'status', 'score',
            'available_from', 'available_until', 'metadata', 'teacher_username',
            'started_at', 'completed_at', 'assignment_type'
        ]
        read_only_fields = fields # Tutti i campi sono derivati o di sola lettura in questo contesto

    # Rimosso: get_assignment_type non serve più, il valore viene letto direttamente dal dizionario
    # def get_assignment_type(self, obj): ...

    # Aggiunto per completezza, anche se read_only_fields copre tutto
    def create(self, validated_data):
        raise NotImplementedError("Questo serializer è di sola lettura.")

    def update(self, instance, validated_data):
        raise NotImplementedError("Questo serializer è di sola lettura.")


# --- Serializers Dettaglio Percorso per Studente ---

class NextPathwayQuizSerializer(serializers.ModelSerializer):
    """ Serializer per mostrare il prossimo quiz da fare in un percorso. """
    # Potrebbe includere dettagli del quiz o solo l'ID
    quiz_id = serializers.IntegerField(source='quiz.id')
    quiz_title = serializers.CharField(source='quiz.title')
    order = serializers.IntegerField()

    class Meta:
        model = PathwayQuiz
        fields = ['quiz_id', 'quiz_title', 'order']


class PathwayAttemptDetailSerializer(PathwaySerializer):
    """ Serializer dettagliato per un percorso quando visualizzato da uno studente. """
    progress = serializers.SerializerMethodField() # Mostra il progresso corrente dello studente
    next_quiz = serializers.SerializerMethodField() # Mostra il prossimo quiz da affrontare

    class Meta(PathwaySerializer.Meta):
        fields = PathwaySerializer.Meta.fields + ['progress', 'next_quiz']

    def get_progress(self, obj):
        student = self.context.get('student')
        if not student: return None
        progress = PathwayProgress.objects.filter(pathway=obj, student=student).first()
        return PathwayProgressSerializer(progress).data if progress else None

    def get_next_quiz(self, obj):
        student = self.context.get('student')
        if not student: return None
        progress = PathwayProgress.objects.filter(pathway=obj, student=student).first()

        if not progress or progress.status == PathwayProgress.StatusChoices.NOT_STARTED:
            # Se non iniziato, il prossimo è il primo quiz del percorso
            next_pq = obj.pathwayquiz_set.order_by('order').first()
        elif progress.status == PathwayProgress.StatusChoices.IN_PROGRESS:
            # Se in corso, il prossimo è quello dopo l'ultimo completato (o il corrente se esiste)
            if progress.current_quiz:
                 # Se c'è un current_quiz, significa che è stato iniziato ma non completato
                 # Quindi il prossimo è ancora current_quiz
                 current_pq = obj.pathwayquiz_set.filter(quiz=progress.current_quiz).first()
                 next_pq = current_pq # Il prossimo è quello corrente da finire
            else:
                 # Se non c'è current_quiz ma è IN_PROGRESS, cerca l'ultimo completato
                 last_completed_order = progress.completed_quizzes.aggregate(Max('order'))['order__max'] or -1
                 next_pq = obj.pathwayquiz_set.filter(order__gt=last_completed_order).order_by('order').first()
        else: # COMPLETED
            next_pq = None

        return NextPathwayQuizSerializer(next_pq).data if next_pq else None