import logging
import uuid # Aggiunto import per gestione UUID
from rest_framework import viewsets, permissions, serializers, generics, status, mixins
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from django.db.models import Count, Sum, Q, OuterRef, Subquery, Avg
# Importa modelli locali
from .models import User, Student, UserRole, StudentGroup, StudentRegistrationToken
# Importa tutti i serializer necessari
from .serializers import (
    UserSerializer,
    StudentSerializer,
    UserCreateSerializer,
    StudentProgressSummarySerializer,
    TeacherStudentCreateSerializer,
    StudentGroupSerializer,
    # Serializer per registrazione
    StudentRegistrationTokenSerializer,
    StudentRegistrationTokenCreateSerializer,
    StudentSelfRegisterSerializer
)
# Importa modelli da altre app per le annotazioni
from apps.education.models import QuizAttempt, PathwayProgress, QuizAssignment, PathwayAssignment, QuizTemplate, PathwayTemplate, StudentAnswer, QuestionType
from apps.education.serializers import StudentQuizAssignmentSerializer, StudentPathwayAssignmentSerializer
from apps.rewards.models import Wallet
# Import per autenticazione e JWT
from django.contrib.auth import login, logout, authenticate
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

# Get an instance of a logger
logger = logging.getLogger(__name__)
from .permissions import IsAdminUser, IsTeacherUser, IsStudentOwnerOrAdmin, IsStudent

# --- ViewSets per Admin/Docenti ---

class UserViewSet(viewsets.ModelViewSet):
    """ API endpoint per Admin per gestire Utenti (Admin/Docenti). """
    queryset = User.objects.all().order_by('-date_joined')
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'me':
             return UserSerializer
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], url_path='me', permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """ Restituisce i dati dell'utente autenticato. """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class StudentViewSet(viewsets.ModelViewSet):
    """ API endpoint per Docenti/Admin per gestire Studenti. """
    permission_classes = [permissions.IsAuthenticated, (IsTeacherUser | IsAdminUser), IsStudentOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == 'create' and self.request.user.is_teacher:
            return TeacherStudentCreateSerializer
        return StudentSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Student.objects.select_related('teacher', 'group')
        if user.is_admin:
            return queryset.all().order_by('last_name', 'first_name')
        elif user.is_teacher:
            return queryset.filter(teacher=user).order_by('last_name', 'first_name')
        else:
            return Student.objects.none()

    def perform_create(self, serializer):
        if self.request.user.is_teacher:
            serializer.save()
        elif self.request.user.is_admin:
            teacher_id = self.request.data.get('teacher')
            group_id = self.request.data.get('group_id')
            if not teacher_id:
                raise serializers.ValidationError({'teacher': 'Questo campo è richiesto per gli Admin.'})
            try:
                teacher = User.objects.get(pk=teacher_id, role=UserRole.TEACHER)
            except User.DoesNotExist:
                raise serializers.ValidationError({'teacher': 'Docente non valido specificato.'})
            group = None
            if group_id:
                try:
                    group = StudentGroup.objects.get(pk=group_id)
                except StudentGroup.DoesNotExist:
                     raise serializers.ValidationError({'group_id': 'Gruppo non valido specificato.'})
            first_name = serializer.validated_data.get('first_name')
            last_name = serializer.validated_data.get('last_name')
            student_code = generate_unique_student_code(first_name, last_name)
            raw_pin = generate_random_pin()
            student = serializer.save(teacher=teacher, group=group, student_code=student_code)
            try:
                student.set_pin(raw_pin)
                student.save(update_fields=['pin_hash'])
            except ValueError as e:
                 logger.error(f"Errore PIN studente creato da admin: {e}")
                 student.delete()
                 raise serializers.ValidationError(f"Errore generazione PIN: {e}")

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'], url_path='assignments')
    def get_student_assignments(self, request, pk=None):
        """ Restituisce le assegnazioni per uno studente specifico. """
        try:
            student = self.get_object()
        except Http404:
             logger.warning(f"Accesso assegnazioni studente non trovato/autorizzato (ID: {pk}) da utente {request.user.id}")
             raise
        quiz_assignments = QuizAssignment.objects.filter(student=student).select_related('quiz').order_by('-assigned_at')
        pathway_assignments = PathwayAssignment.objects.filter(student=student).select_related('pathway').order_by('-assigned_at')
        quiz_serializer = StudentQuizAssignmentSerializer(quiz_assignments, many=True)
        pathway_serializer = StudentPathwayAssignmentSerializer(pathway_assignments, many=True)
        return Response({
            'quiz_assignments': quiz_serializer.data,
            'pathway_assignments': pathway_serializer.data
        })


class StudentGroupViewSet(viewsets.ModelViewSet):
    """ API endpoint per Docenti per gestire i propri Gruppi. """
    serializer_class = StudentGroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser]

    def get_queryset(self):
        user = self.request.user
        if not user.is_teacher:
            return StudentGroup.objects.none()
        return StudentGroup.objects.filter(teacher=user)\
            .prefetch_related('members')\
            .annotate(member_count=Count('members'))\
            .order_by('name')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()


