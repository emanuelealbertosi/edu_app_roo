import logging # Import logging
from rest_framework import viewsets, permissions, serializers, generics
from rest_framework.decorators import action # Import action
from rest_framework.response import Response # Import Response
from django.db import models # Importa models
from django.db.models import Count, Sum, Q, OuterRef, Subquery, F # Aggiungi F
from .models import User, Student, UserRole, RegistrationToken # Aggiungi RegistrationToken
# Importa tutti i serializer necessari
from .serializers import (
    UserSerializer, StudentSerializer, UserCreateSerializer,
    StudentProgressSummarySerializer, RegistrationTokenSerializer,
    StudentRegistrationSerializer, GroupTokenRegistrationSerializer, # Aggiungi GroupTokenRegistrationSerializer
    StudentProfileUpdateSerializer # Import per la rettifica GDPR
)
# Importa modelli da altre app per le annotazioni
from apps.education.models import QuizAttempt, PathwayProgress
from apps.rewards.models import Wallet
from rest_framework import mixins # Importa mixins
# Importa modelli necessari per la nuova logica queryset studenti
from apps.student_groups.models import StudentGroup, GroupAccessRequest

# Get an instance of a logger
logger = logging.getLogger(__name__)
from .permissions import IsAdminUser, IsTeacherUser, IsStudentOwnerOrAdmin, IsStudent

# Import GDPR serializers from other apps
from apps.rewards.serializers import (
    GDPRWalletSerializer, GDPRPointTransactionSerializer, GDPRRewardPurchaseSerializer, EarnedBadgeSerializer # Changed GDPREarnedBadgeSerializer to EarnedBadgeSerializer
)
from apps.education.gdpr_serializers import (
    GDPRQuizAttemptSerializer, GDPRPathwayProgressSerializer,
    GDPRQuizAssignmentSerializer, GDPRPathwayAssignmentSerializer
    # GDPRStudentAnswerSerializer is nested in GDPRQuizAttemptSerializer
)
from apps.student_groups.gdpr_serializers import GDPRStudentGroupMembershipSerializer

