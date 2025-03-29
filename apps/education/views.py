from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction, models, IntegrityError # Import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import PermissionDenied # Import PermissionDenied
from django.db.models import F # Import F

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
    QuizAttemptDetailSerializer # Importa il nuovo serializer
)
from .permissions import (
    IsAdminOrReadOnly, IsQuizTemplateOwnerOrAdmin, IsQuizOwnerOrAdmin, IsPathwayOwnerOrAdmin, # Updated IsPathwayOwner -> IsPathwayOwnerOrAdmin
    IsStudentOwnerForAttempt, IsTeacherOfStudentForAttempt, IsAnswerOptionOwner # Aggiunto IsAnswerOptionOwner
)
from apps.users.permissions import IsAdminUser, IsTeacherUser, IsStudent, IsStudentAuthenticated # Import IsStudentAuthenticated
from apps.users.models import UserRole, Student, User # Import modelli utente e User
from apps.rewards.models import Wallet, PointTransaction # Import Wallet e PointTransaction

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
            if not isinstance(selected_answers_data, dict) or 'answer_text' not in selected_answers_data:
                validation_error = "Per questo tipo di domanda, 'selected_answers' deve essere un dizionario con chiave 'answer_text'."
            else:
                answer_text = selected_answers_data['answer_text']
                if not isinstance(answer_text, str):
                     validation_error = "'answer_text' deve essere una stringa."
                else:
                    valid_data_for_storage = {'answer_text': answer_text}

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

    def calculate_score(self, attempt): # Rimosso validated_data
        """
        Calcola il punteggio per un tentativo basandosi sulle risposte SALVATE nel DB.
        """
        score = 0
        # Recupera le risposte dello studente per questo tentativo
        student_answers = attempt.student_answers.select_related('question').all()
        quiz = attempt.quiz

        # Pre-fetch questions and their correct options for efficiency
        questions = quiz.questions.prefetch_related('answer_options').all()
        correct_options_map = {}
        fill_blank_answers_map = {}
        total_autograded_questions = 0

        for q in questions:
            # Considera solo le domande a correzione automatica per il calcolo del punteggio %
            if q.question_type != QuestionType.OPEN_ANSWER_MANUAL:
                total_autograded_questions += 1
                if q.question_type in [QuestionType.MULTIPLE_CHOICE_SINGLE, QuestionType.TRUE_FALSE]:
                     correct_option = q.answer_options.filter(is_correct=True).first()
                     if correct_option:
                         correct_options_map[q.id] = correct_option.id
                elif q.question_type == QuestionType.MULTIPLE_CHOICE_MULTIPLE:
                     correct_options_map[q.id] = set(q.answer_options.filter(is_correct=True).values_list('id', flat=True))
                elif q.question_type == QuestionType.FILL_BLANK:
                    # Assumendo che la risposta corretta sia in metadata['correct_answer']
                    # Consideriamo anche la possibilità di risposte multiple separate da | e case-insensitivity
                    correct_answers = [ans.strip().lower() for ans in q.metadata.get('correct_answers', [])] # Usa 'correct_answers' (lista)
                    fill_blank_answers_map[q.id] = correct_answers


        correct_answers_count = 0

        if total_autograded_questions == 0:
             # Se non ci sono domande a correzione automatica, il punteggio automatico è 0.
             # Lo stato del tentativo potrebbe dover riflettere la necessità di revisione manuale.
             attempt.score = 0
             print(f"Nessuna domanda a correzione automatica per il quiz {quiz.id}. Punteggio automatico impostato a 0.")
             return 0

        # Itera sulle risposte dello studente recuperate dal DB
        for student_answer in student_answers:
            question = student_answer.question
            # Salta le domande a risposta manuale
            if question.question_type == QuestionType.OPEN_ANSWER_MANUAL:
                continue

            question_id = question.id
            question_type = question.question_type
            selected_data = student_answer.selected_answers # Questo è il JSON salvato

            is_correct = False
            try:
                if question_type in [QuestionType.MULTIPLE_CHOICE_SINGLE, QuestionType.TRUE_FALSE]:
                    selected_option_id = selected_data.get('selected_option_id') if isinstance(selected_data, dict) else None
                    if question_id in correct_options_map and selected_option_id == correct_options_map[question_id]:
                        is_correct = True
                elif question_type == QuestionType.MULTIPLE_CHOICE_MULTIPLE:
                    selected_option_ids = set(selected_data.get('selected_option_ids', [])) if isinstance(selected_data, dict) else set()
                    if question_id in correct_options_map and selected_option_ids == correct_options_map[question_id]:
                        is_correct = True
                elif question_type == QuestionType.FILL_BLANK:
                    user_answer = selected_data.get('answer_text', '').strip().lower() if isinstance(selected_data, dict) else ''
                    # Controlla se la risposta utente è una delle risposte corrette possibili
                    if question_id in fill_blank_answers_map and user_answer in fill_blank_answers_map[question_id]:
                        is_correct = True
            except Exception as e:
                print(f"Errore durante la valutazione della risposta per domanda {question_id} nel tentativo {attempt.id}: {e}")

            if is_correct:
                correct_answers_count += 1
            # Aggiorna il campo is_correct sulla risposta dello studente (se non è manuale)
            # Questo potrebbe essere fatto qui o in un processo separato
            if student_answer.is_correct != is_correct: # Aggiorna solo se cambia
                student_answer.is_correct = is_correct
                student_answer.save(update_fields=['is_correct'])

        # Calculate score as a percentage of auto-graded questions
        score = (correct_answers_count / total_autograded_questions) * 100
        score = round(score, 2) # Round score to two decimal places

        attempt.score = score
        # Il salvataggio dell'istanza attempt con il punteggio è gestito in perform_create/perform_update
        print(f"Calcolato punteggio automatico per tentativo {attempt.id}: {score}")
        return score

    def check_and_assign_points(self, attempt):
        """
        Verifica il punteggio del tentativo e assegna punti allo studente se applicabile,
        basandosi sulle regole definite nel quiz (metadata).
        Controlla anche se è il primo completamento con successo.
        """
        quiz = attempt.quiz
        student = attempt.student # Usa 'student' come nel codice originale
        # Usa i metadati del quiz per soglia e punti, con fallback a default ragionevoli
        threshold = quiz.metadata.get('completion_threshold_percent', 80.0) # Default 80%
        points_to_award = quiz.metadata.get('points_on_completion', 0) # Default 0 punti

        if attempt.score is None:
             print(f"Tentativo {attempt.id}: Punteggio non ancora calcolato. Nessuna azione sui punti.")
             return
        if points_to_award <= 0:
            print(f"Tentativo {attempt.id}: Punti non previsti per questo quiz ({points_to_award}). Nessuna azione.")
            return

        is_successful = attempt.score >= threshold

        if is_successful:
            print(f"Tentativo {attempt.id} superato (Punteggio: {attempt.score} >= Soglia: {threshold}). Controllo assegnazione punti...")
            # Verifica se è il *primo* tentativo completato con successo per questo quiz/studente
            # Escludi il tentativo corrente dalla verifica
            previous_successful_attempts = QuizAttempt.objects.filter(
                student=student,
                quiz=quiz,
                status=QuizAttempt.AttemptStatus.COMPLETED, # Assicurati che lo stato sia corretto
                score__gte=threshold
            ).exclude(pk=attempt.pk).exists()

            if not previous_successful_attempts:
                print(f"Questo è il primo completamento con successo per {student.full_name} del quiz '{quiz.title}'. Assegnazione punti...")
                try:
                    # Usa il wallet dello studente come nel codice originale
                    wallet, created = Wallet.objects.get_or_create(student=student) # Usa get_or_create
                    # Usa F() per aggiornamenti atomici sul campo 'balance' (o come si chiama)
                    # Assumendo che il campo si chiami 'current_points'
                    wallet.current_points = F('current_points') + points_to_award
                    wallet.save(update_fields=['current_points'])
                    # Ricarica per ottenere il valore aggiornato se necessario mostrarlo subito
                    wallet.refresh_from_db()
                    print(f"Assegnati {points_to_award} punti a {student.full_name}. Nuovo saldo: {wallet.current_points}")

                    # Registra la transazione
                    PointTransaction.objects.create(wallet=wallet, points_change=points_to_award, reason=f"Completamento Quiz: {quiz.title}")

                except Wallet.DoesNotExist: # Questo non dovrebbe accadere con get_or_create
                    print(f"ERRORE: Wallet non trovato per lo studente {student.id}. Impossibile assegnare punti.")
                except Exception as e:
                     print(f"ERRORE durante l'assegnazione dei punti per il tentativo {attempt.id}: {e}")
            else:
                print(f"Lo studente {student.full_name} aveva già completato con successo il quiz '{quiz.title}'. Nessun punto aggiuntivo assegnato.")
        else:
            print(f"Tentativo {attempt.id} non superato (Punteggio: {attempt.score} < Soglia: {threshold}). Nessun punto assegnato.")

        # Future enhancement: Check for badge eligibility based on score or points
        # self.check_and_award_badges(student, attempt)


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

        # Controlla se è già stata gradata
        if student_answer.is_correct is not None:
            return Response({'detail': 'Questa risposta è già stata corretta.'}, status=status.HTTP_400_BAD_REQUEST)

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
