import logging
from django.shortcuts import get_object_or_404
from django.db import transaction, models
from django.db.models import ProtectedError
from django.http import Http404
from django.utils import timezone
from rest_framework import viewsets, status, permissions, serializers, generics, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound

from apps.users.permissions import IsAdminUser, IsTeacherUser, IsStudent, IsStudentAuthenticated
from apps.users.models import User, Student, UserRole # Import User
from .models import (
    Wallet, PointTransaction, RewardTemplate, Reward, RewardPurchase,
    Badge, EarnedBadge # Importa modelli Badge
)
from .serializers import (
    WalletSerializer, PointTransactionSerializer, RewardTemplateSerializer,
    RewardSerializer, RewardPurchaseSerializer, StudentWalletDashboardSerializer,
    BadgeSerializer, EarnedBadgeSerializer # Importa serializer Badge
)
from .permissions import (
    IsAdminOrReadOnly, IsRewardTemplateOwnerOrAdmin, IsRewardOwnerOrAdmin,
    IsStudentOwnerForPurchase, IsTeacherOfStudentForPurchase
)

logger = logging.getLogger(__name__)


class RewardTemplateViewSet(viewsets.ModelViewSet):
    """
    API endpoint per i Reward Templates.
    - Admin: CRUD completo su template globali. Lettura template locali.
    - Docente: CRUD completo sui propri template locali. Lettura template globali.
    """
    serializer_class = RewardTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsRewardTemplateOwnerOrAdmin]

    def get_queryset(self):
        """
        Restricts the queryset based on the user role.
        - Admins see all templates (global and local).
        - Teachers see their own local templates and all global templates.
        """
        user = self.request.user
        if isinstance(user, User) and user.is_admin:
            return RewardTemplate.objects.all()
        elif isinstance(user, User) and user.is_teacher:
            return RewardTemplate.objects.filter(
                models.Q(scope=RewardTemplate.RewardScope.GLOBAL) | models.Q(creator=user, scope=RewardTemplate.RewardScope.LOCAL)
            )
        return RewardTemplate.objects.none()

    def perform_create(self, serializer):
        """
        Sets the creator and scope automatically based on the user role.
        - Admins create GLOBAL templates.
        - Teachers create LOCAL templates.
        """
        user = self.request.user
        scope = RewardTemplate.RewardScope.LOCAL
        if isinstance(user, User):
            if user.is_admin:
                scope = RewardTemplate.RewardScope.GLOBAL
            elif not user.is_teacher:
                 raise serializers.ValidationError("Solo Admin o Docenti possono creare template.")
        else:
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
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Restricts the queryset based on the user role for list actions.
        """
        user = self.request.user
        if user.is_admin:
            return Reward.objects.all().select_related('teacher')
        elif user.is_teacher:
            return Reward.objects.filter(teacher=user).select_related('teacher')
        return Reward.objects.none()

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsRewardOwnerOrAdmin]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsTeacherUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer(self, *args, **kwargs):
        """
        Sovrascrive get_serializer per filtrare il queryset del campo
        specific_student_ids basandosi sul docente autenticato.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()

        # Filtra il queryset solo se l'utente è un docente
        user = self.request.user
        if isinstance(user, User) and user.is_teacher:
            # Non è più necessario passare il queryset qui,
            # la validazione avverrà nel serializer.validate()
            pass

        return serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        """ Aggiunge la request al contesto per usarla in serializer.validate(). """
        context = super().get_serializer_context()
        context['request'] = self.request # Assicura che la request sia nel contesto
        return context

    def perform_create(self, serializer):
        """
        Sets the teacher automatically and validates specific student availability.
        """
        user = self.request.user
        if not user.is_teacher:
             raise serializers.ValidationError("Solo i Docenti possono creare ricompense.")
