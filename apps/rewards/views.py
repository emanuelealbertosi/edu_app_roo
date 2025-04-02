from rest_framework import viewsets, permissions, status, serializers, generics # Import generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction, models # Add models
from django.shortcuts import get_object_or_404
from django.http import Http404 # Import Http404
from django.utils import timezone # Add this import
from django.utils import timezone # Add this import
import logging # Import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

from .models import (
    Wallet, PointTransaction, RewardTemplate, Reward, RewardPurchase
)
from .serializers import (
    WalletSerializer, PointTransactionSerializer, RewardTemplateSerializer,
    RewardSerializer, RewardPurchaseSerializer,
    StudentWalletDashboardSerializer # Importa il nuovo serializer
)
from .permissions import (
    IsAdminOrReadOnly, IsRewardTemplateOwnerOrAdmin, IsRewardOwnerOrAdmin, # Aggiornato nome permesso
    IsStudentOwnerForPurchase, IsTeacherOfStudentForPurchase
)
# Importa permessi da users, incluso IsStudentAuthenticated
from apps.users.permissions import IsAdminUser, IsTeacherUser, IsStudent, IsStudentAuthenticated
from apps.users.models import UserRole, Student # Import modelli utente
from .models import Wallet, PointTransaction # Assicurati che siano importati


class RewardTemplateViewSet(viewsets.ModelViewSet):
    """
    API endpoint per i Reward Templates.
    - Admin: CRUD completo su template globali. Lettura template locali.
    - Docente: CRUD completo sui propri template locali. Lettura template globali.
    """
    serializer_class = RewardTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsRewardTemplateOwnerOrAdmin] # IsAdminOrReadOnly gestito implicitamente

    def get_queryset(self):
        """
        Restricts the queryset based on the user role.
        - Admins see all templates (global and local).
        - Teachers see their own local templates and all global templates.
        """
        user = self.request.user
        # Importa User e Student qui per evitare import circolari a livello di modulo
        from apps.users.models import User, Student

        if isinstance(user, User) and user.is_admin:
            # Admin vede tutti i template (globali e locali)
            return RewardTemplate.objects.all()
        elif isinstance(user, User) and user.is_teacher:
            # Docente vede i propri locali + tutti i globali
            return RewardTemplate.objects.filter(
                models.Q(scope=RewardTemplate.RewardScope.GLOBAL) | models.Q(creator=user, scope=RewardTemplate.RewardScope.LOCAL)
            )
        # Gli studenti o altri utenti non vedono nulla tramite questo endpoint
        return RewardTemplate.objects.none()

    def perform_create(self, serializer):
        """
        Sets the creator and scope automatically based on the user role.
        - Admins create GLOBAL templates.
        - Teachers create LOCAL templates.
        """
        user = self.request.user
        # Importa User qui per evitare import circolari
        from apps.users.models import User

        scope = RewardTemplate.RewardScope.LOCAL # Default per Docente
        # Controlla che sia un User prima di accedere a is_admin/is_teacher
        if isinstance(user, User):
            if user.is_admin:
                # Admin può specificare lo scope nel payload, altrimenti default a GLOBAL?
                # Per semplicità, forziamo GLOBAL se creato da Admin.
                scope = RewardTemplate.RewardScope.GLOBAL
                # Potremmo aggiungere un controllo: se l'admin specifica scope=LOCAL, sollevare errore?
            elif not user.is_teacher:
                 raise serializers.ValidationError("Solo Admin o Docenti possono creare template.")
        else:
            # Se non è un User (es. Studente), non può creare
            raise serializers.ValidationError("Azione non permessa.")

        serializer.save(creator=user, scope=scope)