# Import models needed for queries in GDPR export
from apps.rewards.models import Wallet, PointTransaction, RewardPurchase, EarnedBadge
# QuizAttempt, PathwayProgress already imported
from apps.education.models import QuizAssignment, PathwayAssignment
# StudentGroupMembership already imported via student_groups.models

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint che permette agli Admin di visualizzare o modificare Utenti (Admin/Docenti).
    """
    queryset = User.objects.all().order_by('-date_joined')
    # serializer_class = UserSerializer # Rimosso, useremo get_serializer_class
    permission_classes = [permissions.IsAuthenticated, IsAdminUser] # Solo Admin autenticati

    def get_serializer_class(self):
        """ Restituisce il serializer appropriato in base all'azione. """
        # Aggiungiamo il caso per 'me' se necessario, ma UserSerializer dovrebbe andare bene
        if self.action == 'me':
             return UserSerializer # Usa il serializer standard per i dati utente
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer # Default per list, retrieve, update, etc.

    @action(detail=False, methods=['get'], url_path='me', permission_classes=[permissions.IsAuthenticated]) # Ripristinato permesso
    def me(self, request):
        """
        Restituisce i dati dell'utente autenticato.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

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
            # Nuova logica: Trova studenti nei gruppi posseduti o accessibili dal docente
            # 1. Trova ID gruppi posseduti
            owned_group_ids = StudentGroup.objects.filter(owner=user).values_list('id', flat=True)
            # 2. Trova ID gruppi con accesso approvato
            approved_group_ids = GroupAccessRequest.objects.filter(
                requesting_teacher=user,
                status=GroupAccessRequest.AccessStatus.APPROVED
            ).values_list('group_id', flat=True)
            # 3. Combina gli ID
            accessible_group_ids = set(owned_group_ids) | set(approved_group_ids)
            # 4. Filtra studenti membri di questi gruppi
            return Student.objects.filter(
                group_memberships__group_id__in=accessible_group_ids
            ).distinct().order_by('last_name', 'first_name')
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
        # La logica originale per perform_create assumeva che uno studente fosse legato
        # DIRETTAMENTE a un docente. Ora l'associazione avviene tramite gruppi.
        # La creazione di uno studente da parte di un docente/admin dovrebbe ora
        # probabilmente avvenire in un contesto diverso (es. aggiunta a un gruppo specifico
        # o registrazione tramite token).
        # Rimuoviamo temporaneamente l'associazione automatica del 'teacher'.
        # Il serializer StudentSerializer non dovrebbe più avere 'teacher' come campo scrivibile.
        # NOTA: Questo potrebbe richiedere modifiche a StudentSerializer.
        # if self.request.user.is_teacher:
        #     # Non associamo più il teacher direttamente qui
        #     # serializer.save(teacher=self.request.user)
        #     serializer.save() # Salva senza teacher
        # elif self.request.user.is_admin:
        #      L'Admin non può più specificare un 'teacher' diretto qui.
        #      La logica di assegnazione a un docente avverrà tramite gruppi.
        #      teacher_id = self.request.data.get('teacher')
        #      if not teacher_id:
        #          raise serializers.ValidationError({'teacher': 'Questo campo è richiesto per gli Admin.'})
        #      try:
        #          teacher = User.objects.get(pk=teacher_id, role=UserRole.TEACHER)
        #      except User.DoesNotExist:
        #          logger.warning(f"Admin {request.user.username} ha tentato di creare uno studente con ID docente non valido: {teacher_id}")
        #          raise serializers.ValidationError({'teacher': 'Docente non valido specificato.'})
        #      serializer.save(teacher=teacher)
        #      serializer.save() # Salva senza teacher
        # else:
        #      # Gestione errore se non è né docente né admin (improbabile con i permessi)
        #      raise PermissionDenied("Azione non permessa.")

        # Semplificato: salva lo studente senza associare un docente qui.
        # L'associazione avverrà tramite l'aggiunta a un gruppo.
        serializer.save()
        # TODO: Rivedere StudentSerializer per rimuovere 'teacher' come campo modificabile/richiesto se presente.

        # La logica originale per Admin è commentata sotto:
        # elif self.request.user.is_admin:
            # # L'Admin deve specificare il docente nel payload della richiesta.
            # # Dato che 'teacher' è read_only nel serializer, lo recuperiamo dalla request.data
            # # e lo passiamo esplicitamente a save().
            # teacher_id = self.request.data.get('teacher')
            # if not teacher_id:
            #     raise serializers.ValidationError({'teacher': 'Questo campo è richiesto per gli Admin.'})
            # try:
            #     # Verifichiamo che l'ID corrisponda a un Docente valido
            #     teacher = User.objects.get(pk=teacher_id, role=UserRole.TEACHER)
            # except User.DoesNotExist:
            #     logger.warning(f"Admin {request.user.username} ha tentato di creare uno studente con ID docente non valido: {teacher_id}")
            #     raise serializers.ValidationError({'teacher': 'Docente non valido specificato.'})
            # serializer.save(teacher=teacher) # Passiamo il docente esplicitamente
        # Non dovrebbe essere possibile arrivare qui per altri tipi di utente.


# --- Student Authentication ---

from django.contrib.auth import login, logout, authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, serializers # Import serializers
# Import per JWT
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import StudentTokenRefreshSerializer # Importa il nuovo serializer
from rest_framework_simplejwt.tokens import RefreshToken # Assicurati che sia importato

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
        # Modificato per restituire i dati completi dello studente serializzati
        serializer = StudentSerializer(request.student) # Usa StudentSerializer
        logger.debug(f"Returning full student data for student ID {request.student.pk} in StudentProtectedTestView")
        return Response(serializer.data) # Restituisce i dati serializzati


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

        # Queryset base: studenti associati al docente tramite gruppi
        # (Stessa logica di StudentViewSet.get_queryset)
        owned_group_ids = StudentGroup.objects.filter(owner=teacher).values_list('id', flat=True)
        approved_group_ids = GroupAccessRequest.objects.filter(
            requesting_teacher=teacher,
            status=GroupAccessRequest.AccessStatus.APPROVED
        ).values_list('group_id', flat=True)
        accessible_group_ids = set(owned_group_ids) | set(approved_group_ids)
        queryset = Student.objects.filter(
            group_memberships__group_id__in=accessible_group_ids
        ).distinct()

        # Annotazioni per i dati aggregati (restano valide)
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


# --- Registration Token Views ---

class RegistrationTokenViewSet(mixins.CreateModelMixin,
                               mixins.ListModelMixin,
                               mixins.RetrieveModelMixin,
                               viewsets.GenericViewSet):
    """
    API endpoint che permette ai Docenti autenticati di creare e visualizzare
    i propri token di registrazione per gli studenti.
    """
    serializer_class = RegistrationTokenSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser] # Solo Docenti

    def get_queryset(self):
        """ Restituisce solo i token creati dal docente autenticato. """
        # Ordina per data di scadenza decrescente, mostrando prima i più recenti/validi
        return RegistrationToken.objects.filter(teacher=self.request.user).order_by('-expires_at')

    def perform_create(self, serializer):
        """ Associa automaticamente il token al Docente autenticato durante la creazione. """
        # Potremmo aggiungere logica qui, ad esempio limitare il numero di token attivi per docente.
        logger.info(f"Teacher {self.request.user.username} is creating a new registration token.")
        serializer.save(teacher=self.request.user)


class StudentRegistrationView(generics.CreateAPIView):
    """
    API endpoint pubblico per la registrazione di un nuovo studente
    utilizzando un token di registrazione valido.
    """
    serializer_class = StudentRegistrationSerializer
    permission_classes = [permissions.AllowAny] # Accesso pubblico

    def perform_create(self, serializer):
        """
        Esegue la creazione dello studente (la logica è nel serializer).
        Logga l'evento.
        """
        # La validazione del token e la creazione dello studente/wallet
        # avvengono nel metodo create del serializer.
        # Il serializer.save() ora non associa più il teacher direttamente.
        # Il teacher viene recuperato dal token dentro il serializer.
        student, teacher = serializer.save() # Il serializer ora restituisce anche il teacher associato tramite token
        logger.info(f"New student '{student.full_name}' (Code: {student.student_code}) registered successfully using token {serializer.validated_data['token']} for teacher {teacher.username}.")
        # Restituiamo solo lo studente, il teacher non serve qui
        return student

    def create(self, request, *args, **kwargs):
        """
        Sovrascrive il metodo create per restituire i dati dello studente creato
        utilizzando StudentSerializer invece dei dati del serializer di input.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = self.perform_create(serializer) # perform_create ora restituisce lo studente
        # Log dell'oggetto studente PRIMA della serializzazione per la risposta
        logger.debug(f"Student object BEFORE response serialization: id={student.id}, name={student.full_name}, code={student.student_code}, active={student.is_active}")
        # Ora serializza lo studente creato per la risposta
        student_data = StudentSerializer(student, context=self.get_serializer_context()).data
        # Log dei dati serializzati prima di inviarli
        logger.debug(f"Serialized student data being returned after registration: {student_data}")
        headers = self.get_success_headers(student_data) # Usa student_data per gli header
        return Response(student_data, status=status.HTTP_201_CREATED, headers=headers)


