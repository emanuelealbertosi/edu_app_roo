from rest_framework import viewsets, permissions, status, serializers, generics # Import generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction, models, IntegrityError # Import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import PermissionDenied # Import PermissionDenied
from django.db.models import F, OuterRef, Subquery, Count # Import per Subquery e Count

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
    StudentQuizDashboardSerializer, StudentPathwayDashboardSerializer # Importa i nuovi serializer
)
from .permissions import (
    IsAdminOrReadOnly, IsQuizTemplateOwnerOrAdmin, IsQuizOwnerOrAdmin, IsPathwayOwnerOrAdmin, # Updated IsPathwayOwner -> IsPathwayOwnerOrAdmin
    IsStudentOwnerForAttempt, IsTeacherOfStudentForAttempt, IsAnswerOptionOwner # Aggiunto IsAnswerOptionOwner
)
from apps.users.permissions import IsAdminUser, IsTeacherUser, IsStudent, IsStudentAuthenticated # Import IsStudentAuthenticated
from apps.users.models import UserRole, Student, User # Import modelli utente e User
from apps.rewards.models import Wallet, PointTransaction # Import Wallet e PointTransaction
from .models import QuizAssignment, PathwayAssignment, QuizAttempt, PathwayProgress # Assicurati che siano importati

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
    permission_classes = [permissions.IsAuthenticated, IsQuizOwnerOrAdmin] # Removed permissions. prefix

    def get_queryset(self):
        user = self.request.user

        # Per azioni di dettaglio (retrieve, update, etc.), permettiamo a DRF di trovare l'oggetto.
        # Il permesso IsQuizOwner (o altri permessi a livello di oggetto) gestirà l'accesso (403 vs 404).
        # Questo assicura che un utente non autorizzato riceva 403 invece di 404 se l'oggetto esiste.
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'assign_student']: # Aggiunte azioni custom che operano su un oggetto
            return Quiz.objects.all().select_related('teacher')

        # Per l'azione 'list' (e altre azioni a livello di lista), applichiamo i filtri standard.
        if isinstance(user, User) and user.is_admin:
            return Quiz.objects.all().select_related('teacher')
        elif isinstance(user, User) and user.is_teacher:
            return Quiz.objects.filter(teacher=user).select_related('teacher')
        # Per studenti o altri utenti non privilegiati, la lista dei quiz è vuota.
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

class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    # Permetti a Docenti o Admin
    permission_classes = [(IsTeacherUser | IsAdminUser)]

    def get_queryset(self):
        quiz = get_object_or_404(Quiz, pk=self.kwargs['quiz_pk'])
        # Verifica ownership o ruolo admin
        if not isinstance(self.request.user, User) or (not self.request.user.is_admin and quiz.teacher != self.request.user):
             raise PermissionDenied("Non hai accesso a questo quiz.")
        return Question.objects.filter(quiz=quiz)

    def perform_create(self, serializer):
        quiz = get_object_or_404(Quiz, pk=self.kwargs['quiz_pk'])
        if not isinstance(self.request.user, User) or quiz.teacher != self.request.user:
             raise PermissionDenied("Non puoi aggiungere domande a questo quiz.")
        serializer.save(quiz=quiz)

