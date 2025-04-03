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
    QuizAssignment # Importa QuizAssignment per la view
)
from apps.users.serializers import UserSerializer, StudentSerializer # Per info utente/studente
from apps.users.models import User # Aggiunto per associazione docente
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
        read_only=True # Le opzioni sono gestite tramite endpoint dedicati o nested write
    )
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)

    class Meta:
        model = QuestionTemplate
        fields = [
            'id', 'quiz_template', 'text', 'question_type', 'question_type_display',
            'order', 'metadata', 'answer_options'
        ]
        read_only_fields = ['quiz_template'] # Associato tramite URL


class QuizTemplateSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(source='admin.username', read_only=True)
    # Potremmo includere le domande nested in lettura, ma può essere pesante.
    # Meglio un endpoint separato per le domande di un template.
    # questions = QuestionTemplateSerializer(many=True, source='question_templates', read_only=True)

    class Meta:
        model = QuizTemplate
        fields = [
            'id', 'admin', 'admin_username', 'title', 'description', 'metadata', 'created_at'
            # 'questions' # Escluso per performance
        ]
        read_only_fields = ['admin', 'admin_username', 'created_at']


# --- Concrete Serializers ---

class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ['id', 'text', 'is_correct', 'order']


class QuestionSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionSerializer(
        many=True,
        # source='answer_options', # Rimosso perché ridondante
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
    # questions = QuestionSerializer(many=True, source='questions', read_only=True) # Escluso per performance

    class Meta:
        model = Quiz
        fields = [
            'id', 'teacher', 'teacher_username', 'source_template', 'title', 'description',
            'metadata', 'created_at', 'available_from', 'available_until'
            # 'questions' # Escluso
        ]
        read_only_fields = ['teacher', 'teacher_username', 'created_at']
        # Esplicitamente marca 'description' come non obbligatorio a livello di serializer
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True, 'allow_null': True}
        }


# --- Serializer per Upload Quiz ---

ALLOWED_UPLOAD_EXTENSIONS = ['.pdf', '.docx', '.md']