class RewardViewSet(viewsets.ModelViewSet):
    """
    API endpoint per le Reward specifiche.
    - Docente: CRUD completo sulle proprie ricompense.
    - Admin: Lettura di tutte le ricompense (per supervisione).
    - Studente: Lettura delle ricompense disponibili (gestito in endpoint separato 'shop').
    """
    serializer_class = RewardSerializer
    # Imposta permessi base, verranno specificati meglio in get_permissions
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Restricts the queryset based on the user role for list actions.
        - Admins see all rewards.
        - Teachers see only their own rewards.
        Object-level permissions handle retrieve/update/delete access.
        """
        user = self.request.user
        if user.is_admin:
            # Admin vede tutte le ricompense
            return Reward.objects.all().select_related('teacher')
        elif user.is_teacher:
            # Docente vede solo le proprie ricompense
            return Reward.objects.filter(teacher=user).select_related('teacher')
        # Studenti vedono le ricompense disponibili tramite l'endpoint 'shop'
        return Reward.objects.none()

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        Applica permessi più specifici per azioni su oggetti esistenti.
        """
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsRewardOwnerOrAdmin]
        elif self.action == 'create':
             # Per creare, basta essere un docente autenticato (verificato in perform_create)
            permission_classes = [permissions.IsAuthenticated, IsTeacherUser]
        else:
            # Per list o altre azioni custom a livello di lista, basta essere autenticato
            # (il queryset gestirà la visibilità per docenti/admin)
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_context(self):
        """ Aggiunge il docente al contesto per validazione studenti. """
        context = super().get_serializer_context()
        context['teacher'] = self.request.user
        return context

    def perform_create(self, serializer):
        """
        Sets the teacher automatically and validates specific student availability.
        Ensures that if 'available_to_specific_students' is provided,
        those students belong to the requesting teacher.
        """
        user = self.request.user
        if not user.is_teacher:
             raise serializers.ValidationError("Solo i Docenti possono creare ricompense.")

        # Validazione studenti specifici (assicura che appartengano al docente)
        specific_students_data = serializer.validated_data.get('available_to_specific_students', [])
        if specific_students_data:
            teacher_student_ids = set(user.students.values_list('id', flat=True))
            for student in specific_students_data:
                if student.id not in teacher_student_ids:
                    raise serializers.ValidationError(f"Lo studente {student.id} non appartiene a questo docente.")

        serializer.save(teacher=user)

    def perform_update(self, serializer):
        """
        Validates specific student availability during updates.
        Ensures that if 'available_to_specific_students' is provided in the update payload,
        those students belong to the requesting teacher.
        """
         # Simile a perform_create, validiamo gli studenti se vengono modificati
        user = self.request.user
        specific_students_data = serializer.validated_data.get('available_to_specific_students') # Può essere None o []

        if specific_students_data is not None: # Se il campo è stato fornito nell'update
            teacher_student_ids = set(user.students.values_list('id', flat=True))
            for student in specific_students_data:
                if student.id not in teacher_student_ids:
                    raise serializers.ValidationError(f"Lo studente {student.id} non appartiene a questo docente.")

        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """ Sovrascrive destroy per gestire ProtectedError. """
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except models.ProtectedError:
            logger.warning(f"Tentativo fallito di eliminare la ricompensa {instance.id} ('{instance.name}') perché protetta (probabilmente acquistata).")
            return Response(
                {"detail": "Impossibile eliminare questa ricompensa perché è stata acquistata."},
                status=status.HTTP_409_CONFLICT
            )


# --- ViewSet specifici per Studenti ---

class StudentShopViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint ReadOnly per lo Studente per visualizzare le ricompense disponibili.
    """
    serializer_class = RewardSerializer
    permission_classes = [IsStudentAuthenticated] # Solo Studenti autenticati

    def get_queryset(self):
        """
        Returns the queryset of rewards available to the authenticated student.
        Filters rewards based on the student's teacher, reward active status,
        and availability rules (all students or specific student).
        """
        # request.student è impostato da StudentJWTAuthentication
        student = self.request.student
        if not student:
             return Reward.objects.none()
        teacher = student.teacher

        # Ottieni gli ID delle ricompense già acquistate da questo studente
        purchased_reward_ids = RewardPurchase.objects.filter(student=student).values_list('reward_id', flat=True)

        # Filtra le ricompense attive del docente dello studente
        return Reward.objects.filter(
            teacher=teacher,
            is_active=True
        ).filter(
            # O disponibili a tutti O disponibili specificamente a questo studente
            models.Q(availability_type=Reward.AvailabilityType.ALL_STUDENTS) |
            models.Q(availability_type=Reward.AvailabilityType.SPECIFIC_STUDENTS, available_to_specific_students=student)
        ).exclude(
            # Escludi le ricompense già acquistate
            id__in=purchased_reward_ids
        ).distinct()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsStudent]) # Solo Studenti
    def purchase(self, request, pk=None):
        """
        Allows the authenticated student to purchase a specific reward.

        Checks for availability, active status, and sufficient points before proceeding.
        Uses an atomic transaction to subtract points and create the RewardPurchase record.
        """
        reward = self.get_object() # Ottiene la ricompensa specifica dall'URL (pk)
        student = request.student # Ottiene lo studente da StudentJWTAuthentication

        try:
            wallet = student.wallet # Accede al wallet tramite la relazione
        except Wallet.DoesNotExist:
             # Questo non dovrebbe accadere se ogni studente ha un wallet (creato da segnale?)
             return Response({'detail': 'Portafoglio studente non trovato.'}, status=status.HTTP_404_NOT_FOUND)

        # Verifica se la ricompensa è effettivamente disponibile per questo studente
        if not self.get_queryset().filter(pk=reward.pk).exists():
             return Response({'detail': 'Ricompensa non disponibile per questo studente.'}, status=status.HTTP_403_FORBIDDEN)

        # Verifica se la ricompensa è attiva
        if not reward.is_active:
             return Response({'detail': 'Ricompensa non più attiva.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica punti sufficienti e scala i punti (con transazione atomica)
        try:
            with transaction.atomic():
                # Ricarica il wallet con select_for_update per lock sulla riga
                wallet = Wallet.objects.select_for_update().get(student=student)
                wallet.subtract_points(reward.cost_points, f"Acquisto ricompensa: {reward.name}")

                # Crea il record di acquisto
                purchase = RewardPurchase.objects.create(
                    student=student,
                    reward=reward,
                    points_spent=reward.cost_points,
                    # Status di default è PURCHASED
                )
            serializer = RewardPurchaseSerializer(purchase)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e: # Errore da subtract_points (es. punti insufficienti)
            # Questo è un errore "atteso" (es. fondi insufficienti), quindi potremmo loggarlo come warning o info.
            logger.info(f"Errore di validazione durante l'acquisto della ricompensa {reward.id} da parte dello studente {student.id}: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Questo è un errore inatteso, logghiamolo come exception.
            logger.exception(f"Errore imprevisto durante l'acquisto della ricompensa {reward.id} da parte dello studente {student.id}")
            return Response({'detail': 'Errore durante l\'acquisto.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """ Endpoint ReadOnly per lo Studente per vedere il proprio wallet e transazioni. """
    serializer_class = WalletSerializer
    permission_classes = [IsStudentAuthenticated] # Solo Studenti autenticati

    def get_queryset(self):
        """ Returns the Wallet belonging to the authenticated student. """
        # request.student è impostato da StudentJWTAuthentication
        student = self.request.student
        if not student:
             return Wallet.objects.none()
        return Wallet.objects.filter(student=student)

    @action(detail=True, methods=['get']) # pk here is the student_id (as it's the Wallet's PK)
    def transactions(self, request, pk=None):
        """ Lists the point transactions for the student's wallet. """
        wallet = self.get_object()
        transactions = wallet.transactions.all() # Usa related_name
        page = self.paginate_queryset(transactions) # Applica paginazione se configurata
        if page is not None:
            serializer = PointTransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PointTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class StudentPurchasesViewSet(viewsets.ReadOnlyModelViewSet):
    """ Endpoint ReadOnly per lo Studente per vedere i propri acquisti. """
    serializer_class = RewardPurchaseSerializer
    permission_classes = [IsStudentAuthenticated] # Solo Studenti autenticati

    def get_queryset(self):
        # request.student è impostato da StudentJWTAuthentication
        student = self.request.student
        if not student:
             return RewardPurchase.objects.none()
        return RewardPurchase.objects.filter(student=student).select_related('reward')


# --- ViewSet specifici per Docenti ---

