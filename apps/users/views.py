import logging # Import logging
from rest_framework import viewsets, permissions, serializers, generics
from django.db import models # Importa models
from django.db.models import Count, Sum, Q, OuterRef, Subquery
from .models import User, Student, UserRole
# Importa tutti i serializer necessari
from .serializers import UserSerializer, StudentSerializer, UserCreateSerializer, StudentProgressSummarySerializer
# Importa modelli da altre app per le annotazioni
from apps.education.models import QuizAttempt, PathwayProgress
from apps.rewards.models import Wallet

# Get an instance of a logger
logger = logging.getLogger(__name__)
from .permissions import IsAdminUser, IsTeacherUser, IsStudentOwnerOrAdmin, IsStudent

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint che permette agli Admin di visualizzare o modificare Utenti (Admin/Docenti).
    """
    queryset = User.objects.all().order_by('-date_joined')
    # serializer_class = UserSerializer # Rimosso, useremo get_serializer_class
    permission_classes = [permissions.IsAuthenticated, IsAdminUser] # Solo Admin autenticati

    def get_serializer_class(self):
        """ Restituisce il serializer appropriato in base all'azione. """
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer # Default per list, retrieve, update, etc.

    # Potremmo aggiungere filtri o logica specifica per la creazione/aggiornamento qui
    # Ad esempio, impedire a un Admin di cambiare il proprio ruolo o eliminarsi.


class StudentViewSet(viewsets.ModelViewSet):
    """
    API endpoint che permette ai Docenti di visualizzare e modificare i PROPRI Studenti.
    Gli Admin possono vedere/modificare tutti gli studenti (tramite IsStudentOwnerOrAdmin).
    """
    serializer_class = StudentSerializer
    # I permessi vengono applicati in sequenza.
    # IsAuthenticated: Deve essere loggato.
    # IsTeacherUser | IsAdminUser: Deve essere Docente O Admin.
    # IsStudentOwnerOrAdmin: Applicato a livello di oggetto per retrieve/update/delete.
    permission_classes = [permissions.IsAuthenticated, (IsTeacherUser | IsAdminUser), IsStudentOwnerOrAdmin]

    def get_queryset(self):
        """
        Restituisce solo gli studenti associati al Docente autenticato,
        o tutti gli studenti se l'utente è un Admin.
        """
        user = self.request.user
        if user.is_admin:
            return Student.objects.all().order_by('last_name', 'first_name')
        elif user.is_teacher:
            return Student.objects.filter(teacher=user).order_by('last_name', 'first_name')
        else:
            # Teoricamente non dovrebbe accadere a causa dei permessi a livello di vista,
            # ma per sicurezza restituiamo un queryset vuoto.
            return Student.objects.none()

    def perform_create(self, serializer):
        """
        Associa automaticamente lo studente al Docente autenticato durante la creazione.
        Questo metodo viene chiamato solo se l'utente è un Docente (grazie ai permessi).
        Se un Admin crea uno studente, il campo 'teacher' deve essere fornito nel request body.
        """
        if self.request.user.is_teacher:
            serializer.save(teacher=self.request.user)
        elif self.request.user.is_admin:
            # L'Admin deve specificare il docente nel payload della richiesta.
            # Dato che 'teacher' è read_only nel serializer, lo recuperiamo dalla request.data
            # e lo passiamo esplicitamente a save().
            teacher_id = self.request.data.get('teacher')
            if not teacher_id:
                raise serializers.ValidationError({'teacher': 'Questo campo è richiesto per gli Admin.'})
            try:
                # Verifichiamo che l'ID corrisponda a un Docente valido
                teacher = User.objects.get(pk=teacher_id, role=UserRole.TEACHER)
            except User.DoesNotExist:
                logger.warning(f"Admin {request.user.username} ha tentato di creare uno studente con ID docente non valido: {teacher_id}")
                raise serializers.ValidationError({'teacher': 'Docente non valido specificato.'})
            serializer.save(teacher=teacher) # Passiamo il docente esplicitamente
        # Non dovrebbe essere possibile arrivare qui per altri tipi di utente.


# --- Student Authentication ---

from django.contrib.auth import login, logout, authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, serializers # Import serializers
# Import per JWT
from rest_framework_simplejwt.tokens import RefreshToken

