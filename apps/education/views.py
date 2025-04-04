import logging # Import logging
from rest_framework import viewsets, permissions, status, serializers, generics, parsers # Import generics AND parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied as DRFPermissionDenied # Aggiunto import e rinominato per chiarezza
from django.db import transaction, models, IntegrityError # Import IntegrityError
from django.db.models import Max # Import Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import PermissionDenied # Import PermissionDenied Django
from django.db.models import F, OuterRef, Subquery, Count, Prefetch # Import per Subquery, Count e Prefetch

from .models import (
    QuizTemplate, QuestionTemplate, AnswerOptionTemplate,
    Quiz, Question, AnswerOption, Pathway, PathwayQuiz,
    QuizAttempt, StudentAnswer, PathwayProgress, QuestionType,
    QuizAssignment, PathwayAssignment # Importa i modelli Assignment
)
from .serializers import (
    QuizTemplateSerializer, QuestionTemplateSerializer, AnswerOptionTemplateSerializer,
    QuizSerializer, QuestionSerializer, AnswerOptionSerializer, PathwaySerializer, PathwayQuizSerializer, # Aggiunto PathwayQuizSerializer
    QuizAttemptSerializer, StudentAnswerSerializer, PathwayProgressSerializer,
    QuizAttemptDetailSerializer, # Importa il nuovo serializer
    StudentQuizDashboardSerializer, StudentPathwayDashboardSerializer, # Importa i nuovi serializer
    QuizUploadSerializer, # Aggiunto QuizUploadSerializer
    SimpleQuizAttemptSerializer, # Importa SimpleQuizAttemptSerializer
    PathwayAttemptDetailSerializer, # Importa il serializer per la nuova view
    NextPathwayQuizSerializer # Aggiunto import mancante
)
from .permissions import (
    IsAdminOrReadOnly, IsQuizTemplateOwnerOrAdmin, IsQuizOwnerOrAdmin, IsPathwayOwnerOrAdmin, # Updated IsPathwayOwner -> IsPathwayOwnerOrAdmin
    IsStudentOwnerForAttempt, IsTeacherOfStudentForAttempt, IsAnswerOptionOwner # Aggiunto IsAnswerOptionOwner
    # Rimosso IsTeacherOwner che non esiste
)
from apps.users.permissions import IsAdminUser, IsTeacherUser, IsStudent, IsStudentAuthenticated # Import IsStudentAuthenticated
from apps.users.models import UserRole, Student, User # Import modelli utente e User
from apps.rewards.models import Wallet, PointTransaction # Import Wallet e PointTransaction
from .models import QuizAssignment, PathwayAssignment, QuizAttempt, PathwayProgress # Assicurati che siano importati

# Get an instance of a logger
logger = logging.getLogger(__name__)

# --- ViewSets per Admin (Templates) ---
class QuizTemplateViewSet(viewsets.ModelViewSet):
    """ API endpoint per i Quiz Templates (Admin). """
    serializer_class = QuizTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser] # Solo Admin

    def get_queryset(self):
        return QuizTemplate.objects.all()

    def perform_create(self, serializer):
        serializer.save(admin=self.request.user)

class QuestionTemplateViewSet(viewsets.ModelViewSet):
    """ API endpoint per le Question Templates (gestite nel contesto di un QuizTemplate). """
    serializer_class = QuestionTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        # Filtra per il quiz template specificato nell'URL
        return QuestionTemplate.objects.filter(quiz_template_id=self.kwargs['quiz_template_pk'])

    def perform_create(self, serializer):
        quiz_template = get_object_or_404(QuizTemplate, pk=self.kwargs['quiz_template_pk'])
        serializer.save(quiz_template=quiz_template)

class AnswerOptionTemplateViewSet(viewsets.ModelViewSet):
     """ API endpoint per le Answer Option Templates (gestite nel contesto di una QuestionTemplate). """
     serializer_class = AnswerOptionTemplateSerializer
     permission_classes = [permissions.IsAuthenticated, IsAdminUser]

     def get_queryset(self):
         return AnswerOptionTemplate.objects.filter(question_template_id=self.kwargs['question_template_pk'])

     def perform_create(self, serializer):
         question_template = get_object_or_404(QuestionTemplate, pk=self.kwargs['question_template_pk'])
         serializer.save(question_template=question_template)