class QuizUploadSerializer(serializers.Serializer):
    """
    Serializer per gestire l'upload di file (PDF, DOCX, MD) per creare quiz.
    """
    file = serializers.FileField(required=True, help_text="File del quiz (.pdf, .docx, .md)")
    title = serializers.CharField(max_length=255, required=True, help_text="Titolo del nuovo quiz")
    # Aggiungere qui altri campi se necessario (es. description, metadata)

    def validate_file(self, value: UploadedFile):
        """Verifica l'estensione del file."""
        # Assicurati che il nome del file esista
        if not hasattr(value, 'name') or not value.name:
             raise ValidationError("Nome del file mancante o non valido.")

        # Estrai l'estensione in modo sicuro
        parts = value.name.split('.')
        if len(parts) < 2:
            raise ValidationError("Il file non ha un'estensione.")
        ext = '.' + parts[-1].lower()

        if ext not in ALLOWED_UPLOAD_EXTENSIONS:
            raise ValidationError(f"Tipo di file non supportato: {ext}. Sono permessi: {', '.join(ALLOWED_UPLOAD_EXTENSIONS)}")
        return value

    def _extract_text_from_pdf(self, file_obj: io.BytesIO) -> str:
        """Estrae testo da un oggetto file PDF."""
        try:
            reader = PdfReader(file_obj)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text: # Aggiungi solo se c'è testo estratto
                    text += page_text + "\n"
            if not text:
                 logger.warning("Nessun testo estratto dal PDF. Il file potrebbe essere vuoto, basato su immagini o protetto.")
            return text
        except Exception as e:
            logger.error(f"Errore durante l'estrazione del testo dal PDF: {e}", exc_info=True)
            raise ValidationError(f"Impossibile leggere il file PDF. Errore: {e}")

    def _extract_text_from_docx(self, file_obj: io.BytesIO) -> str:
        """Estrae testo da un oggetto file DOCX."""
        try:
            document = DocxDocument(file_obj)
            text = "\n".join([para.text for para in document.paragraphs if para.text])
            if not text:
                 logger.warning("Nessun testo estratto dal DOCX. Il file potrebbe essere vuoto.")
            return text
        except Exception as e:
            logger.error(f"Errore durante l'estrazione del testo dal DOCX: {e}", exc_info=True)
            raise ValidationError(f"Impossibile leggere il file DOCX. Errore: {e}")

    def _extract_text_from_md(self, file_obj: io.BytesIO) -> str:
        """Estrae testo da un oggetto file Markdown."""
        try:
            # Legge i byte e li decodifica in UTF-8 (o altro encoding se necessario)
            md_content = file_obj.read().decode('utf-8')
            # Converte Markdown in HTML, poi estrae il testo (approccio semplice)
            # Potrebbe essere necessario un parser HTML più robusto (es. BeautifulSoup)
            # per rimuovere tag HTML in modo più pulito.
            html = md_parser.markdown(md_content)
            # Semplice rimozione dei tag HTML con regex
            text = re.sub('<[^<]+?>', '', html).strip()
            if not text:
                 logger.warning("Nessun testo estratto dal Markdown dopo la conversione HTML.")
            return text
        except Exception as e:
            logger.error(f"Errore durante l'estrazione del testo dal Markdown: {e}", exc_info=True)
            raise ValidationError(f"Impossibile leggere il file Markdown. Errore: {e}")

    def _parse_quiz_text(self, text: str) -> list[dict]:
        """
        Analizza il testo estratto per identificare domande e opzioni.
        Questa è una implementazione di base e potrebbe necessitare di
        affinamenti significativi a seconda della formattazione del file.
        Assume domande numerate (es. "1.", "2.") e opzioni con lettere
        seguite da parentesi o punto (es. "A)", "B.", "C)").
        """
        questions = []
        current_question = None
        # Regex per identificare l'inizio di una domanda (numero seguito da punto o parentesi)
        # Rende il numero opzionale per gestire anche domande non numerate, ma dà priorità a quelle numerate
        question_start_re = re.compile(r"^\s*(?:(\d+)\s*[.)])?\s*(.*)", re.MULTILINE)
        # Regex per identificare un'opzione (lettera A-Z seguita da punto o parentesi)
        option_re = re.compile(r"^\s*([A-Z])\s*[.)]\s*(.*)", re.MULTILINE)
        # Regex per identificare linee vuote o di solo whitespace
        empty_line_re = re.compile(r"^\s*$")

        lines = text.splitlines()
        question_counter = 0 # Contatore per domande non numerate

        for line in lines:
            if empty_line_re.match(line):
                continue # Salta linee vuote

            line_stripped = line.strip()
            question_match = question_start_re.match(line) # Usiamo la linea originale per preservare indentazione potenziale
            option_match = option_re.match(line_stripped)

            # Heuristica: se una linea inizia con un numero seguito da punto/parentesi, è probabilmente una domanda.
            # Se inizia con una lettera maiuscola seguita da punto/parentesi, è probabilmente un'opzione.
            # Altrimenti, è parte del testo della domanda o dell'opzione precedente.

            is_likely_question_start = question_match and question_match.group(1) # Ha un numero?
            is_likely_option = option_match

            # Caso 1: Nuova domanda (con numero)
            if is_likely_question_start:
                if current_question:
                    questions.append(current_question)

                question_number = int(question_match.group(1))
                question_text = question_match.group(2).strip()
                question_counter = question_number # Aggiorna il contatore
                current_question = {
                    "text": question_text,
                    "order": question_number,
                    "options": [],
                    "type": QuestionType.MULTIPLE_CHOICE_SINGLE # Default - Usa QuestionType importato
                }

            # Caso 2: Opzione
            elif is_likely_option and current_question:
                option_letter = option_match.group(1)
                option_text = option_match.group(2).strip()
                current_question["options"].append({
                    "text": option_text,
                    "order": len(current_question["options"]) + 1,
                    "is_correct": False # Default
                })

            # Caso 3: Continuazione del testo (domanda o opzione) o domanda senza numero
            elif current_question:
                 # Se la linea precedente era un'opzione, accoda a quella
                 if current_question["options"] and not is_likely_question_start:
                     current_question["options"][-1]["text"] += " " + line_stripped
                 # Altrimenti, accoda al testo della domanda
                 else:
                     # Potrebbe essere l'inizio di una domanda *senza* numero?
                     # Se la domanda precedente aveva opzioni, è probabile sia una nuova domanda.
                     if current_question["options"] or not current_question["text"]:
                         if current_question["text"]: # Salva la domanda precedente se aveva testo
                             questions.append(current_question)
                         question_counter += 1
                         current_question = {
                             "text": line_stripped,
                             "order": question_counter,
                             "options": [],
                             "type": QuestionType.MULTIPLE_CHOICE_SINGLE # Default - Usa QuestionType importato
                         }
                     else: # Altrimenti è continuazione del testo della domanda
                        current_question["text"] += " " + line_stripped

            # Caso 4: Prima riga del file, probabilmente parte della prima domanda (senza numero)
            elif not current_question and line_stripped:
                 question_counter += 1
                 current_question = {
                     "text": line_stripped,
                     "order": question_counter,
                     "options": [],
                     "type": QuestionType.MULTIPLE_CHOICE_SINGLE # Default - Usa QuestionType importato
                 }


        if current_question:
            questions.append(current_question)

        # Filtra eventuali domande vuote create per errore
        questions = [q for q in questions if q.get("text")]

        # Riordina e assegna ordine sequenziale finale
        questions.sort(key=lambda q: q.get("order", float('inf')))
        for i, q in enumerate(questions):
            q["order"] = i + 1
            # Semplice heuristica per tipo domanda: se non ha opzioni, mettila come OpenAnswer
            if not q["options"]:
                q["type"] = QuestionType.OPEN_ANSWER_MANUAL # Usa QuestionType importato

        if not questions:
             raise ValidationError("Nessuna domanda valida trovata nel file. Verifica la formattazione (es. domande numerate, opzioni A/B/C).")

        return questions


    @transaction.atomic
    def create(self, validated_data):
        """
        Estrae il testo dal file, lo analizza, crea il Quiz e le relative Domande/Opzioni.
        """
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
                raise ValidationError("Tipo di file non gestito internamente.") # Sicurezza
        except ValidationError as e:
             # Rilancia l'errore specifico di estrazione
             raise e
        except Exception as e:
             # Cattura altri errori imprevisti durante l'estrazione
             logger.error(f"Errore imprevisto durante l'estrazione del testo da {uploaded_file.name}: {e}", exc_info=True)
             raise ValidationError(f"Errore imprevisto durante la lettura del file {file_ext}.")


        if not text or text.isspace():
             raise ValidationError(f"Impossibile estrarre contenuto testuale valido dal file {uploaded_file.name}.")

        try:
            parsed_questions = self._parse_quiz_text(text)
        except ValidationError as e:
             # Rilancia l'errore specifico del parsing
             raise e
        except Exception as e:
             # Cattura altri errori imprevisti durante il parsing
             logger.error(f"Errore imprevisto durante il parsing del testo da {uploaded_file.name}: {e}", exc_info=True)
             raise ValidationError("Errore imprevisto durante l'analisi del contenuto del file.")


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

        # Mappa per recuperare le domande create tramite un identificatore univoco (testo+ordine)
        # L'ordine da solo potrebbe non bastare se il parsing non è perfetto
        question_map = {(q.text, q.order): q for q in created_questions}

        for q_data in parsed_questions:
             # Cerca la domanda corrispondente nella mappa
             question_obj = question_map.get((q_data['text'], q_data['order']))
             if not question_obj:
                 logger.warning(f"Domanda '{q_data['text'][:50]}...' (ordine {q_data['order']}) non trovata dopo bulk_create.")
                 continue

             for opt_data in q_data['options']:
                 option = AnswerOption(
                     question=question_obj,
                     text=opt_data['text'],
                     is_correct=opt_data['is_correct'], # Sempre False inizialmente
                     order=opt_data['order']
                 )
                 options_to_create.append(option)

        if options_to_create:
            AnswerOption.objects.bulk_create(options_to_create)

        logger.info(f"Creato Quiz '{quiz.title}' (ID: {quiz.id}) con {len(created_questions)} domande da {uploaded_file.name}")

        # Usa QuizSerializer per restituire i dati del quiz creato
        return QuizSerializer(quiz, context=self.context).data