class StudentLoginView(APIView):
    """
    View per il login dello studente usando student_code e PIN.
    Usa il backend StudentCodeBackend.
    """
    permission_classes = [permissions.AllowAny] # Permette accesso non autenticato

    def post(self, request, *args, **kwargs):
        student_code = request.data.get('student_code')
        pin = request.data.get('pin')

        if not student_code or not pin:
            return Response(
                {'detail': 'Codice studente e PIN sono richiesti.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Usa authenticate di Django, che proverà tutti i backend in AUTHENTICATION_BACKENDS
        # Passiamo student_code come 'username' e pin come 'password' come atteso dal nostro backend
        student = authenticate(request, username=student_code, password=pin)

        if student is not None:
            # Autenticazione riuscita con StudentCodeBackend
            # 'student' è un'istanza del modello Student

            # Genera token JWT per lo studente
            # Aggiungiamo claim custom per identificare che è uno studente e il suo ID
            refresh = RefreshToken()
            refresh['student_id'] = student.pk
            refresh['student_code'] = student.student_code
            refresh['is_student'] = True # Claim custom per identificarlo facilmente

            # Genera l'access token dal refresh token e aggiungi i claim custom anche qui
            access = refresh.access_token
            access['student_id'] = student.pk
            access['student_code'] = student.student_code
            access['is_student'] = True

            # Non usiamo login() di Django qui, ci basiamo solo sui token
            # login(request, student, backend='apps.users.backends.StudentCodeBackend')

            serializer = StudentSerializer(student) # Info studente da restituire
            return Response({
                'refresh': str(refresh),
                'access': str(access), # Usa l'access token modificato
                'student': serializer.data
            })
        else:
            # Autenticazione fallita (o l'utente autenticato è un Admin/Docente, non uno Studente)
            return Response(
                {'detail': 'Codice studente o PIN non validi.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

from rest_framework.views import APIView # Import APIView

# Potremmo aggiungere StudentLogoutView se necessario

# View semplice per testare l'autenticazione studente
class StudentProtectedTestView(APIView):
    """ Endpoint protetto accessibile solo da studenti autenticati. """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        # request.student è disponibile grazie a StudentJWTAuthentication
        return Response({"message": "Access granted", "student_id": request.student.pk})


# --- Teacher Views ---

class TeacherStudentProgressSummaryView(generics.ListAPIView):
    """
    Restituisce un sommario dei progressi per tutti gli studenti
    associati al docente autenticato.
    """
    serializer_class = StudentProgressSummarySerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser] # Solo Docenti

    def get_queryset(self):
        teacher = self.request.user

        # Queryset base: studenti del docente
        queryset = Student.objects.filter(teacher=teacher)

        # Annotazioni per i dati aggregati
        # Conteggio Quiz Completati (con successo, basato sulla soglia del quiz)
        # Nota: Questo richiede un modo per definire/ottenere la soglia per ogni quiz.
        # Per semplicità ora contiamo solo gli status COMPLETED.
        # Una soluzione più precisa richiederebbe subquery più complesse o denormalizzazione.
        completed_quizzes = QuizAttempt.objects.filter(
            student=OuterRef('pk'),
            status=QuizAttempt.AttemptStatus.COMPLETED
            # Aggiungere filtro su score >= soglia se necessario e fattibile
        ).values('student').annotate(count=Count('id')).values('count')

        # Conteggio Percorsi Completati
        completed_pathways = PathwayProgress.objects.filter(
            student=OuterRef('pk'),
            status=PathwayProgress.ProgressStatus.COMPLETED
        ).values('student').annotate(count=Count('id')).values('count')

        # Punti totali guadagnati (dal Wallet)
        total_points = Wallet.objects.filter(
            student=OuterRef('pk')
        ).values('current_points') # Assumiamo che current_points rifletta il totale guadagnato - speso

        queryset = queryset.annotate(
            completed_quizzes_count=Subquery(completed_quizzes[:1], output_field=models.IntegerField()),
            completed_pathways_count=Subquery(completed_pathways[:1], output_field=models.IntegerField()),
            total_points_earned=Subquery(total_points[:1], output_field=models.IntegerField())
        ).order_by('last_name', 'first_name')

        # Imposta valori predefiniti a 0 se le subquery restituiscono None
        # Questo si può fare anche nel serializer con default=0
        # queryset = queryset.annotate(
        #     completed_quizzes_count=Coalesce(F('completed_quizzes_count'), 0),
        #     completed_pathways_count=Coalesce(F('completed_pathways_count'), 0),
        #     total_points_earned=Coalesce(F('total_points_earned'), 0)
        # )

        return queryset

# TODO: Aggiungere azione a StudentViewSet per i dettagli del progresso
# @action(detail=True, methods=['get'], url_path='progress-details')
# def progress_details(self, request, pk=None): ...