# --- Student Token Refresh View ---

class StudentTokenRefreshView(TokenRefreshView):
    """
    View personalizzata per il refresh del token JWT per gli Studenti.
    Utilizza StudentTokenRefreshSerializer per la validazione.
    """
    serializer_class = StudentTokenRefreshSerializer

# --- Group Token Registration View ---

class GroupTokenRegistrationView(generics.CreateAPIView):
    """
    API endpoint pubblico per la registrazione di un nuovo studente
    utilizzando un token di registrazione di gruppo valido.
    """
    serializer_class = GroupTokenRegistrationSerializer
    permission_classes = [permissions.AllowAny] # Accesso pubblico

    def perform_create(self, serializer):
        """
        Esegue la creazione dello studente e l'aggiunta al gruppo (la logica è nel serializer).
        Logga l'evento.
        """
        # La validazione del token, la creazione dello studente/wallet e della membership
        # avvengono nel metodo create del serializer.
        student = serializer.save() # Il serializer restituisce lo studente creato
        group = serializer.context['group_instance'] # Recupera il gruppo dal contesto
        logger.info(f"New student '{student.full_name}' (Code: {student.student_code}) registered successfully using group token {serializer.validated_data['token']} for group '{group.name}' (ID: {group.id}).")
        return student

    def create(self, request, *args, **kwargs):
        """
        Sovrascrive il metodo create per restituire i dati dello studente creato
        utilizzando StudentSerializer invece dei dati del serializer di input.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = self.perform_create(serializer) # perform_create restituisce lo studente

        # --- Generazione Token JWT ---
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
        # --- Fine Generazione Token JWT ---

        # Serializza lo studente creato per la risposta usando StudentSerializer
        student_data = StudentSerializer(student, context=self.get_serializer_context()).data
        logger.debug(f"Serialized student data being returned after group token registration: {student_data}")

        # Costruisci la risposta nel formato atteso dal frontend
        response_data = {
            'refresh': str(refresh),
            'access': str(access),
            'student': student_data
        }

        headers = self.get_success_headers(response_data) # Usa response_data per gli header
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

from rest_framework.views import APIView
from rest_framework import status # Assicurati che status sia importato
from django.utils import timezone # Import timezone per il timestamp

class UserDataExportView(APIView):
    """
    API endpoint per utenti (Admin, Docente, Studente) per esportare i propri dati personali
    come richiesto dall'Articolo 15 GDPR (Diritto di accesso).
    """
    permission_classes = [permissions.IsAuthenticated] # Deve essere loggato

    def get(self, request, *args, **kwargs):
        """
        Gestisce la richiesta GET per esportare i dati dell'utente autenticato.
        """
        user = request.user # Questo sarà User (Admin/Teacher) o Student

        if isinstance(user, User):
            # Logica per l'esportazione dati Admin/Docente
            logger.info(f"Inizio esportazione dati GDPR per User ID: {user.pk} ({user.username})")
            user_data = self._get_admin_teacher_data(user)
            logger.info(f"Fine esportazione dati GDPR per User ID: {user.pk}")
            # TODO: Serializzare user_data con un serializer specifico
            return Response(user_data) # Restituisce i dati raccolti (placeholder)

        elif isinstance(user, Student):
            # Logica per l'esportazione dati Studente
            logger.info(f"Inizio esportazione dati GDPR per Student ID: {user.pk} ({user.student_code})")
            user_data = self._get_student_data(user)
            logger.info(f"Fine esportazione dati GDPR per Student ID: {user.pk}")
            # user_data contiene già i dati serializzati dal metodo _get_student_data
            return Response(user_data) # Restituisce i dati serializzati

        else:
            # Non dovrebbe accadere con IsAuthenticated, ma gestiamo difensivamente
            logger.error(f"Tentativo di accesso a UserDataExportView da utente non riconosciuto: {type(user)}")
            return Response({"detail": "Utente non riconosciuto."}, status=status.HTTP_400_BAD_REQUEST)

    def _get_admin_teacher_data(self, user: User):
        """
        Raccoglie i dati rilevanti per un Admin o Docente.
        Placeholder - da implementare con query e serializer specifici.
        """
        # Dati base del profilo User
        profile_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "date_joined": user.date_joined,
            "is_active": user.is_active,
            "privacy_policy_accepted_at": user.privacy_policy_accepted_at,
            "terms_of_service_accepted_at": user.terms_of_service_accepted_at,
            "can_create_public_groups": user.can_create_public_groups,
        }

        # TODO: Aggiungere query per recuperare:
        # - Quiz Templates creati (se Admin)
        # - Reward Templates creati (globali se Admin, locali se Docente)
        # - Gruppi posseduti (se Docente)
        # - Richieste di accesso a gruppi inviate/ricevute (se Docente)
        # - Studenti creati tramite token (RegistrationToken)
        # - Quiz/Percorsi/Lezioni create (se Docente)
        # - Ricompense create (se Docente)
        # - Correzioni manuali effettuate (StudentAnswer con score manuale?)
        # - Consegne ricompense effettuate (RewardPurchase)

        data = {
            "user_type": "Admin/Teacher",
            "profile": profile_data,
            "created_content": "PLACEHOLDER - Dati su quiz, percorsi, ricompense, template, gruppi creati...",
            "student_interactions": "PLACEHOLDER - Dati su token generati, correzioni, consegne..."
        }
        return data

    def _get_student_data(self, student: Student):
        """
        Raccoglie e serializza i dati personali rilevanti per uno Studente per l'esportazione GDPR.
        """
        # 1. Dati Profilo Studente (usando StudentSerializer per ora, potrebbe essere raffinato con GDPRStudentSerializer)
        profile_data = StudentSerializer(student).data
        # Considera la rimozione di campi non essenziali se StudentSerializer è troppo ampio
        # profile_data.pop('teacher', None) # Esempio

        # 2. Dati Wallet
        try:
            wallet = Wallet.objects.get(student=student)
            wallet_data = GDPRWalletSerializer(wallet).data
        except Wallet.DoesNotExist:
            wallet_data = None
            logger.warning(f"Nessun wallet trovato per lo studente {student.pk} durante l'esportazione GDPR.")

        # 3. Transazioni Punti
        point_transactions = PointTransaction.objects.filter(wallet__student=student).order_by('-timestamp')
        point_transactions_data = GDPRPointTransactionSerializer(point_transactions, many=True).data

        # 4. Acquisti Ricompense
        reward_purchases = RewardPurchase.objects.filter(student=student).order_by('-purchased_at')
        reward_purchases_data = GDPRRewardPurchaseSerializer(reward_purchases, many=True).data

        # 5. Badge Guadagnati
        earned_badges = EarnedBadge.objects.filter(student=student).order_by('-earned_at')
        earned_badges_data = GDPREarnedBadgeSerializer(earned_badges, many=True).data

        # 6. Tentativi Quiz (include risposte tramite serializer nidificato)
        quiz_attempts = QuizAttempt.objects.filter(student=student).select_related('quiz').prefetch_related('student_answers', 'student_answers__question').order_by('-started_at')
        quiz_attempts_data = GDPRQuizAttemptSerializer(quiz_attempts, many=True).data

        # 7. Progresso Percorsi
        pathway_progress = PathwayProgress.objects.filter(student=student).select_related('pathway').order_by('-started_at')
        pathway_progress_data = GDPRPathwayProgressSerializer(pathway_progress, many=True).data

        # 8. Assegnazioni Quiz
        quiz_assignments = QuizAssignment.objects.filter(student=student).select_related('quiz').order_by('-assigned_at')
        quiz_assignments_data = GDPRQuizAssignmentSerializer(quiz_assignments, many=True).data

        # 9. Assegnazioni Percorsi
        pathway_assignments = PathwayAssignment.objects.filter(student=student).select_related('pathway').order_by('-assigned_at')
        pathway_assignments_data = GDPRPathwayAssignmentSerializer(pathway_assignments, many=True).data

        # 10. Appartenenza a Gruppi
        # Import necessario qui dentro se non globale
        from apps.student_groups.models import StudentGroupMembership
        group_memberships = StudentGroupMembership.objects.filter(student=student).select_related('group', 'group__owner').order_by('-joined_at')
        group_memberships_data = GDPRStudentGroupMembershipSerializer(group_memberships, many=True).data


        # Combina tutti i dati
        data = {
            "profile": profile_data,
            "wallet": wallet_data,
            "point_transactions": point_transactions_data,
            "reward_purchases": reward_purchases_data,
            "earned_badges": earned_badges_data,
            "quiz_attempts": quiz_attempts_data,
            "pathway_progress": pathway_progress_data,
            "quiz_assignments": quiz_assignments_data,
            "pathway_assignments": pathway_assignments_data,
            "group_memberships": group_memberships_data,
        }
        return data

# --- Student Profile Update View (GDPR Rectification) ---

class StudentProfileUpdateView(generics.UpdateAPIView):
    """
    API endpoint per permettere allo studente autenticato di aggiornare
    il proprio profilo (nome, cognome) per la rettifica GDPR.
    Utilizza PATCH per aggiornamenti parziali.
    """
    serializer_class = StudentProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get_object(self):
        """ Restituisce l'oggetto studente autenticato. """
        # request.user qui è l'istanza Student grazie a StudentJWTAuthentication
        return self.request.user

    def perform_update(self, serializer):
        """ Esegue l'aggiornamento e logga l'evento. """
        student = serializer.save()
        logger.info(f"Studente ID {student.pk} ({student.student_code}) ha aggiornato il proprio profilo (nome/cognome).")

    # Non è necessario implementare partial_update esplicitamente
    # perché UpdateAPIView lo gestisce di default con PATCH.


