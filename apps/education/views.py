from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction, models
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import (
    QuizTemplate, QuestionTemplate, AnswerOptionTemplate,
    Quiz, Question, AnswerOption, Pathway, PathwayQuiz,
    QuizAttempt, StudentAnswer, PathwayProgress, QuestionType,
    QuizAssignment, PathwayAssignment # Importa i modelli Assignment
)
from .serializers import (
    QuizTemplateSerializer, QuestionTemplateSerializer, AnswerOptionTemplateSerializer,
    QuizSerializer, QuestionSerializer, AnswerOptionSerializer, PathwaySerializer,
    QuizAttemptSerializer, StudentAnswerSerializer, PathwayProgressSerializer,
    QuizAttemptDetailSerializer # Importa il nuovo serializer
)
from .permissions import (
    IsAdminOrReadOnly, IsQuizTemplateOwnerOrAdmin, IsQuizOwner, IsPathwayOwner,
    IsStudentOwnerForAttempt, IsTeacherOfStudentForAttempt
)
from apps.users.permissions import IsAdminUser, IsTeacherUser, IsStudent # Import IsStudent
from apps.users.models import UserRole, Student # Import modelli utente
from apps.rewards.models import Wallet # Import Wallet

# --- ViewSets per Admin (Templates) ---
# ... (QuizTemplateViewSet, QuestionTemplateViewSet, AnswerOptionTemplateViewSet come prima) ...
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
# ... (QuizViewSet, QuestionViewSet, AnswerOptionViewSet, PathwayViewSet come prima, con azioni assign) ...
class QuizViewSet(viewsets.ModelViewSet):
    """ API endpoint per i Quiz concreti (Docente). """
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated, IsQuizOwner] # IsTeacherUser implicito

    def get_queryset(self):
        user = self.request.user
        if user.is_admin: # Admin può vedere tutti i quiz? Decidiamo di sì.
            return Quiz.objects.all().select_related('teacher')
        elif user.is_teacher:
            return Quiz.objects.filter(teacher=user).select_related('teacher')
        return Quiz.objects.none()

    def perform_create(self, serializer):
        if not self.request.user.is_teacher:
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

    @action(detail=True, methods=['post'], url_path='assign-student', permission_classes=[permissions.IsAuthenticated, IsQuizOwner])
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
    permission_classes = [permissions.IsAuthenticated, IsQuizOwner]

    def get_queryset(self):
        quiz = get_object_or_404(Quiz, pk=self.kwargs['quiz_pk'])
        if quiz.teacher != self.request.user and not self.request.user.is_admin:
             raise PermissionDenied("Non hai accesso a questo quiz.")
        return Question.objects.filter(quiz=quiz)

    def perform_create(self, serializer):
        quiz = get_object_or_404(Quiz, pk=self.kwargs['quiz_pk'])
        if quiz.teacher != self.request.user:
             raise PermissionDenied("Non puoi aggiungere domande a questo quiz.")
        serializer.save(quiz=quiz)

class AnswerOptionViewSet(viewsets.ModelViewSet):
     serializer_class = AnswerOptionSerializer

     def get_queryset(self):
         question = get_object_or_404(Question, pk=self.kwargs['question_pk'])
         if question.quiz.teacher != self.request.user and not self.request.user.is_admin:
              raise PermissionDenied("Non hai accesso a questa domanda.")
         return AnswerOption.objects.filter(question=question)

     def perform_create(self, serializer):
         question = get_object_or_404(Question, pk=self.kwargs['question_pk'])
         if question.quiz.teacher != self.request.user:
              raise PermissionDenied("Non puoi aggiungere opzioni a questa domanda.")
         serializer.save(question=question)