# --- Serializers Esistenti (continuano sotto) ---

class PathwayQuizSerializer(serializers.ModelSerializer):
    """ Serializer per la relazione M2M Pathway-Quiz (usato nested in Pathway). """
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)

    class Meta:
        model = PathwayQuiz
        fields = ['id', 'quiz', 'quiz_title', 'order']


class PathwaySerializer(serializers.ModelSerializer):
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    # Mostra i quiz nel percorso con il loro ordine
    quiz_details = PathwayQuizSerializer(source='pathwayquiz_set', many=True, read_only=True)

    class Meta:
        model = Pathway
        fields = [
            'id', 'teacher', 'teacher_username', 'title', 'description',
            'metadata', 'created_at', 'quiz_details'
        ]
        read_only_fields = ['teacher', 'teacher_username', 'created_at', 'quiz_details']


# --- Student Progress/Attempt Serializers ---

class StudentAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    question_type = serializers.CharField(source='question.question_type', read_only=True)
    selected_answers = serializers.JSONField() # Definisci esplicitamente il campo JSON

    class Meta:
        model = StudentAnswer
        fields = [
            'id', 'quiz_attempt', 'question', 'question_text', 'question_type',
            'selected_answers', 'is_correct', 'score', 'answered_at'
        ]
        read_only_fields = [
            'quiz_attempt', 'question', 'question_text', 'question_type',
            'is_correct', 'score', 'answered_at'
            # 'selected_answers' è scrivibile solo in fase di submit
        ]