# La validazione che gli studenti appartengano al docente è ora gestita
# dal queryset filtrato passato al PrimaryKeyRelatedField nel serializer.
# Non è più necessaria la validazione esplicita qui.

        serializer.save(teacher=user)

    def perform_update(self, serializer):
        """
        Validates specific student availability during updates.
        """
        user = self.request.user
        # La validazione che gli studenti appartengano al docente è ora gestita
        # dal queryset filtrato passato al PrimaryKeyRelatedField nel serializer.
        # Non è più necessaria la validazione esplicita qui.
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """ Sovrascrive destroy per gestire ProtectedError. """
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError: # Corretto: Usare ProtectedError importato
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
    permission_classes = [IsStudentAuthenticated]

    def get_queryset(self):
        """
        Returns the queryset of rewards available to the authenticated student.
        """
        student = self.request.student
        if not student:
             return Reward.objects.none()
        teacher = student.teacher

        purchased_reward_ids = RewardPurchase.objects.filter(student=student).values_list('reward_id', flat=True)

        return Reward.objects.filter(
            teacher=teacher,
            is_active=True
        ).filter(
            models.Q(availability_type=Reward.AvailabilityType.ALL_STUDENTS) |
            models.Q(availability_type=Reward.AvailabilityType.SPECIFIC_STUDENTS, available_to_specific_students=student)
        ).exclude(
            id__in=purchased_reward_ids
        ).distinct()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsStudent])
    def purchase(self, request, pk=None):
        """
        Allows the authenticated student to purchase a specific reward.
        """
        reward = self.get_object()
        student = request.student

        try:
            wallet = student.wallet
        except Wallet.DoesNotExist:
             return Response({'detail': 'Portafoglio studente non trovato.'}, status=status.HTTP_404_NOT_FOUND)

        if not self.get_queryset().filter(pk=reward.pk).exists():
             return Response({'detail': 'Ricompensa non disponibile per questo studente.'}, status=status.HTTP_403_FORBIDDEN)

        if not reward.is_active:
             return Response({'detail': 'Ricompensa non più attiva.'}, status=status.HTTP_400_BAD_REQUEST)

        try: # Blocco try per la transazione atomica
            with transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(student=student)
                wallet.subtract_points(reward.cost_points, f"Acquisto ricompensa: {reward.name}")

                purchase = RewardPurchase.objects.create(
                    student=student,
                    reward=reward,
                    points_spent=reward.cost_points,
                )
            serializer = RewardPurchaseSerializer(purchase)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e: # Errore da subtract_points (es. punti insufficienti)
            logger.info(f"Errore di validazione durante l'acquisto della ricompensa {reward.id} da parte dello studente {student.id}: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Errore imprevisto durante l'acquisto della ricompensa {reward.id} da parte dello studente {student.id}")
            return Response({'detail': 'Errore durante l\'acquisto.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- ViewSets per Gamification (Badge) ---

class BadgeViewSet(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet):
    """
    ViewSet per visualizzare le definizioni dei Badge disponibili.
    Accessibile in sola lettura da tutti gli utenti autenticati.
    """
    queryset = Badge.objects.filter(is_active=True)
    serializer_class = BadgeSerializer
    permission_classes = [permissions.IsAuthenticated]


class StudentEarnedBadgeViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    """
    ViewSet per visualizzare i Badge guadagnati dallo studente autenticato.
    Accessibile in sola lettura solo dagli studenti.
    """
    serializer_class = EarnedBadgeSerializer
    permission_classes = [IsStudentAuthenticated]

    def get_queryset(self):
        """ Filtra i badge guadagnati per lo studente corrente. """
        student = self.request.student
        if not student:
             logger.warning(f"Utente non studente ha tentato accesso a EarnedBadge.")
             return EarnedBadge.objects.none()
        # Aggiunto prefetch_related per ottimizzare l'accesso all'immagine del badge
        return EarnedBadge.objects.filter(student=student).select_related('badge').prefetch_related('badge')

    def get_serializer_context(self):
        """
        Assicura che il contesto della richiesta sia passato al serializer.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# --- Altri ViewSet Studente ---

class StudentWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """ Endpoint ReadOnly per lo Studente per vedere il proprio wallet e transazioni. """
    serializer_class = WalletSerializer
    permission_classes = [IsStudentAuthenticated]

    def get_queryset(self):
        """ Returns the Wallet belonging to the authenticated student. """
        student = self.request.student
        if not student:
             return Wallet.objects.none()
        return Wallet.objects.filter(student=student)

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """ Lists the point transactions for the student's wallet. """
        wallet = self.get_object()
        transactions = wallet.transactions.all()
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = PointTransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PointTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class StudentPurchasesViewSet(viewsets.ReadOnlyModelViewSet):
    """ Endpoint ReadOnly per lo Studente per vedere i propri acquisti. """
    serializer_class = RewardPurchaseSerializer
    permission_classes = [IsStudentAuthenticated]

    def get_queryset(self):
        student = self.request.student
        if not student:
             return RewardPurchase.objects.none()
        return RewardPurchase.objects.filter(student=student).select_related('reward')


# --- ViewSet specifici per Docenti ---

class TeacherRewardDeliveryViewSet(viewsets.GenericViewSet):
    """ Endpoint per Docenti per gestire la consegna delle ricompense reali. """
    serializer_class = RewardPurchaseSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser, IsTeacherOfStudentForPurchase]

    def get_queryset(self):
        """ Filtra gli acquisti pendenti dei propri studenti. """
        user = self.request.user
        return RewardPurchase.objects.filter(
            student__teacher=user,
            status=RewardPurchase.PurchaseStatus.PURCHASED
        ).select_related('student', 'reward')

    @action(detail=False, methods=['get'], url_path='pending-delivery', permission_classes=[permissions.IsAuthenticated, IsTeacherUser])
    def list_pending(self, request):
        """ Lista gli acquisti in attesa di consegna. """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='mark-delivered', permission_classes=[permissions.IsAuthenticated, IsTeacherUser, IsTeacherOfStudentForPurchase])
    def mark_delivered(self, request, pk=None):
        """ Segna un acquisto come consegnato. """
        purchase = get_object_or_404(
            RewardPurchase.objects.filter(
                student__teacher=request.user
            ),
            pk=pk
        )

        if purchase.status != RewardPurchase.PurchaseStatus.PURCHASED:
            return Response(
                {'detail': 'Questo acquisto non è in attesa di consegna (potrebbe essere già consegnato o cancellato).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        delivery_notes = request.data.get('delivery_notes', '')

        purchase.status = RewardPurchase.PurchaseStatus.DELIVERED
        purchase.delivered_by = request.user
        purchase.delivered_at = timezone.now()
        purchase.delivery_notes = delivery_notes
        purchase.save()

        serializer = self.get_serializer(purchase)
        return Response(serializer.data)


# --- View Specifiche per Dashboard Studente ---

class StudentWalletInfoView(generics.RetrieveAPIView):
    """
    Restituisce le informazioni aggregate del wallet per la dashboard studente:
    punti correnti e transazioni recenti.
    """
    serializer_class = StudentWalletDashboardSerializer
    permission_classes = [IsStudentAuthenticated]

    def get_object(self):
        """
        Recupera il wallet dello studente autenticato.
        """
        student = self.request.user
        try:
            wallet = student.wallet
            return wallet
        except Wallet.DoesNotExist:
            logger.error(f"Wallet non trovato per lo studente {student.id} ({student.student_code})")
            raise Http404("Wallet non trovato.")

    def retrieve(self, request, *args, **kwargs):
        """
        Costruisce l'oggetto dati aggregato e lo passa al serializer.
        """
        wallet = self.get_object()
        recent_transactions = wallet.transactions.order_by('-timestamp')[:5]

        data = {
            'current_points': wallet.current_points,
            'recent_transactions': recent_transactions
        }

        serializer = self.get_serializer(data)
        return Response(serializer.data)