class PathwayViewSet(viewsets.ModelViewSet):
    """ API endpoint per i Percorsi (Docente). """
    serializer_class = PathwaySerializer
    permission_classes = [permissions.IsAuthenticated, IsPathwayOwner] # IsTeacherUser implicito

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Pathway.objects.all().select_related('teacher').prefetch_related('pathwayquiz_set__quiz')
        elif user.is_teacher:
            return Pathway.objects.filter(teacher=user).select_related('teacher').prefetch_related('pathwayquiz_set__quiz')
        return Pathway.objects.none()

    def perform_create(self, serializer):
        if not self.request.user.is_teacher:
             raise serializers.ValidationError("Solo i Docenti possono creare percorsi.")
        serializer.save(teacher=self.request.user)

    @action(detail=True, methods=['post'], url_path='add-quiz', permission_classes=[permissions.IsAuthenticated, IsPathwayOwner])
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

    @action(detail=True, methods=['post'], url_path='assign-student', permission_classes=[permissions.IsAuthenticated, IsPathwayOwner])
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
     permission_classes = [permissions.IsAuthenticated, IsStudent] # Solo Studenti

     def list(self, request):
         student = request.student
         if not student:
             return Response({"assigned_quizzes": [], "assigned_pathways": []})

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
    permission_classes = [permissions.IsAuthenticated, IsStudent] # Solo Studenti
    serializer_class = QuizAttemptSerializer # Per output base

    # POST /api/education/quizzes/{quiz_pk}/start-attempt/
    @action(detail=False, methods=['post'], url_path='start-attempt')
    def start_attempt(self, request, quiz_pk=None):
         quiz = get_object_or_404(Quiz, pk=quiz_pk)
         student = request.student
         if not student:
             return Response({'detail': 'Autenticazione studente fallita.'}, status=status.HTTP_401_UNAUTHORIZED)

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
    permission_classes = [permissions.IsAuthenticated, IsStudent, IsStudentOwnerForAttempt] # Solo lo studente proprietario

    # GET /api/education/attempts/{pk}/details/
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        attempt = self.get_object() # get_object usa queryset e pk dall'URL
        serializer = QuizAttemptDetailSerializer(attempt, context={'request': request})
        return Response(serializer.data)

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

        # TODO: Validare selected_answers_data in base a question.question_type

        # Crea o aggiorna la risposta dello studente
        student_answer, created = StudentAnswer.objects.update_or_create(
            quiz_attempt=attempt,
            question=question,
            defaults={'selected_answers': selected_answers_data}
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
                # --- INIZIO LOGICA DA IMPLEMENTARE ---
                attempt.score = self.calculate_score(attempt)
                # Verifica se è il primo completamento corretto e assegna punti
                self.check_and_assign_points(attempt)
                # --- FINE LOGICA DA IMPLEMENTARE ---
                attempt.save()

            serializer = QuizAttemptSerializer(attempt) # Usa serializer base
            return Response(serializer.data)

    def calculate_score(self, attempt):
        """
        Placeholder: Calcola il punteggio finale per un tentativo
        (solo domande a correzione automatica).
        """
        total_score = 0
        max_score = 0 # O numero di domande
        correct_answers = 0
        total_questions = attempt.quiz.questions.count() # O solo quelle auto?

        for answer in attempt.student_answers.select_related('question').all():
            question = answer.question
            # Ignora manuali per ora
            if question.question_type == QuestionType.OPEN_ANSWER_MANUAL:
                continue

            # Logica di correzione automatica (semplificata)
            is_correct = False
            if question.question_type in [QuestionType.MULTIPLE_CHOICE_SINGLE, QuestionType.TRUE_FALSE]:
                correct_option = question.answer_options.filter(is_correct=True).first()
                selected_id = answer.selected_answers.get('selected_options', [None])[0]
                is_correct = correct_option and selected_id == correct_option.id
            elif question.question_type == QuestionType.MULTIPLE_CHOICE_MULTIPLE:
                correct_ids = set(question.answer_options.filter(is_correct=True).values_list('id', flat=True))
                selected_ids = set(answer.selected_answers.get('selected_options', []))
                is_correct = correct_ids == selected_ids
            # Aggiungere logica per FILL_BLANK basata su question.metadata

            answer.is_correct = is_correct
            # Assegna punteggio (es. 1 punto per risposta corretta)
            answer.score = 1.0 if is_correct else 0.0
            answer.save()

            if is_correct:
                correct_answers += 1

        # Calcola punteggio finale (es. percentuale)
        if total_questions > 0:
             final_score = (correct_answers / total_questions) * 100
             return round(final_score, 2)
        return 0.0

    def check_and_assign_points(self, attempt):
        """
        Placeholder: Verifica se è il primo completamento corretto e assegna punti.
        """
        quiz = attempt.quiz
        student = attempt.student
        threshold = quiz.metadata.get('completion_threshold', 0.8) * 100 # Converti in percentuale
        points_to_award = quiz.metadata.get('points_on_completion', 0)

        if attempt.score is None or points_to_award <= 0:
            return

        is_successful = attempt.score >= threshold

        if is_successful:
            # Verifica se è il *primo* tentativo completato con successo
            previous_success = QuizAttempt.objects.filter(
                student=student,
                quiz=quiz,
                status=QuizAttempt.AttemptStatus.COMPLETED,
                score__gte=threshold
            ).exclude(pk=attempt.pk).exists()

            if not previous_success:
                try:
                    wallet = student.wallet
                    wallet.add_points(points_to_award, f"Completamento Quiz: {quiz.title}")
                    print(f"Assegnati {points_to_award} punti a {student.full_name} per {quiz.title}") # Log
                except Wallet.DoesNotExist:
                    print(f"Errore: Wallet non trovato per studente {student.id}") # Log errore
                except Exception as e:
                     print(f"Errore durante assegnazione punti: {e}") # Log errore


# --- ViewSets per Docenti (Correzione/Risultati) ---
# ... (TeacherGradingViewSet come prima) ...
class TeacherGradingViewSet(viewsets.GenericViewSet):
    """ Endpoint per Docenti per visualizzare e correggere risposte manuali. """
    serializer_class = StudentAnswerSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser, IsTeacherOfStudentForAttempt]

    def get_queryset(self):
        """ Filtra le risposte manuali pendenti dei propri studenti. """
        user = self.request.user
        return StudentAnswer.objects.filter(
            quiz_attempt__student__teacher=user,
            question__question_type=QuestionType.OPEN_ANSWER_MANUAL,
            is_correct__isnull=True # Solo quelle non ancora corrette
        ).select_related('quiz_attempt__student', 'question')

    @action(detail=False, methods=['get'], url_path='pending')
    def list_pending(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='grade')
    def grade_answer(self, request, pk=None):
        student_answer = get_object_or_404(self.get_queryset(), pk=pk)

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
        pending_answers = attempt.student_answers.filter(is_correct__isnull=True).count()
        if pending_answers == 0 and attempt.status == QuizAttempt.AttemptStatus.PENDING_GRADING:
            # Tutte le risposte (manuali) sono state corrette, finalizza l'attempt
            with transaction.atomic():
                attempt = QuizAttempt.objects.select_for_update().get(pk=attempt.pk) # Lock
                attempt.status = QuizAttempt.AttemptStatus.COMPLETED
                attempt.completed_at = timezone.now()
                # Ricalcola punteggio includendo le risposte manuali (se necessario)
                # La logica in calculate_score potrebbe dover essere aggiornata
                attempt.score = self.calculate_score(attempt) # Ricalcola
                self.check_and_assign_points(attempt)
                attempt.save()
            print(f"Attempt {attempt.id} completato e corretto dopo grading manuale.")

        serializer = self.get_serializer(student_answer)
        return Response(serializer.data)

# Nota: La logica di calculate_score e check_and_assign_points è placeholder
# e potrebbe necessitare di raffinamenti (es. gestione punti per domanda,
# calcolo punteggio con risposte manuali).