# --- ViewSets per Docenti (Contenuti Concreti) ---
class QuizViewSet(viewsets.ModelViewSet):
    """ API endpoint per i Quiz concreti (Docente). """
    serializer_class = QuizSerializer
    # Modificato: Usiamo permessi più generali a livello di ViewSet.
    # IsAuthenticated garantisce che l'utente sia loggato.
    # (IsTeacherUser | IsAdminUser) garantisce che sia un docente o un admin.
    # La logica di get_queryset e i permessi a livello di oggetto (controllati da DRF per retrieve/update/delete)
    # gestiranno l'accesso specifico ai dati.
    # Usiamo IsQuizOwnerOrAdmin per gestire l'accesso a livello di oggetto
    permission_classes = [permissions.IsAuthenticated, IsQuizOwnerOrAdmin]

    def get_queryset(self):
        """
        Filtra i quiz: l'admin vede tutto, il docente vede solo i propri.
        IsQuizOwnerOrAdmin gestirà l'accesso specifico per retrieve/update/delete.
        """
        user = self.request.user

        if isinstance(user, User) and user.is_admin:
            # Admin vede tutto
            return Quiz.objects.all().select_related('teacher')
        elif isinstance(user, User) and user.is_teacher: # Manteniamo user.is_teacher se è corretto nel contesto
            # Docente vede solo i propri quiz
            return Quiz.objects.filter(teacher=user).select_related('teacher')
        # Altri tipi di utenti (es. Studente) non dovrebbero poter accedere a questa view
        # a causa dei permessi, ma per sicurezza restituiamo un queryset vuoto.
        return Quiz.objects.none()

    def perform_create(self, serializer):
        if not isinstance(self.request.user, User) or not self.request.user.is_teacher:
             raise serializers.ValidationError("Solo i Docenti possono creare quiz.")
        serializer.save(teacher=self.request.user)

    @action(detail=False, methods=['post'], url_path='create-from-template', permission_classes=[permissions.IsAuthenticated, IsTeacherUser])
    def create_from_template(self, request):
        template_id = request.data.get('template_id')
        if not template_id:
            return Response({'template_id': 'Questo campo è richiesto.'}, status=status.HTTP_400_BAD_REQUEST)

        template = get_object_or_404(QuizTemplate, pk=template_id)
        new_quiz = None

        try:
            with transaction.atomic():
                new_quiz = Quiz.objects.create(
                    teacher=request.user,
                    source_template=template,
                    title=request.data.get('title', template.title),
                    description=template.description,
                    metadata=template.metadata
                )
                for q_template in template.question_templates.prefetch_related('answer_option_templates').all():
                    new_question = Question.objects.create(
                        quiz=new_quiz,
                        text=q_template.text,
                        question_type=q_template.question_type,
                        order=q_template.order,
                        metadata=q_template.metadata
                    )
                    for opt_template in q_template.answer_option_templates.all():
                        AnswerOption.objects.create(
                            question=new_question,
                            text=opt_template.text,
                            is_correct=opt_template.is_correct,
                            order=opt_template.order
                        )
            serializer = self.get_serializer(new_quiz)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'detail': f'Errore durante la creazione da template: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # --- Azioni Specifiche Docente ---

    @action(detail=False, methods=['post'], url_path='upload', permission_classes=[permissions.IsAuthenticated, IsTeacherUser], parser_classes=[parsers.MultiPartParser, parsers.FormParser])
    def upload_quiz(self, request, *args, **kwargs):
        """
        Permette a un docente di caricare un file (PDF, DOCX, MD) per creare un quiz.
        Richiede 'file' e 'title' nei dati della richiesta (form-data).
        """
        serializer = QuizUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                # Il metodo create del serializer gestisce l'estrazione, il parsing e la creazione
                quiz_data = serializer.save() # .save() chiama .create()
                # Restituisce i dati del quiz creato (formattati da QuizSerializer dentro QuizUploadSerializer)
                return Response(quiz_data, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                # Se il serializer.create solleva ValidationError (es. parsing fallito, testo vuoto)
                logger.warning(f"Errore di validazione durante upload quiz da utente {request.user.id}: {e.detail}")
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                # Cattura altri errori imprevisti durante la creazione
                logger.error(f"Errore imprevisto durante l'upload del quiz da utente {request.user.id}: {e}", exc_info=True)
                return Response({"detail": "Errore interno durante la creazione del quiz dal file."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Errori di validazione del serializer (es. file mancante, titolo mancante, tipo file errato)
            logger.warning(f"Errore di validazione dati upload quiz da utente {request.user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='assign-student', permission_classes=[permissions.IsAuthenticated, IsQuizOwnerOrAdmin]) # Removed permissions. prefix
    def assign_student(self, request, pk=None):
        quiz = self.get_object()
        student_id = request.data.get('student_id')
        if not student_id:
             return Response({'student_id': 'ID studente richiesto.'}, status=status.HTTP_400_BAD_REQUEST)

        student = get_object_or_404(Student, pk=student_id, teacher=request.user)

        assignment, created = QuizAssignment.objects.get_or_create(
            quiz=quiz,
            student=student,
            defaults={'assigned_by': request.user}
        )

        if created:
            return Response({'status': 'Quiz assegnato con successo.'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'Quiz già assegnato a questo studente.'}, status=status.HTTP_200_OK)

from django.db.models import F # Assicurati che F sia importato all'inizio del file

class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    # Permetti a Docenti o Admin
    permission_classes = [(IsTeacherUser | IsAdminUser)]

    def get_queryset(self):
        quiz = get_object_or_404(Quiz, pk=self.kwargs['quiz_pk'])
        # Verifica ownership o ruolo admin
        if not isinstance(self.request.user, User) or (not self.request.user.is_admin and quiz.teacher != self.request.user):
             raise DRFPermissionDenied("Non hai accesso a questo quiz.") # Usa DRFPermissionDenied
        # Ordina per 'order' per coerenza
        return Question.objects.filter(quiz=quiz).order_by('order')

    def perform_create(self, serializer):
        quiz = get_object_or_404(Quiz, pk=self.kwargs['quiz_pk'])
        if not isinstance(self.request.user, User) or quiz.teacher != self.request.user:
             raise DRFPermissionDenied("Non puoi aggiungere domande a questo quiz.") # Usa DRFPermissionDenied
        # Calcola il prossimo ordine disponibile
        last_order = Question.objects.filter(quiz=quiz).aggregate(Max('order'))['order__max']
        # L'ordine parte da 1, non da 0
        next_order = 1 if last_order is None else last_order + 1
        # Salva la domanda con il quiz e l'ordine calcolato
        serializer.save(quiz=quiz, order=next_order)

    @transaction.atomic # Assicura che l'eliminazione e il riordino avvengano insieme
    def perform_destroy(self, instance):
        """
        Elimina la domanda e riordina le domande successive nello stesso quiz.
        """
        quiz = instance.quiz
        deleted_order = instance.order
        instance.delete()

        # Riordina le domande successive
        questions_to_reorder = Question.objects.filter(
            quiz=quiz,
            order__gt=deleted_order
        ).order_by('order')

        # Aggiorna l'ordine in modo efficiente se possibile
        # Nota: bulk_update potrebbe non funzionare direttamente con F() in tutte le versioni/DB
        # Un approccio più sicuro è iterare, ma meno performante per molti aggiornamenti.
        # Tentativo con update() e F():
        updated_count = questions_to_reorder.update(order=F('order') - 1)
        logger.info(f"Riordinate {updated_count} domande nel quiz {quiz.id} dopo l'eliminazione della domanda con ordine {deleted_order}.")

        # Fallback se update() non funziona come previsto o per maggiore robustezza:
        # questions_list = list(questions_to_reorder) # Esegui la query
        # for i, question in enumerate(questions_list):
        #     question.order = deleted_order + i # Assegna il nuovo ordine sequenziale
        # Question.objects.bulk_update(questions_list, ['order'])
        # logger.info(f"Riordinate {len(questions_list)} domande nel quiz {quiz.id} dopo l'eliminazione.")

class AnswerOptionViewSet(viewsets.ModelViewSet):
     serializer_class = AnswerOptionSerializer
     # Usa il nuovo permesso IsAnswerOptionOwner
     permission_classes = [IsAnswerOptionOwner]

     def get_queryset(self):
         question = get_object_or_404(Question, pk=self.kwargs['question_pk'])
         # Verifica ownership o ruolo admin
         if not isinstance(self.request.user, User) or (not self.request.user.is_admin and question.quiz.teacher != self.request.user):
              raise DRFPermissionDenied("Non hai accesso a questa domanda.") # Usa DRFPermissionDenied
         return AnswerOption.objects.filter(question=question)

     def perform_create(self, serializer):
         question = get_object_or_404(Question, pk=self.kwargs['question_pk'])
         if not isinstance(self.request.user, User) or question.quiz.teacher != self.request.user:
              raise DRFPermissionDenied("Non puoi aggiungere opzioni a questa domanda.") # Usa DRFPermissionDenied
         # Calcola il prossimo ordine disponibile per questa domanda
         last_order = AnswerOption.objects.filter(question=question).aggregate(Max('order'))['order__max']
         # L'ordine parte da 1 (o dal successivo se esistono già opzioni)
         next_order = 1 if last_order is None else last_order + 1
         # Salva l'opzione con la domanda e l'ordine calcolato
         serializer.save(question=question, order=next_order)

class PathwayViewSet(viewsets.ModelViewSet):
    """ API endpoint per i Percorsi (Docente). """
    serializer_class = PathwaySerializer
    permission_classes = [permissions.IsAuthenticated, IsPathwayOwnerOrAdmin] # Updated permission

    def get_queryset(self):
        user = self.request.user

        # Allow DRF to find the object for detail actions. Permissions handle access.
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'add_quiz', 'assign_student_pathway']: # Added detail/custom actions
            return Pathway.objects.all().select_related('teacher').prefetch_related('pathwayquiz_set__quiz')

        # Standard filtering for list action.
        if isinstance(user, User) and user.is_admin:
            return Pathway.objects.all().select_related('teacher').prefetch_related('pathwayquiz_set__quiz')
        elif isinstance(user, User) and user.is_teacher:
            return Pathway.objects.filter(teacher=user).select_related('teacher').prefetch_related('pathwayquiz_set__quiz')
        # Empty list for students or others.
        return Pathway.objects.none()

    def perform_create(self, serializer):
        if not isinstance(self.request.user, User) or not self.request.user.is_teacher:
             raise serializers.ValidationError("Solo i Docenti possono creare percorsi.")
        serializer.save(teacher=self.request.user)

    @action(detail=True, methods=['post'], url_path='add-quiz', permission_classes=[permissions.IsAuthenticated, IsPathwayOwnerOrAdmin]) # Updated permission
    def add_quiz(self, request, pk=None):
        pathway = self.get_object()
        quiz_id = request.data.get('quiz_id')
        order = request.data.get('order')

        if not quiz_id or order is None:
            return Response({'detail': 'quiz_id e order sono richiesti.'}, status=status.HTTP_400_BAD_REQUEST)

        quiz = get_object_or_404(Quiz, pk=quiz_id, teacher=request.user)

        try:
            order = int(order)
            if order < 0: raise ValueError()
        except (ValueError, TypeError):
            return Response({'order': 'L\'ordine deve essere un intero non negativo.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica se l'ordine è già occupato da un *altro* quiz in questo percorso
        existing_entry_with_order = PathwayQuiz.objects.filter(
            pathway=pathway,
            order=order
        ).exclude(quiz=quiz).first() # Escludi il quiz corrente (per permettere l'update dell'ordine dello stesso quiz)

        if existing_entry_with_order:
            return Response(
                {'order': f'L\'ordine {order} è già utilizzato dal quiz "{existing_entry_with_order.quiz.title}" in questo percorso.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Procedi con update_or_create (sicuro ora che l'ordine non è usato da altri quiz)
            pathway_quiz, created = PathwayQuiz.objects.update_or_create(
                pathway=pathway,
                quiz=quiz,
                defaults={'order': order}
            )
            return Response(PathwayQuizSerializer(pathway_quiz).data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
        except IntegrityError as e:
             # Questo non dovrebbe più accadere per il vincolo (pathway, order),
             # ma potrebbe esserci un altro IntegrityError (es. (pathway, quiz) se non gestito da update_or_create?)
             logger.error(f"Errore di integrità imprevisto aggiungendo quiz {quiz_id} a percorso {pathway.id}: {e}", exc_info=True)
             return Response({'detail': 'Errore di integrità durante l\'aggiunta del quiz al percorso.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='assign-student', permission_classes=[permissions.IsAuthenticated, IsPathwayOwnerOrAdmin]) # Updated permission
    def assign_student_pathway(self, request, pk=None):
        pathway = self.get_object()
        student_id = request.data.get('student_id')
        if not student_id:
             return Response({'student_id': 'ID studente richiesto.'}, status=status.HTTP_400_BAD_REQUEST)

        student = get_object_or_404(Student, pk=student_id, teacher=request.user)

        assignment, created = PathwayAssignment.objects.get_or_create(
            pathway=pathway,
            student=student,
            defaults={'assigned_by': request.user}
        )

        if created:
            return Response({'status': 'Percorso assegnato con successo.'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'Percorso già assegnato a questo studente.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], url_path='remove-quiz/(?P<pathway_quiz_pk>[^/.]+)', permission_classes=[permissions.IsAuthenticated, IsPathwayOwnerOrAdmin])
    def remove_quiz(self, request, pk=None, pathway_quiz_pk=None):
        """
        Rimuove una specifica relazione PathwayQuiz (un quiz da un percorso).
        """
        pathway = self.get_object() # Assicura che l'utente abbia accesso al percorso

        try:
            # Trova la specifica relazione PathwayQuiz da eliminare
            pathway_quiz_entry = get_object_or_404(
                PathwayQuiz,
                pk=pathway_quiz_pk,
                pathway=pathway # Assicura che appartenga al percorso corretto
            )
            deleted_order = pathway_quiz_entry.order
            quiz_title = pathway_quiz_entry.quiz.title # Per logging
            pathway_quiz_entry.delete()

            # Opzionale ma consigliato: Riordina i quiz successivi nel percorso
            # Simile a QuestionViewSet.perform_destroy
            quizzes_to_reorder = PathwayQuiz.objects.filter(
                pathway=pathway,
                order__gt=deleted_order
            ).order_by('order')
            updated_count = quizzes_to_reorder.update(order=F('order') - 1)
            logger.info(f"Rimosso quiz '{quiz_title}' (relazione {pathway_quiz_pk}) e riordinate {updated_count} voci nel percorso {pathway.id}.")

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404: # Importa Http404 da django.http se non già fatto
             return Response({'detail': 'Relazione Quiz-Percorso non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Errore durante la rimozione del quiz (relazione {pathway_quiz_pk}) dal percorso {pk}: {e}", exc_info=True)
            return Response({'detail': 'Errore interno durante la rimozione del quiz dal percorso.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- ViewSets per Studenti (Svolgimento) ---

class StudentDashboardViewSet(viewsets.ViewSet):
     """ Endpoint per lo studente per vedere cosa gli è stato assegnato. """
     permission_classes = [IsStudentAuthenticated] # Solo Studenti autenticati

     def list(self, request):
         student = request.user # Ora request.user è lo studente
         # Rimosso controllo 'if not student:' perché IsStudentAuthenticated garantisce che ci sia

         assigned_quiz_ids = QuizAssignment.objects.filter(student=student).values_list('quiz_id', flat=True)
         assigned_pathway_ids = PathwayAssignment.objects.filter(student=student).values_list('pathway_id', flat=True)

         assigned_quizzes = Quiz.objects.filter(id__in=assigned_quiz_ids)
         assigned_pathways = Pathway.objects.filter(id__in=assigned_pathway_ids)

         quiz_serializer = QuizSerializer(assigned_quizzes, many=True, context={'request': request})
         pathway_serializer = PathwaySerializer(assigned_pathways, many=True, context={'request': request})

         return Response({
             "assigned_quizzes": quiz_serializer.data,
             "assigned_pathways": pathway_serializer.data
         })


class StudentQuizAttemptViewSet(viewsets.GenericViewSet):
    """ Gestisce l'inizio di un Quiz da parte dello Studente (spostato da QuizViewSet). """
    permission_classes = [IsStudentAuthenticated] # Solo Studenti autenticati
    serializer_class = QuizAttemptSerializer # Per output base

    # POST /api/education/quizzes/{quiz_pk}/start-attempt/
    @action(detail=False, methods=['post'], url_path='start-attempt')
    def start_attempt(self, request, quiz_pk=None):
         quiz = get_object_or_404(Quiz, pk=quiz_pk)
         student = request.user # Ora request.user è lo studente
         # Rimosso controllo 'if not student:'

         # Verifica se il quiz è assegnato direttamente
         is_directly_assigned = QuizAssignment.objects.filter(student=student, quiz=quiz).exists()

         # Verifica se il quiz fa parte di un percorso assegnato (query alternativa corretta)
         is_in_assigned_pathway = Pathway.objects.filter(
             assignments__student=student,      # Usa il related_name corretto 'assignments'
             pathwayquiz__quiz=quiz             # Usa 'pathwayquiz' come suggerito da FieldError
         ).exists()

         if not is_directly_assigned and not is_in_assigned_pathway:
             logger.warning(f"Tentativo accesso non autorizzato a quiz {quiz.id} da studente {student.id}. Assegnato direttamente: {is_directly_assigned}, In percorso assegnato: {is_in_assigned_pathway}")
             return Response({'detail': 'Questo quiz non ti è stato assegnato direttamente o tramite un percorso.'}, status=status.HTTP_403_FORBIDDEN)

         existing_attempt = QuizAttempt.objects.filter(student=student, quiz=quiz, status=QuizAttempt.AttemptStatus.IN_PROGRESS).first()
         if existing_attempt:
             serializer = QuizAttemptDetailSerializer(existing_attempt, context={'request': request})
             return Response(serializer.data, status=status.HTTP_200_OK)

         attempt = QuizAttempt.objects.create(student=student, quiz=quiz)
         serializer = QuizAttemptDetailSerializer(attempt, context={'request': request})
         return Response(serializer.data, status=status.HTTP_201_CREATED)


# NUOVO ViewSet per gestire un tentativo specifico
class AttemptViewSet(viewsets.GenericViewSet):
    """ Gestisce le azioni su un tentativo di quiz specifico (submit, complete). """
    queryset = QuizAttempt.objects.all()
    # Usa IsStudentAuthenticated
    permission_classes = [IsStudentAuthenticated, IsStudentOwnerForAttempt] # Solo lo studente proprietario

    # GET /api/education/attempts/{pk}/details/
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        attempt = self.get_object() # get_object usa queryset e pk dall'URL
        serializer = QuizAttemptDetailSerializer(attempt, context={'request': request})
        return Response(serializer.data)

    # GET /api/education/attempts/{pk}/current-question/
    @action(detail=True, methods=['get'], url_path='current-question')
    def current_question(self, request, pk=None):
        """ Restituisce la prossima domanda non risposta nel tentativo. """
        attempt = self.get_object()
        if attempt.status != QuizAttempt.AttemptStatus.IN_PROGRESS:
            return Response({'detail': 'Questo tentativo non è più in corso.'}, status=status.HTTP_400_BAD_REQUEST)

        # Ottieni tutte le domande del quiz ordinate
        all_questions = attempt.quiz.questions.prefetch_related('answer_options').order_by('order') # Aggiunto prefetch_related
        # Ottieni gli ID delle domande già risposte in questo tentativo
        answered_question_ids = set(attempt.student_answers.values_list('question_id', flat=True))

        next_question = None
        for question in all_questions:
            if question.id not in answered_question_ids:
                next_question = question
                break # Trovata la prima domanda non risposta

        if next_question:
            # Serializza e restituisci la domanda corrente
            serializer = QuestionSerializer(next_question, context={'request': request})
            return Response(serializer.data)
        else:
            # Se non ci sono più domande non risposte, ma il tentativo è ancora in corso
            # (l'utente potrebbe non aver ancora chiamato 'complete'),
            # restituisci 204 No Content per indicare che non c'è una *prossima* domanda.
            return Response(status=status.HTTP_204_NO_CONTENT)

    # POST /api/education/attempts/{pk}/submit-answer/
    @action(detail=True, methods=['post'], url_path='submit-answer')
    def submit_answer(self, request, pk=None):
        attempt = self.get_object()
        if attempt.status != QuizAttempt.AttemptStatus.IN_PROGRESS:
            return Response({'detail': 'Questo tentativo non è più in corso.'}, status=status.HTTP_400_BAD_REQUEST)

        question_id = request.data.get('question_id')
        selected_answers_data = request.data.get('selected_answers') # Formato dipende dal tipo di domanda

        if question_id is None or selected_answers_data is None:
             return Response({'detail': 'question_id e selected_answers sono richiesti.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            question = Question.objects.get(pk=question_id, quiz=attempt.quiz)
        except Question.DoesNotExist:
             return Response({'detail': 'Domanda non trovata in questo quiz.'}, status=status.HTTP_404_NOT_FOUND)

        # Validazione di selected_answers_data in base a question.question_type
        logger.info(f"Attempt {pk} - Submit Answer - Raw request.data: {request.data}") # LOGGING
        logger.info(f"Attempt {pk} - Submit Answer - Extracted selected_answers_data: {selected_answers_data}") # LOGGING
        logger.info(f"Attempt {pk} - Submit Answer - Type of selected_answers_data: {type(selected_answers_data)}") # LOGGING
        validation_error = None
        valid_data_for_storage = {} # Dati validati da salvare

        q_type = question.question_type
        if q_type in [QuestionType.MULTIPLE_CHOICE_SINGLE, QuestionType.TRUE_FALSE]:
            # Modificato per aspettarsi 'answer_option_id'
            if not isinstance(selected_answers_data, dict) or 'answer_option_id' not in selected_answers_data:
                validation_error = "Per questo tipo di domanda, 'selected_answers' deve essere un dizionario con chiave 'answer_option_id'."
            else:
                selected_id = selected_answers_data['answer_option_id'] # Modificato per usare la chiave corretta
                # Permetti None per deselezionare? Se sì, aggiungere 'or selected_id is None'
                # Modificato messaggio di errore
                if not isinstance(selected_id, int):
                    validation_error = "'answer_option_id' deve essere un intero."
                else:
                    # Verifica che l'opzione esista per questa domanda
                    # Modificato messaggio di errore
                    if not question.answer_options.filter(pk=selected_id).exists():
                        validation_error = f"L'opzione con ID {selected_id} ('answer_option_id') non è valida per questa domanda."
                    else:
                        # Dati validi per il salvataggio
                        valid_data_for_storage = {'answer_option_id': selected_id} # Modificato per salvare la chiave corretta

        elif q_type == QuestionType.MULTIPLE_CHOICE_MULTIPLE:
            # Modificato per aspettarsi 'answer_option_ids'
            if not isinstance(selected_answers_data, dict) or 'answer_option_ids' not in selected_answers_data:
                validation_error = "Per questo tipo di domanda, 'selected_answers' deve essere un dizionario con chiave 'answer_option_ids'."
            else:
                selected_ids = selected_answers_data['answer_option_ids'] # Modificato per usare la chiave corretta
                # Modificato messaggio di errore
                if not isinstance(selected_ids, list) or not all(isinstance(i, int) for i in selected_ids):
                    validation_error = "'answer_option_ids' deve essere una lista di interi."
                else:
                    # Verifica che tutte le opzioni esistano per questa domanda
                    valid_option_ids = set(question.answer_options.values_list('id', flat=True))
                    submitted_ids_set = set(selected_ids)
                    if not submitted_ids_set.issubset(valid_option_ids):
                        invalid_ids = submitted_ids_set - valid_option_ids
                        # Modificato messaggio di errore
                        validation_error = f"Le seguenti opzioni ('answer_option_ids') non sono valide per questa domanda: {list(invalid_ids)}."
                    else:
                        # Dati validi per il salvataggio
                        valid_data_for_storage = {'answer_option_ids': sorted(list(submitted_ids_set))} # Salva come lista ordinata

        elif q_type == QuestionType.FILL_BLANK:
            # Modificato per aspettarsi 'answers' come lista di stringhe
            if not isinstance(selected_answers_data, dict) or 'answers' not in selected_answers_data:
                 validation_error = "Per questo tipo di domanda, 'selected_answers' deve essere un dizionario con chiave 'answers'."
            else:
                answers = selected_answers_data['answers']
                # Modificato messaggio di errore
                if not isinstance(answers, list) or not all(isinstance(a, str) for a in answers):
                    validation_error = "'answers' deve essere una lista di stringhe."
                else:
                    # Verifica che il numero di risposte corrisponda agli spazi vuoti attesi (se definito in metadata)
                    expected_blanks = question.metadata.get('blanks_count')
                    if expected_blanks is not None and len(answers) != expected_blanks:
                        validation_error = f"Numero di risposte ('answers') non corretto. Attesi {expected_blanks}, ricevuti {len(answers)}."
                    else:
                        # Dati validi per il salvataggio
                        valid_data_for_storage = {'answers': answers} # Modificato per salvare la chiave corretta

        elif q_type == QuestionType.OPEN_ANSWER_MANUAL:
            # Modificato per aspettarsi 'text'
            if not isinstance(selected_answers_data, dict) or 'text' not in selected_answers_data:
                 validation_error = "Per questo tipo di domanda, 'selected_answers' deve essere un dizionario con chiave 'text'."
            else:
                answer_text = selected_answers_data['text'] # Modificato per usare la chiave corretta
                # Modificato messaggio di errore
                if not isinstance(answer_text, str):
                    validation_error = "'text' deve essere una stringa."
                else:
                    # Dati validi per il salvataggio
                    valid_data_for_storage = {'text': answer_text} # Modificato per salvare la chiave corretta

        else:
            validation_error = f"Tipo di domanda non supportato: {q_type}"

        if validation_error:
            logger.warning(f"Attempt {pk} - Submit Answer - Validation Error: {validation_error}") # LOGGING
            return Response({'selected_answers': validation_error}, status=status.HTTP_400_BAD_REQUEST)

        # Crea o aggiorna la risposta dello studente
        student_answer, created = StudentAnswer.objects.update_or_create(
            quiz_attempt=attempt,
            question=question,
            defaults={
                'selected_answers': valid_data_for_storage, # Salva i dati validati
                'answered_at': timezone.now()
                # Rimosso 'is_correct' e 'score' da qui, verranno calcolati/impostati dopo
            }
        )

        # Rimosso: La valutazione avviene in calculate_final_score o manualmente
        # if question.question_type != QuestionType.OPEN_ANSWER_MANUAL:
        #     student_answer.evaluate() # Il metodo evaluate() salva la risposta

        serializer = StudentAnswerSerializer(student_answer)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


    # POST /api/education/attempts/{pk}/complete/
    @action(detail=True, methods=['post'], url_path='complete')
    def complete_attempt(self, request, pk=None):
        """ Completa un tentativo di quiz. """
        attempt = self.get_object()
        if attempt.status != QuizAttempt.AttemptStatus.IN_PROGRESS:
            return Response({'detail': 'Questo tentativo non è più in corso.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica se ci sono domande a risposta aperta non ancora valutate manualmente
        has_manual_questions = attempt.quiz.questions.filter(question_type=QuestionType.OPEN_ANSWER_MANUAL).exists()
        needs_manual_grading = False
        if has_manual_questions:
            # Controlla se *tutte* le risposte alle domande manuali sono state date
            manual_question_ids = attempt.quiz.questions.filter(question_type=QuestionType.OPEN_ANSWER_MANUAL).values_list('id', flat=True)
            answered_manual_ids = attempt.student_answers.filter(question_id__in=manual_question_ids).values_list('question_id', flat=True)
            if set(manual_question_ids) == set(answered_manual_ids):
                 # Tutte le domande manuali hanno una risposta, ma potrebbero non essere state corrette
                 needs_manual_grading = True
            else:
                 # Non tutte le domande manuali hanno una risposta, l'utente non può completare
                 return Response({'detail': 'Devi rispondere a tutte le domande prima di completare il tentativo.'}, status=status.HTTP_400_BAD_REQUEST)


        if needs_manual_grading:
            attempt.status = QuizAttempt.AttemptStatus.PENDING_GRADING
            attempt.completed_at = timezone.now() # Registra comunque il tempo di completamento
            attempt.save()
            logger.info(f"Tentativo Quiz {attempt.id} completato, in attesa di correzione manuale.")
        else:
            # Calcola punteggio finale e assegna punti se è il primo completamento corretto
            final_score = attempt.calculate_final_score() # Calcola e salva lo score
            attempt.assign_completion_points() # Assegna punti se necessario (e salva first_correct_completion)
            # Lo stato viene aggiornato dentro assign_completion_points o rimane COMPLETED
            attempt.completed_at = timezone.now()
            attempt.save() # Salva eventuali modifiche da assign_completion_points
            logger.info(f"Tentativo Quiz {attempt.id} completato automaticamente. Score: {final_score}, Status: {attempt.status}")


        serializer = QuizAttemptSerializer(attempt, context={'request': request})
        return Response(serializer.data)


# --- ViewSet per Docenti (Correzione Manuale) ---

class TeacherGradingViewSet(viewsets.GenericViewSet):
    """ Endpoint per Docenti per visualizzare e correggere risposte manuali. """
    # queryset = QuizAttempt.objects.filter(status=QuizAttempt.AttemptStatus.PENDING_GRADING)
    serializer_class = QuizAttemptSerializer # Usato per la lista
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser] # Solo Docenti

    def get_queryset(self):
        """ Filtra i tentativi in attesa di correzione per i quiz del docente. """
        user = self.request.user
        if not isinstance(user, User) or not user.is_teacher:
            return QuizAttempt.objects.none() # Sicurezza: non docenti non vedono nulla

        # Filtra i tentativi PENDING_GRADING relativi ai quiz creati da questo docente
        return QuizAttempt.objects.filter(
            quiz__teacher=user,
            status=QuizAttempt.AttemptStatus.PENDING_GRADING
        ).select_related('student', 'quiz').order_by('completed_at')


    # GET /api/education/teacher/grading/pending/
    @action(detail=False, methods=['get'], url_path='pending')
    def list_pending(self, request):
        """ Lista dei tentativi in attesa di correzione per il docente loggato. """
        # Workaround per permessi: controllo manuale perché i permessi standard sembrano fallire qui
        if not isinstance(request.user, User) or not request.user.is_teacher:
             raise DRFPermissionDenied("Accesso negato.")

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # POST /api/education/teacher/grading/{pk}/grade/
    @action(detail=True, methods=['post'], url_path='grade')
    def grade_answer(self, request, pk=None):
        """ Permette al docente di assegnare un punteggio a una risposta manuale. """
        # Workaround per permessi: controllo manuale
        if not isinstance(request.user, User) or not request.user.is_teacher:
             raise DRFPermissionDenied("Accesso negato.")

        attempt = get_object_or_404(QuizAttempt, pk=pk)

        # Verifica che il docente sia il proprietario del quiz
        if attempt.quiz.teacher != request.user:
             raise DRFPermissionDenied("Non puoi correggere tentativi per quiz di altri docenti.")

        if attempt.status != QuizAttempt.AttemptStatus.PENDING_GRADING:
            return Response({'detail': 'Questo tentativo non è in attesa di correzione.'}, status=status.HTTP_400_BAD_REQUEST)

        answer_id = request.data.get('answer_id')
        score = request.data.get('score')
        is_correct = request.data.get('is_correct') # Boolean

        if answer_id is None or score is None or is_correct is None:
            return Response({'detail': 'answer_id, score e is_correct sono richiesti.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            answer = StudentAnswer.objects.get(pk=answer_id, quiz_attempt=attempt, question__question_type=QuestionType.OPEN_ANSWER_MANUAL)
        except StudentAnswer.DoesNotExist:
            return Response({'detail': 'Risposta manuale non trovata per questo tentativo.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            score = int(score)
            if score < 0: raise ValueError("Score non può essere negativo")
            # Potremmo aggiungere un controllo sul punteggio massimo della domanda se definito nei metadata
        except (ValueError, TypeError):
            return Response({'score': 'Il punteggio deve essere un intero non negativo.'}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(is_correct, bool):
             return Response({'is_correct': 'is_correct deve essere un booleano (true/false).'}, status=status.HTTP_400_BAD_REQUEST)


        # Aggiorna la risposta
        answer.score = score
        answer.is_correct = is_correct
        answer.save()

        # Verifica se tutte le risposte manuali sono state corrette
        all_manual_answers_graded = not attempt.student_answers.filter(
            question__question_type=QuestionType.OPEN_ANSWER_MANUAL,
            score__isnull=True # Cerca risposte manuali non ancora corrette (score è NULL)
        ).exists()

        if all_manual_answers_graded:
            # Tutte corrette, finalizza il tentativo
            logger.info(f"Tutte le risposte manuali per il tentativo {attempt.id} sono state corrette.")
            final_score = attempt.calculate_final_score() # Calcola e salva lo score finale
            attempt.assign_completion_points() # Assegna punti se necessario (e aggiorna stato)
            attempt.save() # Salva eventuali modifiche da assign_completion_points
            logger.info(f"Tentativo Quiz {attempt.id} finalizzato dopo correzione manuale. Score: {final_score}, Status: {attempt.status}")
            # Restituisci lo stato aggiornato del tentativo
            serializer = QuizAttemptSerializer(attempt, context={'request': request})
            return Response(serializer.data)
        else:
            # Ci sono ancora risposte da correggere, restituisci solo la risposta aggiornata
            serializer = StudentAnswerSerializer(answer)
            return Response(serializer.data)


# --- Viste Generiche per Dashboard Studente (usano generics.ListAPIView) ---

class StudentAssignedQuizzesView(generics.ListAPIView):
    """
    Restituisce l'elenco dei quiz assegnati allo studente loggato,
    arricchiti con informazioni sull'ultimo tentativo.
    """
    serializer_class = StudentQuizDashboardSerializer
    permission_classes = [IsStudentAuthenticated]

    def get_queryset(self):
        student = self.request.user # Assicurato da IsStudentAuthenticated
        assigned_quiz_ids = QuizAssignment.objects.filter(student=student).values_list('quiz_id', flat=True)

        # Filtra i quiz assegnati e prefetch tutti i tentativi dello studente per questi quiz
        queryset = Quiz.objects.filter(id__in=assigned_quiz_ids).select_related('teacher').prefetch_related(
             Prefetch(
                 'attempts',
                 queryset=QuizAttempt.objects.filter(student=student).order_by('-started_at'), # Ordina per trovare facilmente l'ultimo nel serializer
                 to_attr='student_attempts_for_quiz' # Salva in un attributo temporaneo
             )
        ).order_by('-created_at') # Ordina per data di creazione (o altro criterio)

        return queryset

    def get_serializer_context(self):
        """ Aggiunge lo studente al contesto del serializer. """
        context = super().get_serializer_context()
        context['student'] = self.request.user
        return context

class StudentAssignedPathwaysView(generics.ListAPIView):
    """
    Restituisce l'elenco dei percorsi assegnati allo studente loggato,
    arricchiti con informazioni sull'ultimo progresso.
    """
    serializer_class = StudentPathwayDashboardSerializer
    permission_classes = [IsStudentAuthenticated]

    def get_queryset(self):
        student = self.request.user
        assigned_pathway_ids = PathwayAssignment.objects.filter(student=student).values_list('pathway_id', flat=True)

        # Filtra i percorsi assegnati e prefetch tutti i progressi dello studente per questi percorsi
        queryset = Pathway.objects.filter(id__in=assigned_pathway_ids).select_related('teacher').prefetch_related(
            Prefetch(
                'progresses', # Usa il related_name corretto
                queryset=PathwayProgress.objects.filter(student=student).order_by('-started_at'), # Ordina per trovare facilmente l'ultimo nel serializer
                to_attr='student_progresses_for_pathway' # Salva in un attributo temporaneo
            ),
            'pathwayquiz_set__quiz' # Prefetch anche i quiz nel percorso
        ).order_by('-created_at')

        return queryset

    def get_serializer_context(self):
        """ Aggiunge lo studente al contesto del serializer. """
        context = super().get_serializer_context()
        context['student'] = self.request.user
        return context

# --- Vista per Dettagli Tentativo Percorso Studente ---

class PathwayAttemptDetailView(generics.RetrieveAPIView):
    """
    Restituisce i dettagli di un percorso per lo studente che lo sta svolgendo,
    includendo il progresso e il prossimo quiz da affrontare.
    """
    queryset = Pathway.objects.all().prefetch_related('pathwayquiz_set__quiz') # Queryset base
    serializer_class = PathwayAttemptDetailSerializer
    permission_classes = [IsStudentAuthenticated] # Solo studenti autenticati

    def get_object(self):
        """ Recupera il percorso e verifica l'assegnazione allo studente. """
        pathway = super().get_object() # Recupera il percorso usando il pk dall'URL
        student = self.request.user

        # Verifica se il percorso è assegnato allo studente
        is_assigned = PathwayAssignment.objects.filter(pathway=pathway, student=student).exists()
        if not is_assigned:
            # Solleva PermissionDenied se non assegnato
            raise DRFPermissionDenied("Questo percorso non ti è stato assegnato.")

        return pathway

    def retrieve(self, request, *args, **kwargs):
        """
        Recupera i dati del percorso, calcola il prossimo quiz e aggiunge
        le informazioni al serializer.
        """
        pathway = self.get_object() # Ottiene il percorso e verifica l'assegnazione
        student = request.user

        # Recupera o crea il progresso dello studente per questo percorso
        progress, created = PathwayProgress.objects.get_or_create(
            student=student,
            pathway=pathway,
            defaults={'status': PathwayProgress.ProgressStatus.IN_PROGRESS}
        )

        next_quiz = None
        if progress.status == PathwayProgress.ProgressStatus.IN_PROGRESS:
            last_completed_order = progress.last_completed_quiz_order
            # Trova il quiz nel percorso con l'ordine successivo
            next_pathway_quiz = pathway.pathwayquiz_set.filter(
                order__gt=last_completed_order if last_completed_order is not None else -1
            ).order_by('order').first()

            if next_pathway_quiz:
                next_quiz = next_pathway_quiz.quiz

        # Serializza il percorso
        serializer = self.get_serializer(pathway)
        data = serializer.data

        # Aggiungi manualmente i dati del progresso e del prossimo quiz
        # (Il serializer li ha definiti come read_only, quindi li popoliamo qui)
        data['progress'] = PathwayProgressSerializer(progress).data if progress else None
        data['next_quiz'] = NextPathwayQuizSerializer(next_quiz).data if next_quiz else None # Corretto: Usa il serializer importato

        return Response(data)