class TeacherRewardDeliveryViewSet(viewsets.GenericViewSet):
    """ Endpoint per Docenti per gestire la consegna delle ricompense reali. """
    serializer_class = RewardPurchaseSerializer # Usato per output
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser, IsTeacherOfStudentForPurchase]

    def get_queryset(self):
        """ Filtra gli acquisti pendenti dei propri studenti. """
        user = self.request.user
        return RewardPurchase.objects.filter(
            student__teacher=user, # Filtra per studenti del docente
            # Rimosso filtro per tipo: mostra tutti i tipi in attesa
            status=RewardPurchase.PurchaseStatus.PURCHASED # Solo quelle non ancora consegnate
        ).select_related('student', 'reward')

    @action(detail=False, methods=['get'], url_path='pending-delivery', permission_classes=[permissions.IsAuthenticated, IsTeacherUser]) # Già aggiunto
    def list_pending(self, request):
        """ Lista gli acquisti in attesa di consegna. """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='mark-delivered', permission_classes=[permissions.IsAuthenticated, IsTeacherUser, IsTeacherOfStudentForPurchase]) # Aggiunto IsTeacherUser
    def mark_delivered(self, request, pk=None):
        """ Segna un acquisto come consegnato. """
        # Modificato: Recupera l'acquisto senza filtrare per stato nel queryset principale
        # Il permesso IsTeacherOfStudentForPurchase verifica l'appartenenza
        purchase = get_object_or_404(
            RewardPurchase.objects.filter(
                student__teacher=request.user
                # Rimosso filtro reward__type: permette di marcare qualsiasi tipo
            ),
            pk=pk
        )

        # AGGIUNTO: Controlla lo stato PRIMA di procedere
        if purchase.status != RewardPurchase.PurchaseStatus.PURCHASED:
            return Response(
                {'detail': 'Questo acquisto non è in attesa di consegna (potrebbe essere già consegnato o cancellato).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verifica permessi a livello oggetto (già fatto da get_queryset + get_object_or_404)
        # self.check_object_permissions(request, purchase) # Non strettamente necessario qui

        delivery_notes = request.data.get('delivery_notes', '')

        purchase.status = RewardPurchase.PurchaseStatus.DELIVERED
        purchase.delivered_by = request.user
        purchase.delivered_at = timezone.now() # Importare timezone da django.utils
        purchase.delivery_notes = delivery_notes
        purchase.save()

        serializer = self.get_serializer(purchase)
        return Response(serializer.data)

# Nota: Manca l'import di timezone. Aggiungerlo all'inizio del file:
# from django.utils import timezone

# --- View Specifiche per Dashboard Studente ---

class StudentWalletInfoView(generics.RetrieveAPIView):
    """
    Restituisce le informazioni aggregate del wallet per la dashboard studente:
    punti correnti e transazioni recenti.
    """
    serializer_class = StudentWalletDashboardSerializer
    permission_classes = [IsStudentAuthenticated] # Solo studenti autenticati

    def get_object(self):
        """
        Recupera il wallet dello studente autenticato.
        La creazione del wallet dovrebbe essere gestita altrove (es. segnali).
        """
        student = self.request.user # request.user è lo studente
        try:
            # Accedi direttamente tramite la relazione one-to-one inversa
            wallet = student.wallet
            return wallet
        except Wallet.DoesNotExist:
            # Se il wallet non esiste per qualche motivo, solleva 404
            # Logga questo evento perché non dovrebbe accadere in teoria
            logger.error(f"Wallet non trovato per lo studente {student.id} ({student.student_code})")
            raise Http404("Wallet non trovato.")

    def retrieve(self, request, *args, **kwargs):
        """
        Costruisce l'oggetto dati aggregato e lo passa al serializer.
        """
        wallet = self.get_object()
        # Recupera le ultime N transazioni (es. le ultime 5)
        recent_transactions = wallet.transactions.order_by('-timestamp')[:5]

        # Costruisci l'oggetto dati per il serializer
        data = {
            'current_points': wallet.current_points,
            'recent_transactions': recent_transactions
        }

        serializer = self.get_serializer(data)
        return Response(serializer.data)
