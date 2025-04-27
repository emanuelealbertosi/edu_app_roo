import logging
from django.shortcuts import get_object_or_404
from django.db import transaction, models, IntegrityError # Aggiunto IntegrityError
from django.db.models import ProtectedError
from django.http import Http404
from django.utils import timezone
from rest_framework import viewsets, status, permissions, serializers, generics, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound

from apps.users.permissions import IsAdminUser, IsTeacherUser, IsStudent, IsStudentAuthenticated
from apps.users.models import User, Student, UserRole # Import User
from apps.student_groups.models import StudentGroup # Importa StudentGroup
from .models import (
    Wallet, PointTransaction, RewardTemplate, Reward, RewardPurchase,
    Badge, EarnedBadge, RewardAvailability # Importa RewardAvailability
)
from .serializers import (
    WalletSerializer, PointTransactionSerializer, RewardTemplateSerializer,
    RewardSerializer, RewardPurchaseSerializer, StudentWalletDashboardSerializer,
    BadgeSerializer, EarnedBadgeSerializer,
    # Nuovi serializer per disponibilità
    RewardAvailabilitySerializer, MakeRewardAvailableSerializer
)
from .permissions import (
    IsAdminOrReadOnly, IsRewardTemplateOwnerOrAdmin, IsRewardOwnerOrAdmin,
    IsStudentOwnerForPurchase, IsTeacherOfStudentForPurchase
)
# Importa o definisci RevokeAssignmentSerializer
try:
    from apps.education.views import QuizViewSet as EducationQuizViewSet # Alias per evitare conflitti
    RevokeAssignmentSerializer = EducationQuizViewSet.RevokeAssignmentSerializer