# --- ViewSet per Gestione Token Registrazione (Docente) ---

class StudentRegistrationTokenViewSet(mixins.CreateModelMixin,
                                  mixins.ListModelMixin,
                                  mixins.RetrieveModelMixin,
                                  mixins.DestroyModelMixin,
                                  viewsets.GenericViewSet):
    """
    API endpoint per Docenti per creare, visualizzare ed eliminare token di registrazione.
    I token non sono modificabili (update/partial_update non sono permessi).
    """
    serializer_class = StudentRegistrationTokenSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser]

    def get_queryset(self):
        """ Restituisce solo i token attivi creati dal docente autenticato. """
        user = self.request.user
        # Mostra solo token attivi e non scaduti? O tutti? Mostriamo tutti per ora.
        return StudentRegistrationToken.objects.filter(teacher=user).select_related('group').order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return StudentRegistrationTokenCreateSerializer
        return StudentRegistrationTokenSerializer

    def get_serializer_context(self):
        """ Aggiunge la request al contesto per la validazione del gruppo. """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        """ Crea il token associandolo al docente autenticato. """
        # Il serializer StudentRegistrationTokenCreateSerializer gestisce la creazione
        serializer.save() # Il teacher viene preso dal contesto nel serializer

    # Non permettiamo update (PATCH/PUT) perché non includiamo UpdateModelMixin

    # Potremmo aggiungere un'azione per disattivare un token manualmente se necessario
    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate_token(self, request, pk=None):
        """ Disattiva manualmente un token di registrazione. """
        try:
            token_instance = self.get_object() # get_object usa il queryset filtrato
            if token_instance.is_active:
                token_instance.is_active = False
                token_instance.save(update_fields=['is_active'])
                logger.info(f"Docente {request.user.username} ha disattivato il token {token_instance.token}")
                return Response({'status': 'Token disattivato'}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'Token già inattivo'}, status=status.HTTP_200_OK)
        except Http404:
            return Response({'detail': 'Token non trovato o non appartenente a questo docente.'}, status=status.HTTP_404_NOT_FOUND)


# --- Viste Pubbliche per Registrazione Studente ---

