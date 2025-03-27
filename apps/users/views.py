from rest_framework import viewsets, permissions, serializers # Import serializers for ValidationError
from .models import User, Student, UserRole # Import UserRole
from .serializers import UserSerializer, StudentSerializer
from .permissions import IsAdminUser, IsTeacherUser, IsStudentOwnerOrAdmin

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint che permette agli Admin di visualizzare o modificare Utenti (Admin/Docenti).
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser] # Solo Admin autenticati

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

            # Non usiamo login() di Django qui, ci basiamo solo sui token
            # login(request, student, backend='apps.users.backends.StudentCodeBackend')

            serializer = StudentSerializer(student) # Info studente da restituire
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'student': serializer.data
            })
        else:
            # Autenticazione fallita (o l'utente autenticato è un Admin/Docente, non uno Studente)
            return Response(
                {'detail': 'Codice studente o PIN non validi.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

# Potremmo aggiungere StudentLogoutView se necessario