class QuizAttemptSerializer(serializers.ModelSerializer):
    student_info = StudentSerializer(source='student', read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    # Opzionale: includere le risposte date dallo studente
    # student_answers = StudentAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'student', 'student_info', 'quiz', 'quiz_title', 'started_at',
            'completed_at', 'score', 'status', 'status_display'
            # 'student_answers' # Escluso per performance, usare endpoint dedicato
        ]
        read_only_fields = fields # Gli attempt sono gestiti da azioni specifiche


# Serializer dettagliato per QuizAttempt che include le domande
class QuizAttemptDetailSerializer(QuizAttemptSerializer):
    # Usa il QuestionSerializer che include già le AnswerOptionSerializer nested
    questions = QuestionSerializer(source='quiz.questions', many=True, read_only=True)
    # Potremmo aggiungere anche le risposte già date dallo studente per questo tentativo
    given_answers = StudentAnswerSerializer(source='student_answers', many=True, read_only=True)

    class Meta(QuizAttemptSerializer.Meta): # Eredita Meta dal serializer base
         fields = QuizAttemptSerializer.Meta.fields + ['questions', 'given_answers']
         read_only_fields = fields # Anche questo è read-only


class PathwayProgressSerializer(serializers.ModelSerializer):
    student_info = StudentSerializer(source='student', read_only=True)
    pathway_title = serializers.CharField(source='pathway.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PathwayProgress
        fields = [
            'id', 'student', 'student_info', 'pathway', 'pathway_title',
            'last_completed_quiz_order', 'started_at', 'completed_at', 'status', 'status_display'
        ]
        read_only_fields = fields # Il progresso è gestito internamente


# --- Serializers Specifici per Dashboard Studente ---

class SimpleQuizAttemptSerializer(serializers.ModelSerializer):
    """ Serializer semplificato per l'ultimo tentativo, usato nella dashboard. """
    class Meta:
        model = QuizAttempt
        fields = ['id', 'status', 'score', 'started_at', 'completed_at']
        read_only_fields = fields

class StudentQuizDashboardSerializer(QuizSerializer):
    """
    Serializer per i Quiz nella dashboard studente.
    Include informazioni sull'ultimo tentativo dello studente.
    """
    latest_attempt = SimpleQuizAttemptSerializer(read_only=True) # Campo per l'ultimo tentativo
    attempts_count = serializers.IntegerField(read_only=True) # Campo per il numero di tentativi

    class Meta(QuizSerializer.Meta): # Eredita Meta da QuizSerializer
        # Aggiungi i nuovi campi a quelli esistenti
        fields = QuizSerializer.Meta.fields + ['latest_attempt', 'attempts_count']
        read_only_fields = fields # Tutto è read-only in questo contesto


class SimplePathwayProgressSerializer(serializers.ModelSerializer):
    """ Serializer semplificato per il progresso del percorso, usato nella dashboard. """
    class Meta:
        model = PathwayProgress
        fields = ['status', 'last_completed_quiz_order', 'completed_at', 'points_earned'] # Aggiunto points_earned
        read_only_fields = fields

class StudentPathwayDashboardSerializer(PathwaySerializer):
    """
    Serializer per i Percorsi nella dashboard studente.
    Include informazioni sul progresso dello studente.
    """
    progress = SimplePathwayProgressSerializer(read_only=True) # Campo per il progresso

    class Meta(PathwaySerializer.Meta): # Eredita Meta da PathwaySerializer
        # Aggiungi il nuovo campo a quelli esistenti
        fields = PathwaySerializer.Meta.fields + ['progress']
        read_only_fields = fields # Tutto è read-only in questo contesto