class ValidateStudentRegistrationTokenView(APIView):
    """
    Endpoint pubblico per validare un token di registrazione prima di mostrare il form.
    Restituisce info sul docente/gruppo se valido.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, token, *args, **kwargs):
        try:
            token_uuid = uuid.UUID(token) # Convalida formato UUID
            token_instance = StudentRegistrationToken.objects.select_related('teacher', 'group').get(token=token_uuid)

            if token_instance.is_valid():
                # Restituisci dati utili per il frontend
                data = {
                    'token': str(token_instance.token),
                    'teacher_name': token_instance.teacher.get_full_name() or token_instance.teacher.username,
                    'group_name': token_instance.group.name if token_instance.group else None,
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Token non valido o scaduto.'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, StudentRegistrationToken.DoesNotExist):
            # ValueError se 'token' non è un UUID valido
            return Response({'detail': 'Token non valido.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Errore imprevisto validazione token {token}: {e}")
            return Response({'detail': 'Errore interno del server.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentSelfRegisterView(generics.CreateAPIView):
    """
    Endpoint pubblico per permettere a uno studente di registrarsi
    usando un token valido, nome, cognome e PIN.
    """
    serializer_class = StudentSelfRegisterSerializer # Usato per l'INPUT
    permission_classes = [permissions.AllowAny]

    # Sovrascriviamo il metodo create per usare un serializer diverso per l'OUTPUT
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = self.perform_create(serializer) # perform_create ora restituisce solo l'istanza

        # Usiamo StudentSerializer per l'output
        output_serializer = StudentSerializer(student, context=self.get_serializer_context())
        headers = self.get_success_headers(output_serializer.data)

        # Aggiungiamo manualmente il PIN alla risposta (se presente sull'istanza temporanea)
        response_data = output_serializer.data
        if hasattr(student, 'pin'):
             response_data['pin'] = student.pin

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    # perform_create ora restituisce solo l'istanza dello studente
    def perform_create(self, serializer):
        """
        Il serializer StudentSelfRegisterSerializer gestisce la creazione dello studente.
        """
        # La gestione delle eccezioni ora avviene nel metodo create sovrascritto
        student = serializer.save()
        logger.info(f"Nuovo studente {student.student_code} registrato con token {serializer.validated_data['token']}")
        return student


# --- Student Authentication ---

class StudentLoginView(APIView):
    """ View per il login dello studente usando student_code e PIN. """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        student_code = request.data.get('student_code')
        pin = request.data.get('pin')
        if not student_code or not pin:
            return Response({'detail': 'Codice studente e PIN sono richiesti.'}, status=status.HTTP_400_BAD_REQUEST)

        student = authenticate(request, username=student_code, password=pin)
        if student is not None:
            refresh = RefreshToken()
            refresh['student_id'] = student.pk
            refresh['student_code'] = student.student_code
            refresh['is_student'] = True
            access = refresh.access_token
            access['student_id'] = student.pk
            access['student_code'] = student.student_code
            access['is_student'] = True
            serializer = StudentSerializer(student)
            return Response({
                'refresh': str(refresh),
                'access': str(access),
                'student': serializer.data
            })
        else:
            return Response({'detail': 'Codice studente o PIN non validi.'}, status=status.HTTP_401_UNAUTHORIZED)


# View semplice per testare l'autenticazione studente
class StudentProtectedTestView(APIView):
    """ Endpoint protetto accessibile solo da studenti autenticati. """
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    def get(self, request):
        return Response({"message": "Access granted", "student_id": request.student.pk})


# --- Teacher Views (Sommario e Dashboard) ---

class TeacherStudentProgressSummaryView(generics.ListAPIView):
    """ Restituisce un sommario dei progressi per gli studenti del docente. """
    serializer_class = StudentProgressSummarySerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser]

    def get_queryset(self):
        teacher = self.request.user
        student_id = self.request.query_params.get('student_id')
        queryset = Student.objects.filter(teacher=teacher).select_related('group')
        if student_id:
            try:
                queryset = queryset.filter(pk=int(student_id))
                if not queryset.exists():
                    logger.warning(f"Docente {teacher.username} richiesto progressi studente non suo/inesistente: {student_id}")
                    return Student.objects.none()
            except (ValueError, TypeError):
                logger.warning(f"Docente {teacher.username} fornito student_id non valido: {student_id}")
                return Student.objects.none()
        # Annotazioni
        completed_quizzes = QuizAttempt.objects.filter(student=OuterRef('pk'), status=QuizAttempt.AttemptStatus.COMPLETED).values('student').annotate(count=Count('id')).values('count')
        completed_pathways = PathwayProgress.objects.filter(student=OuterRef('pk'), status=PathwayProgress.ProgressStatus.COMPLETED).values('student').annotate(count=Count('id')).values('count')
        total_points = Wallet.objects.filter(student=OuterRef('pk')).values('current_points')
        avg_score_subquery = QuizAttempt.objects.filter(student=OuterRef('pk'), status=QuizAttempt.AttemptStatus.COMPLETED).values('student').annotate(avg_s=Avg('score')).values('avg_s')
        queryset = queryset.annotate(
            completed_quizzes_count=Subquery(completed_quizzes[:1], output_field=models.IntegerField()),
            completed_pathways_count=Subquery(completed_pathways[:1], output_field=models.IntegerField()),
            total_points_earned=Subquery(total_points[:1], output_field=models.IntegerField()),
            average_quiz_score=Subquery(avg_score_subquery[:1], output_field=models.FloatField())
        ).order_by('last_name', 'first_name')
        return queryset


class TeacherDashboardDataView(APIView):
    """ Restituisce dati aggregati per la dashboard del docente. """
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser]
    def get(self, request, *args, **kwargs):
        teacher = request.user
        student_count = Student.objects.filter(teacher=teacher).count()
        group_count = StudentGroup.objects.filter(teacher=teacher).count()
        quiz_template_count = QuizTemplate.objects.filter(teacher=teacher).count()
        pathway_template_count = PathwayTemplate.objects.filter(teacher=teacher).count()
        pending_manual_answers_count = StudentAnswer.objects.filter(
            quiz_attempt__quiz__teacher=teacher,
            question__question_type=QuestionType.OPEN_ANSWER_MANUAL,
            is_correct__isnull=True
        ).count()
        data = {
            'student_count': student_count, 'group_count': group_count,
            'quiz_template_count': quiz_template_count, 'pathway_template_count': pathway_template_count,
            'pending_manual_answers_count': pending_manual_answers_count,
        }
        return Response(data)

# Refactoring completato: Rimossa relazione M2M ridondante da StudentGroup.
# L'appartenenza al gruppo è gestita tramite Student.group (ForeignKey).