except (ImportError, AttributeError):
    # Fallback: definisci un serializer di revoca qui se non importabile
    class RevokeAssignmentSerializer(serializers.Serializer):
        assignment_id = serializers.IntegerField(required=True, help_text="ID della disponibilità/assegnazione da revocare.")


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
    - Docente: CRUD completo sulle proprie ricompense, gestione disponibilità.
    - Admin: Lettura di tutte le ricompense (per supervisione).
    """
    serializer_class = RewardSerializer
    permission_classes = [permissions.IsAuthenticated] # Permessi specifici per azione

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
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'make_available', 'revoke_availability']:
            # Solo il proprietario (Docente) o Admin possono modificare/gestire disponibilità
            permission_classes = [permissions.IsAuthenticated, IsRewardOwnerOrAdmin]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsTeacherUser]
        else: # list
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_context(self):
        """ Aggiunge la request al contesto per usarla in serializer.validate(). """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        """ Sets the teacher automatically. """
        user = self.request.user
        if not user.is_teacher:
             raise serializers.ValidationError("Solo i Docenti possono creare ricompense.")
        serializer.save(teacher=user)

    def perform_update(self, serializer):
        # La validazione ownership è gestita da IsRewardOwnerOrAdmin
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """ Sovrascrive destroy per gestire ProtectedError. """
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            logger.warning(f"Tentativo fallito di eliminare la ricompensa {instance.id} ('{instance.name}') perché protetta (probabilmente acquistata).")
            return Response(
                {"detail": "Impossibile eliminare questa ricompensa perché è stata acquistata."},
                status=status.HTTP_409_CONFLICT
            )

    # --- Azioni per Disponibilità ---

    @action(detail=True, methods=['post'], url_path='make-available', permission_classes=[permissions.IsAuthenticated, IsRewardOwnerOrAdmin])
    def make_available(self, request, pk=None):
        """
        Rende questa Ricompensa (pk) disponibile a uno Studente o a un Gruppo.
        Richiede 'student_id' o 'group_id' nel corpo della richiesta.
        """
        reward = self.get_object() # Verifica ownership e recupera ricompensa
        serializer = MakeRewardAvailableSerializer(data=request.data, context={'request': request, 'reward': reward})

        if serializer.is_valid():
            try:
                availability = serializer.save() # .save() chiama .create()
                # Usa RewardAvailabilitySerializer per la risposta (fatto da to_representation)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                logger.warning(f"Errore validazione disponibilità ricompensa {pk} da utente {request.user.id}: {e.detail}")
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            except IntegrityError as e:
                 logger.error(f"Errore integrità disponibilità ricompensa {pk} da utente {request.user.id}: {e}", exc_info=True)
                 return Response({'detail': 'Errore durante il salvataggio della disponibilità.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                 logger.error(f"Errore imprevisto disponibilità ricompensa {pk} da utente {request.user.id}: {e}", exc_info=True)
                 return Response({'detail': 'Errore interno durante la gestione della disponibilità.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Errore dati richiesta disponibilità ricompensa {pk} da utente {request.user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='revoke-availability', permission_classes=[permissions.IsAuthenticated, IsRewardOwnerOrAdmin])
    def revoke_availability(self, request, pk=None):
        """
        Revoca una specifica disponibilità (identificata da 'assignment_id') per questa Ricompensa (pk).
        """
        reward = self.get_object() # Verifica ownership ricompensa
        serializer = RevokeAssignmentSerializer(data=request.data) # Riusa serializer

        if serializer.is_valid():
            availability_id = serializer.validated_data['assignment_id']
            try:
                availability = get_object_or_404(RewardAvailability, id=availability_id, reward=reward)
                availability.delete()
                logger.info(f"Disponibilità Ricompensa ID {availability_id} (Ricompensa ID {pk}) revocata da utente {request.user.id}")
                return Response(status=status.HTTP_204_NO_CONTENT)
            except RewardAvailability.DoesNotExist:
                 logger.warning(f"Tentativo revoca disponibilità ricompensa non trovata ID {availability_id} per ricompensa {pk} da utente {request.user.id}")
                 return Response({'detail': 'Disponibilità non trovata per questa ricompensa.'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                 logger.error(f"Errore imprevisto revoca disponibilità ricompensa {availability_id} (Ricompensa {pk}) da utente {request.user.id}: {e}", exc_info=True)
                 return Response({'detail': 'Errore interno durante la revoca.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Errore dati richiesta revoca disponibilità ricompensa {pk} da utente {request.user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- ViewSet specifici per Studenti ---

class StudentShopViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint ReadOnly per lo Studente per visualizzare le ricompense disponibili.
    """
    serializer_class = RewardSerializer
    permission_classes = [IsStudentAuthenticated]

    def get_queryset(self):
        """
        Restituisce il queryset delle ricompense attive disponibili
        per lo studente autenticato (direttamente o tramite gruppo).
        """
        student = self.request.user # IsStudentAuthenticated assicura che sia uno studente
        # Verifica se l'utente ha la relazione corretta usando il related_name='group_memberships'
        if not hasattr(student, 'group_memberships'):
             logger.error(f"L'utente {student.id} ({student}) non sembra avere la relazione 'group_memberships'.")
             return Reward.objects.none()

        # Ottieni gli ID dei gruppi attivi a cui lo studente appartiene usando il related_name corretto
        student_group_ids = student.group_memberships.filter(group__is_active=True).values_list('group_id', flat=True) # Considera solo gruppi attivi

        # Trova gli ID delle ricompense disponibili per questo studente o i suoi gruppi
        available_reward_ids = RewardAvailability.objects.filter(
            models.Q(student=student) | models.Q(group_id__in=student_group_ids)
        ).values_list('reward_id', flat=True).distinct()

        # Ottieni gli ID delle ricompense già acquistate da questo studente
        purchased_reward_ids = RewardPurchase.objects.filter(student=student).values_list('reward_id', flat=True)

        # Filtra le ricompense attive che sono nella lista degli ID disponibili
        # E escludi quelle già acquistate dallo studente
        return Reward.objects.filter(
            id__in=available_reward_ids,
            is_active=True
        ).exclude(
            id__in=purchased_reward_ids # Escludi le ricompense già acquistate
        ).select_related('teacher') # Ottimizza

    @action(detail=True, methods=['post']) # Rimosso IsStudent dai permessi, già coperto da permission_classes del ViewSet
    def purchase(self, request, pk=None):
        """
        Permette allo studente autenticato di acquistare una ricompensa specifica.
        """
        reward = get_object_or_404(Reward, pk=pk, is_active=True) # Assicura che la ricompensa esista e sia attiva
        student = request.user # Sappiamo che è uno studente grazie a IsStudentAuthenticated

        # Verifica se la ricompensa è effettivamente disponibile per lo studente (usando la stessa logica di get_queryset)
        if not self.get_queryset().filter(pk=reward.pk).exists():
             logger.warning(f"Studente {student.id} ha tentato acquisto ricompensa non disponibile ID {pk}")
             return Response({'detail': 'Ricompensa non disponibile per te.'}, status=status.HTTP_403_FORBIDDEN)

        # Verifica se già acquistata (opzionale, potrebbe essere gestito da logica diversa)
        if RewardPurchase.objects.filter(student=student, reward=reward).exists():
             return Response({'detail': 'Hai già acquistato questa ricompensa.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wallet = student.wallet
        except Wallet.DoesNotExist:
             logger.error(f"Wallet non trovato per lo studente {student.id}")
             return Response({'detail': 'Portafoglio studente non trovato.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            with transaction.atomic():
                # Lock sul wallet per evitare race conditions
                wallet = Wallet.objects.select_for_update().get(student=student)
                wallet.subtract_points(reward.cost_points, f"Acquisto ricompensa: {reward.name}")

                purchase = RewardPurchase.objects.create(
                    student=student,
                    reward=reward,
                    points_spent=reward.cost_points,
                )
            serializer = RewardPurchaseSerializer(purchase)
            logger.info(f"Studente {student.id} ha acquistato ricompensa {reward.id} per {reward.cost_points} punti.")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e: # Errore da subtract_points (es. punti insufficienti)
            logger.info(f"Acquisto fallito per studente {student.id}, ricompensa {reward.id}: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Errore imprevisto durante acquisto ricompensa {reward.id} da studente {student.id}")
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
        student = self.request.user # IsStudentAuthenticated assicura che sia uno studente
        return EarnedBadge.objects.filter(student=student).select_related('badge').prefetch_related('badge') # Prefetch badge

    def get_serializer_context(self):
        """ Assicura che il contesto della richiesta sia passato al serializer. """
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
        student = self.request.user
        return Wallet.objects.filter(student=student)

    @action(detail=False, methods=['get']) # Cambiato detail=False, opera sul wallet dello studente loggato
    def transactions(self, request):
        """ Lists the point transactions for the student's wallet. """
        student = request.user
        try:
            wallet = student.wallet
            transactions = wallet.transactions.all().order_by('-timestamp') # Ordina per più recente
            page = self.paginate_queryset(transactions)
            if page is not None:
                serializer = PointTransactionSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = PointTransactionSerializer(transactions, many=True)
            return Response(serializer.data)
        except Wallet.DoesNotExist:
             logger.error(f"Wallet non trovato per studente {student.id} in transactions action.")
             raise Http404("Wallet non trovato.")


class StudentPurchasesViewSet(viewsets.ReadOnlyModelViewSet):
    """ Endpoint ReadOnly per lo Studente per vedere i propri acquisti. """
    serializer_class = RewardPurchaseSerializer
    permission_classes = [IsStudentAuthenticated]

    def get_queryset(self):
        student = self.request.user
        return RewardPurchase.objects.filter(student=student).select_related('reward__teacher') # Include info ricompensa e docente


# --- ViewSet specifici per Docenti ---

class TeacherRewardDeliveryViewSet(viewsets.GenericViewSet):
    """ Endpoint per Docenti per gestire la consegna delle ricompense reali. """
    serializer_class = RewardPurchaseSerializer
    # Permessi: deve essere docente E il docente dello studente che ha fatto l'acquisto
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser]

    def get_queryset(self):
        """ Filtra gli acquisti pendenti dei propri studenti. """
        user = self.request.user
        # Assicurati che l'utente sia un docente prima di filtrare
        if not isinstance(user, User) or not user.is_teacher:
             return RewardPurchase.objects.none()
        return RewardPurchase.objects.filter(
            reward__teacher=user, # Filtra per ricompense create dal docente
            status=RewardPurchase.PurchaseStatus.PURCHASED
        ).select_related('student', 'reward')

    @action(detail=False, methods=['get'], url_path='pending-delivery')
    def list_pending(self, request):
        """ Lista gli acquisti in attesa di consegna per questo docente. """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='mark-delivered')
    def mark_delivered(self, request, pk=None):
        """ Segna un acquisto (pk) come consegnato. """
        user = request.user
        # Recupera l'acquisto assicurandosi che appartenga a una ricompensa del docente
        purchase = get_object_or_404(
            RewardPurchase.objects.select_related('reward'), # Seleziona reward per controllo teacher
            pk=pk,
            reward__teacher=user # Filtra per ricompense del docente loggato
        )

        if purchase.status != RewardPurchase.PurchaseStatus.PURCHASED:
            return Response(
                {'detail': 'Questo acquisto non è in attesa di consegna.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        delivery_notes = request.data.get('delivery_notes', '')

        purchase.status = RewardPurchase.PurchaseStatus.DELIVERED
        purchase.delivered_by = user
        purchase.delivered_at = timezone.now()
        purchase.delivery_notes = delivery_notes
        purchase.save()

        serializer = self.get_serializer(purchase)
        logger.info(f"Docente {user.id} ha marcato acquisto {pk} come consegnato.")
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
        """ Recupera il wallet dello studente autenticato. """
        student = self.request.user
        try:
            # Assicurati che il wallet esista, crealo se necessario (potrebbe essere fatto al momento della creazione dello studente)
            wallet, created = Wallet.objects.get_or_create(student=student)
            if created:
                 logger.info(f"Creato wallet per lo studente {student.id}")
            return wallet
        except AttributeError: # Se request.user non è uno Studente o manca la relazione
             logger.error(f"Impossibile recuperare/creare wallet per l'utente {student.id}, non è uno studente valido?")
             raise Http404("Wallet non trovato.")
        except Exception as e:
             logger.exception(f"Errore recupero/creazione wallet per studente {student.id}")
             raise Http404("Errore accesso al wallet.")


    def retrieve(self, request, *args, **kwargs):
        """ Costruisce l'oggetto dati aggregato e lo passa al serializer. """
        wallet = self.get_object()
        # Limita il numero di transazioni per performance
        recent_transactions = wallet.transactions.order_by('-timestamp')[:10] # Mostra le ultime 10

        data = {
            'current_points': wallet.current_points,
            'recent_transactions': recent_transactions
        }

        serializer = self.get_serializer(data)
        return Response(serializer.data)