class AnswerOptionViewSet(viewsets.ModelViewSet):
     serializer_class = AnswerOptionSerializer
     # Usa il nuovo permesso IsAnswerOptionOwner
     permission_classes = [IsAnswerOptionOwner]

     def get_queryset(self):
         question = get_object_or_404(Question, pk=self.kwargs['question_pk'])
         # Verifica ownership o ruolo admin
         if not isinstance(self.request.user, User) or (not self.request.user.is_admin and question.quiz.teacher != self.request.user):
              raise PermissionDenied("Non hai accesso a questa domanda.")
         return AnswerOption.objects.filter(question=question)

     def perform_create(self, serializer):
         question = get_object_or_404(Question, pk=self.kwargs['question_pk'])
         if not isinstance(self.request.user, User) or question.quiz.teacher != self.request.user:
              raise PermissionDenied("Non puoi aggiungere opzioni a questa domanda.")
         serializer.save(question=question)

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

        try:
            pathway_quiz, created = PathwayQuiz.objects.update_or_create(
                pathway=pathway,
                quiz=quiz,
                defaults={'order': order}
            )
            return Response(PathwayQuizSerializer(pathway_quiz).data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
        except IntegrityError:
             return Response({'detail': 'Errore nell\'aggiungere il quiz al percorso.'}, status=status.HTTP_400_BAD_REQUEST)

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

         is_assigned = QuizAssignment.objects.filter(student=student, quiz=quiz).exists()
         if not is_assigned:
             return Response({'detail': 'Questo quiz non è assegnato allo studente.'}, status=status.HTTP_403_FORBIDDEN)

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
        all_questions = attempt.quiz.questions.order_by('order')
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
        validation_error = None
        valid_data_for_storage = {} # Dati validati da salvare

        q_type = question.question_type
        if q_type in [QuestionType.MULTIPLE_CHOICE_SINGLE, QuestionType.TRUE_FALSE]:
            if not isinstance(selected_answers_data, dict) or 'selected_option_id' not in selected_answers_data:
                validation_error = "Per questo tipo di domanda, 'selected_answers' deve essere un dizionario con chiave 'selected_option_id'."
            else:
                selected_id = selected_answers_data['selected_option_id']
                # Permetti None per deselezionare? Se sì, aggiungere 'or selected_id is None'
                if not isinstance(selected_id, int):
                    validation_error = "'selected_option_id' deve essere un intero."
                else:
                    # Verifica che l'opzione esista per questa domanda
                    if not question.answer_options.filter(pk=selected_id).exists():
                        validation_error = f"L'opzione con ID {selected_id} non è valida per questa domanda."
                    else:
                        # Dati validi per il salvataggio
                        valid_data_for_storage = {'selected_option_id': selected_id}

        elif q_type == QuestionType.MULTIPLE_CHOICE_MULTIPLE:
            if not isinstance(selected_answers_data, dict) or 'selected_option_ids' not in selected_answers_data:
                validation_error = "Per questo tipo di domanda, 'selected_answers' deve essere un dizionario con chiave 'selected_option_ids'."
            else:
                selected_ids = selected_answers_data['selected_option_ids']
                if not isinstance(selected_ids, list) or not all(isinstance(i, int) for i in selected_ids):
                    validation_error = "'selected_option_ids' deve essere una lista di interi."
                else:
                    # Verifica che tutte le opzioni esistano per questa domanda
                    valid_option_ids = set(question.answer_options.values_list('id', flat=True))
                    submitted_ids_set = set(selected_ids)
                    if not submitted_ids_set.issubset(valid_option_ids):
                        invalid_ids = submitted_ids_set - valid_option_ids
                        validation_error = f"Le seguenti opzioni non sono valide per questa domanda: {list(invalid_ids)}."
                    else:
                        # Dati validi per il salvataggio (salva la lista)
                        # Ordina gli ID per consistenza, se importante
                        valid_data_for_storage = {'selected_option_ids': sorted(list(submitted_ids_set))}

        elif q_type == QuestionType.FILL_BLANK:
            # CORRETTO: Aspettarsi 'answers' come lista
            if not isinstance(selected_answers_data, dict) or 'answers' not in selected_answers_data:
                validation_error = "Per questo tipo di domanda, 'selected_answers' deve essere un dizionario con chiave 'answers'."
            else:
                answers_list = selected_answers_data['answers']
                # CORRETTO: Validare che sia una lista di stringhe
                if not isinstance(answers_list, list) or not all(isinstance(a, str) for a in answers_list):
                     validation_error = "'answers' deve essere una lista di stringhe."
                else:
                    # CORRETTO: Controllare il numero di risposte
                    expected_answers_count = len(question.metadata.get('correct_answers', []))
                    if len(answers_list) != expected_answers_count:
                        validation_error = f"Numero errato di risposte fornite. Attese {expected_answers_count}, ricevute {len(answers_list)}."
                    else:
                        # Dati validi per il salvataggio
                        valid_data_for_storage = {'answers': answers_list} # Salva la lista

        elif q_type == QuestionType.OPEN_ANSWER_MANUAL:
            if not isinstance(selected_answers_data, dict) or 'answer_text' not in selected_answers_data:
                validation_error = "Per questo tipo di domanda, 'selected_answers' deve essere un dizionario con chiave 'answer_text'."
            else:
                answer_text = selected_answers_data['answer_text']
                # Permetti stringa vuota? Se sì, va bene. Altrimenti aggiungi controllo.
                if not isinstance(answer_text, str):
                     validation_error = "'answer_text' deve essere una stringa."
                else:
                    # Dati validi per il salvataggio
                    valid_data_for_storage = {'answer_text': answer_text}
        else:
            # Tipo di domanda non gestito o sconosciuto
             validation_error = f"La validazione per il tipo di domanda '{q_type}' non è implementata."

        if validation_error:
            return Response({'detail': validation_error}, status=status.HTTP_400_BAD_REQUEST)

        # Usa valid_data_for_storage per creare/aggiornare
        student_answer, created = StudentAnswer.objects.update_or_create(
            quiz_attempt=attempt,
            question=question,
            defaults={'selected_answers': valid_data_for_storage} # Usa i dati validati
        )

        # Per ora, restituisce solo la risposta salvata. Non facciamo correzione automatica qui.
        serializer = StudentAnswerSerializer(student_answer)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    # POST /api/education/attempts/{pk}/complete/
    @action(detail=True, methods=['post'], url_path='complete')
    def complete_attempt(self, request, pk=None):
        attempt = self.get_object()
        if attempt.status != QuizAttempt.AttemptStatus.IN_PROGRESS:
            return Response({'detail': 'Questo tentativo non è più in corso.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica se ci sono domande a risposta manuale
        has_manual_questions = attempt.quiz.questions.filter(question_type=QuestionType.OPEN_ANSWER_MANUAL).exists()

        if has_manual_questions:
            # Se ci sono risposte manuali, metti in attesa di grading
            attempt.status = QuizAttempt.AttemptStatus.PENDING_GRADING
            attempt.save()
            serializer = QuizAttemptSerializer(attempt) # Usa serializer base
            return Response(serializer.data)
        else:
            # Se non ci sono risposte manuali, calcola punteggio e finalizza
            with transaction.atomic():
                attempt = QuizAttempt.objects.select_for_update().get(pk=pk) # Lock
                attempt.status = QuizAttempt.AttemptStatus.COMPLETED
                attempt.completed_at = timezone.now()
                # Chiama i metodi spostati sul modello QuizAttempt
                attempt.score = attempt.calculate_final_score()
                # Verifica se è il primo completamento corretto e assegna punti
                # Il metodo del modello ora gestisce anche il salvataggio di points_earned se necessario
                points_assigned = attempt.assign_completion_points()
                # Salva lo stato, il punteggio e completed_at. La creazione della PointTransaction
                # e l'aggiornamento di first_correct_completion avvengono dentro assign_completion_points.
                attempt.save(update_fields=['status', 'completed_at', 'score']) # Removed 'points_earned'

            serializer = QuizAttemptSerializer(attempt) # Usa serializer base
            return Response(serializer.data)

# --- ViewSets per Docenti (Correzione/Risultati) ---
class TeacherGradingViewSet(viewsets.GenericViewSet):
    """ Endpoint per Docenti per visualizzare e correggere risposte manuali. """
    serializer_class = StudentAnswerSerializer
    # Ripristiniamo IsTeacherUser a livello di ViewSet (anche se sembra inefficace per list_pending)
    permission_classes = [IsTeacherUser]

    def get_queryset(self):
        """ Filtra le risposte manuali pendenti dei propri studenti. """
        user = self.request.user
        # Assicurati che user sia un'istanza di User prima di filtrare
        if not isinstance(user, User):
            return StudentAnswer.objects.none()
        return StudentAnswer.objects.filter(
            quiz_attempt__student__teacher=user,
            question__question_type=QuestionType.OPEN_ANSWER_MANUAL,
            is_correct__isnull=True # Solo quelle non ancora corrette
        ).select_related('quiz_attempt__student', 'question')

    # Rimuoviamo il permesso esplicito qui, affidandoci a quello del ViewSet
    @action(detail=False, methods=['get'], url_path='pending')
    def list_pending(self, request):
        # WORKAROUND STABILE: Controllo manuale che restituisce 403 direttamente.
        if not IsTeacherUser().has_permission(request, self):
            print("[list_pending WORKAROUND] Controllo manuale fallito! Restituisco 403.")
            return Response({"detail": "Accesso consentito solo ai docenti."}, status=status.HTTP_403_FORBIDDEN)

        # Rimosso controllo manuale duplicato
        # if not IsTeacherUser().has_permission(request, self):
        #     print("[list_pending DEBUG] Controllo esplicito fallito!")
        #     raise PermissionDenied("Accesso negato esplicitamente.")

        # print(f"[list_pending] User: {request.user}, Student: {getattr(request, 'student', 'N/A')}") # DEBUG
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='grade')
    def grade_answer(self, request, pk=None):
        # WORKAROUND: Controllo manuale esplicito perché il permesso a livello di ViewSet
        # non blocca correttamente gli studenti in questo caso specifico.
        if not IsTeacherUser().has_permission(request, self):
            print("[grade_answer WORKAROUND] Controllo manuale fallito! Restituisco 403.")
            return Response({"detail": "Accesso consentito solo ai docenti."}, status=status.HTTP_403_FORBIDDEN)

        # Recupera la risposta verificando che appartenga al docente, ma senza filtrare per is_correct=None
        student_answer = get_object_or_404(
            StudentAnswer.objects.filter(
                quiz_attempt__student__teacher=request.user,
                question__question_type=QuestionType.OPEN_ANSWER_MANUAL
            ),
            pk=pk
        )

        # INVERTITO: Controlla PRIMA se è già stata gradata
        if student_answer.is_correct is not None:
            return Response({'detail': 'Questa risposta è già stata corretta.'}, status=status.HTTP_400_BAD_REQUEST)

        # POI controlla se il tentativo è in attesa di grading
        if student_answer.quiz_attempt.status != QuizAttempt.AttemptStatus.PENDING_GRADING:
            return Response({'detail': 'Il tentativo associato non è in attesa di correzione manuale.'}, status=status.HTTP_400_BAD_REQUEST)

        is_correct_input = request.data.get('is_correct')
        score_input = request.data.get('score')

        if is_correct_input is None:
             return Response({'is_correct': 'Questo campo è richiesto (true/false).'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            is_correct = str(is_correct_input).lower() in ['true', '1', 'yes']
            score = float(score_input) if score_input is not None else None
        except (ValueError, TypeError):
             return Response({'score': 'Il punteggio deve essere un numero valido.'}, status=status.HTTP_400_BAD_REQUEST)

        student_answer.is_correct = is_correct
        student_answer.score = score
        student_answer.save()

        attempt = student_answer.quiz_attempt
        # Modificato: Filtra solo le risposte a domande MANUALI che sono ancora pendenti
        pending_answers = attempt.student_answers.filter(
            question__question_type=QuestionType.OPEN_ANSWER_MANUAL,
            is_correct__isnull=True
        ).count()
        if pending_answers == 0 and attempt.status == QuizAttempt.AttemptStatus.PENDING_GRADING:
            # Tutte le risposte (manuali) sono state corrette, finalizza l'attempt
            with transaction.atomic():
                attempt = QuizAttempt.objects.select_for_update().get(pk=attempt.pk) # Lock
                attempt.status = QuizAttempt.AttemptStatus.COMPLETED
                attempt.completed_at = timezone.now()
                # Ricalcola punteggio finale usando il metodo del modello
                attempt.score = attempt.calculate_final_score()
                # Verifica se è il primo completamento corretto e assegna punti (gestito nel modello)
                attempt.assign_completion_points()
                # Salva i campi aggiornati
                attempt.save(update_fields=['status', 'completed_at', 'score'])
            print(f"Attempt {attempt.id} completato e corretto dopo grading manuale.")

        serializer = self.get_serializer(student_answer)
        return Response(serializer.data)

# Nota: La logica di calculate_score e check_and_assign_points è placeholder
# e potrebbe necessitare di raffinamenti (es. gestione punti per domanda,
# gestione più robusta dei metadati, etc.)
# --- View Specifiche per Dashboard Studente ---

class StudentAssignedQuizzesView(generics.ListAPIView):
    """
    Restituisce la lista dei quiz assegnati allo studente autenticato,
    arricchiti con informazioni sull'ultimo tentativo.
    """
    serializer_class = StudentQuizDashboardSerializer
    permission_classes = [IsStudentAuthenticated] # Solo studenti autenticati

    def get_queryset(self):
        student = self.request.user # request.user è lo studente grazie a StudentJWTAuthentication

        # Ottieni gli ID dei quiz assegnati allo studente
        assigned_quiz_ids = QuizAssignment.objects.filter(student=student).values_list('quiz_id', flat=True)

        # Subquery per ottenere l'ID dell'ultimo tentativo per ogni quiz per questo studente
        latest_attempt_subquery = QuizAttempt.objects.filter(
            quiz=OuterRef('pk'),
            student=student
        ).order_by('-started_at').values('pk')[:1] # Prende solo il più recente

        # Query principale: filtra per i quiz assegnati e annota con l'ID dell'ultimo tentativo e il conteggio
        queryset = Quiz.objects.filter(
            id__in=assigned_quiz_ids
        ).annotate(
            # Annotazione per l'ID dell'ultimo tentativo (usando Subquery)
            latest_attempt_id=Subquery(latest_attempt_subquery),
            # Annotazione per il conteggio dei tentativi
            attempts_count=Count('attempts', filter=models.Q(attempts__student=student))
        ).select_related('teacher') # Ottimizzazione

        # Recupera gli oggetti QuizAttempt completi per gli ID annotati
        attempt_ids = [qz.latest_attempt_id for qz in queryset if qz.latest_attempt_id]
        attempts_dict = {att.pk: att for att in QuizAttempt.objects.filter(pk__in=attempt_ids)}

        # Assegna l'oggetto tentativo completo al campo 'latest_attempt' (che il serializer si aspetta)
        for qz in queryset:
            qz.latest_attempt = attempts_dict.get(qz.latest_attempt_id) # Usa .get() per sicurezza

        return queryset


class StudentAssignedPathwaysView(generics.ListAPIView):
    """
    Restituisce la lista dei percorsi assegnati allo studente autenticato,
    arricchiti con informazioni sul progresso.
    """
    serializer_class = StudentPathwayDashboardSerializer
    permission_classes = [IsStudentAuthenticated]

    def get_queryset(self):
        student = self.request.user

        # Ottieni gli ID dei percorsi assegnati
        assigned_pathway_ids = PathwayAssignment.objects.filter(student=student).values_list('pathway_id', flat=True)

        # Subquery per ottenere l'ID del progresso per ogni percorso per questo studente
        progress_subquery = PathwayProgress.objects.filter(
            pathway=OuterRef('pk'),
            student=student
        ).values('pk')[:1] # Assume al massimo un progresso per studente/percorso

        # Query principale: filtra per i percorsi assegnati e annota con l'ID del progresso
        queryset = Pathway.objects.filter(
            id__in=assigned_pathway_ids
        ).annotate(
            progress_id=Subquery(progress_subquery) # Annotiamo l'ID
        ).select_related('teacher').prefetch_related('pathwayquiz_set__quiz') # Ottimizzazione

        # Recupera gli oggetti PathwayProgress completi per gli ID annotati
        progress_ids = [pw.progress_id for pw in queryset if pw.progress_id]
        progress_dict = {prog.pk: prog for prog in PathwayProgress.objects.filter(pk__in=progress_ids)}

        # Assegna l'oggetto progresso completo al campo 'progress' (che il serializer si aspetta)
        for pw in queryset:
            pw.progress = progress_dict.get(pw.progress_id) # Usa .get() per sicurezza

        return queryset