# --- GDPR Data Deletion Request View ---

class UserDataDeletionRequestView(APIView):
    """
    API endpoint per utenti (Admin, Docente, Studente) per richiedere la cancellazione
    dei propri dati personali (Articolo 17 GDPR - Diritto all'oblio).
    La cancellazione effettiva è gestita asincronamente.
    """
    permission_classes = [permissions.IsAuthenticated] # Deve essere loggato

    def post(self, request, *args, **kwargs):
        """
        Gestisce la richiesta POST per avviare il processo di cancellazione dati.
        """
        user = request.user # User (Admin/Teacher) o Student

        # Identifica il tipo di utente
        user_type = ""
        user_identifier = ""
        if isinstance(user, User):
            user_type = "User (Admin/Teacher)"
            user_identifier = f"ID: {user.pk} ({user.username})"
        elif isinstance(user, Student):
            user_type = "Student"
            user_identifier = f"ID: {user.pk} ({user.student_code})"
        else:
            logger.error(f"Tentativo di richiesta cancellazione da utente non riconosciuto: {type(user)}")
            return Response({"detail": "Tipo utente non supportato per la cancellazione."}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Ricevuta richiesta di cancellazione dati GDPR per {user_type} {user_identifier}")

        # --- Logica di gestione richiesta: Imposta Flag ---
        now = timezone.now()
        user.is_deletion_requested = True
        user.deletion_requested_at = now
        user.save(update_fields=['is_deletion_requested', 'deletion_requested_at'])
        logger.info(f"Richiesta di cancellazione marcata per {user_type} {user_identifier} at {now}. Il processo asincrono gestirà la cancellazione effettiva.")
        # --------------------------------------------------

        # Restituisce 202 Accepted per indicare che la richiesta è stata ricevuta
        # e verrà processata (ma non è ancora completata).
        return Response(
            {"detail": "La tua richiesta di cancellazione dati è stata ricevuta e verrà processata."},
            status=status.HTTP_202_ACCEPTED
        )


# --- Parental Consent Verification View ---

from django.shortcuts import get_object_or_404, render # Import render for HTML response
from django.utils import timezone
from .models import Student # Import Student

class ParentalConsentVerificationView(APIView):
    """
    Gestisce la verifica del token di consenso parentale inviato via email.
    Attiva l'account dello studente se il token è valido.
    """
    permission_classes = [permissions.AllowAny] # Accessibile pubblicamente

    def get(self, request, token, *args, **kwargs):
        """
        Gestisce la richiesta GET sull'URL di verifica.
        """
        logger.info(f"Ricevuta richiesta di verifica consenso parentale con token: {token}")

        try:
            # Cerca lo studente con il token specificato e stato PENDING
            student = get_object_or_404(
                Student,
                parental_consent_verification_token=token,
                parental_consent_status='PENDING'
            )

            # Verifica scadenza token
            if student.parental_consent_token_expires_at and student.parental_consent_token_expires_at < timezone.now():
                logger.warning(f"Tentativo di verifica con token scaduto per studente {student.id}. Token: {token}")
                # Potremmo offrire un modo per rigenerare il token qui
                # Per ora, restituiamo un errore semplice
                # return Response({"detail": "Token di verifica scaduto."}, status=status.HTTP_400_BAD_REQUEST)
                return render(request, 'verification_result.html', {'success': False, 'message': 'Il link di verifica è scaduto.'})


            # Token valido e non scaduto: aggiorna lo studente
            student.parental_consent_status = 'GRANTED'
            student.is_active = True # Attiva l'account dello studente
            student.parental_consent_granted_at = timezone.now()
            # Invalida il token per prevenire riutilizzi
            student.parental_consent_verification_token = None
            student.parental_consent_token_expires_at = None
            student.save(update_fields=[
                'parental_consent_status', 'is_active', 'parental_consent_granted_at',
                'parental_consent_verification_token', 'parental_consent_token_expires_at'
            ])

            logger.info(f"Consenso parentale concesso e account attivato per studente {student.id} tramite token {token}.")
            # Restituisce una pagina HTML di successo semplice
            # return Response({"detail": "Consenso parentale verificato con successo. L'account dello studente è ora attivo."}, status=status.HTTP_200_OK)
            return render(request, 'verification_result.html', {
                'success': True,
                'message': f"Grazie! Il consenso per l'account di {student.full_name} è stato registrato con successo. L'account è ora attivo."
            })

        except Student.DoesNotExist:
            logger.warning(f"Tentativo di verifica con token non valido o già utilizzato: {token}")
            # return Response({"detail": "Token di verifica non valido o già utilizzato."}, status=status.HTTP_404_NOT_FOUND)
            return render(request, 'verification_result.html', {'success': False, 'message': 'Il link di verifica non è valido o è già stato utilizzato.'})

        except Exception as e:
            logger.error(f"Errore imprevisto durante la verifica del consenso parentale con token {token}: {e}", exc_info=True)
            # return Response({"detail": "Si è verificato un errore durante la verifica."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return render(request, 'verification_result.html', {'success': False, 'message': 'Si è verificato un errore imprevisto durante la verifica. Riprova più tardi.'})

# --- Template Esempio (da creare in templates/verification_result.html) ---
"""
<!DOCTYPE html>
<html>
<head>
    <title>Verifica Consenso Parentale</title>
    <style>
        body { font-family: sans-serif; padding: 20px; }
        .message { padding: 15px; border-radius: 5px; margin-bottom: 15px; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <h1>Verifica Consenso Parentale</h1>
    {% if success %}
        <div class="message success">
            {{ message }}
        </div>
        <p>Lo studente può ora accedere alla piattaforma utilizzando il suo codice studente e PIN.</p>
    {% else %}
        <div class="message error">
            {{ message }}
        </div>
        <p>Se ritieni che si tratti di un errore, contatta il supporto.</p>
    {% endif %}
</body>
</html>
"""
