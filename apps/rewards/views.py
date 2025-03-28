from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction, models # Add models
from django.shortcuts import get_object_or_404
from django.utils import timezone # Add this import

from .models import (
    Wallet, PointTransaction, RewardTemplate, Reward, RewardPurchase
)
from .serializers import (
    WalletSerializer, PointTransactionSerializer, RewardTemplateSerializer,
    RewardSerializer, RewardPurchaseSerializer
)
from .permissions import (
    IsAdminOrReadOnly, IsRewardTemplateOwnerOrAdmin, IsRewardOwner,
    IsStudentOwnerForPurchase, IsTeacherOfStudentForPurchase
)
# Importa permessi da users, incluso IsStudentAuthenticated
from apps.users.permissions import IsAdminUser, IsTeacherUser, IsStudent, IsStudentAuthenticated
from apps.users.models import UserRole, Student # Import modelli utente


class RewardTemplateViewSet(viewsets.ModelViewSet):
    """
    API endpoint per i Reward Templates.
    - Admin: CRUD completo su template globali. Lettura template locali.
    - Docente: CRUD completo sui propri template locali. Lettura template globali.
    """
    serializer_class = RewardTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsRewardTemplateOwnerOrAdmin] # IsAdminOrReadOnly gestito implicitamente

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            # Admin vede tutti i template (globali e locali)
            return RewardTemplate.objects.all()
        elif user.is_teacher:
            # Docente vede i propri locali + tutti i globali
            return RewardTemplate.objects.filter(
                models.Q(scope=RewardTemplate.RewardScope.GLOBAL) | models.Q(creator=user, scope=RewardTemplate.RewardScope.LOCAL)
            )
        return RewardTemplate.objects.none() # Nessun altro può vedere template

    def perform_create(self, serializer):
        user = self.request.user
        scope = RewardTemplate.RewardScope.LOCAL # Default per Docente
        if user.is_admin:
            # Admin può specificare lo scope nel payload, altrimenti default a GLOBAL?
            # Per semplicità, forziamo GLOBAL se creato da Admin.
            scope = RewardTemplate.RewardScope.GLOBAL
            # Potremmo aggiungere un controllo: se l'admin specifica scope=LOCAL, sollevare errore?
        elif not user.is_teacher:
             raise serializers.ValidationError("Solo Admin o Docenti possono creare template.")

        serializer.save(creator=user, scope=scope)


class RewardViewSet(viewsets.ModelViewSet):
    """
    API endpoint per le Reward specifiche.
    - Docente: CRUD completo sulle proprie ricompense.
    - Admin: Lettura di tutte le ricompense (per supervisione).
    - Studente: Lettura delle ricompense disponibili (gestito in endpoint separato 'shop').
    """
    serializer_class = RewardSerializer
    permission_classes = [permissions.IsAuthenticated, IsRewardOwner] # IsTeacherUser è implicito in IsRewardOwner per scrittura

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            # Admin vede tutte le ricompense
            return Reward.objects.all().select_related('teacher')
        elif user.is_teacher:
            # Docente vede solo le proprie ricompense
            return Reward.objects.filter(teacher=user).select_related('teacher')
        # Studenti vedono le ricompense disponibili tramite l'endpoint 'shop'
        return Reward.objects.none()

    def get_serializer_context(self):
        """ Aggiunge il docente al contesto per validazione studenti. """
        context = super().get_serializer_context()
        context['teacher'] = self.request.user
        return context

    def perform_create(self, serializer):
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
         # Simile a perform_create, validiamo gli studenti se vengono modificati
        user = self.request.user
        specific_students_data = serializer.validated_data.get('available_to_specific_students') # Può essere None o []

        if specific_students_data is not None: # Se il campo è stato fornito nell'update
            teacher_student_ids = set(user.students.values_list('id', flat=True))
            for student in specific_students_data:
                if student.id not in teacher_student_ids:
                    raise serializers.ValidationError(f"Lo studente {student.id} non appartiene a questo docente.")

        serializer.save()


# --- ViewSet specifici per Studenti ---

class StudentShopViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint ReadOnly per lo Studente per visualizzare le ricompense disponibili.
    """
    serializer_class = RewardSerializer
    permission_classes = [IsStudentAuthenticated] # Solo Studenti autenticati

    def get_queryset(self):
        # request.student è impostato da StudentJWTAuthentication
        student = self.request.student
        if not student:
             return Reward.objects.none()
        teacher = student.teacher

        # Filtra le ricompense attive del docente dello studente
        return Reward.objects.filter(
            teacher=teacher,
            is_active=True
        ).filter(
            # O disponibili a tutti O disponibili specificamente a questo studente
            models.Q(availability_type=Reward.AvailabilityType.ALL_STUDENTS) |
            models.Q(availability_type=Reward.AvailabilityType.SPECIFIC_STUDENTS, available_to_specific_students=student)
        ).distinct() # distinct() per evitare duplicati se uno studente è in M2M e anche ALL

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsStudent]) # Solo Studenti
    def purchase(self, request, pk=None):
        """ Azione custom per acquistare una ricompensa. """
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
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log dell'errore
            return Response({'detail': 'Errore durante l\'acquisto.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StudentWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """ Endpoint ReadOnly per lo Studente per vedere il proprio wallet e transazioni. """
    serializer_class = WalletSerializer
    permission_classes = [IsStudentAuthenticated] # Solo Studenti autenticati

    def get_queryset(self):
        # request.student è impostato da StudentJWTAuthentication
        student = self.request.student
        if not student:
             return Wallet.objects.none()
        return Wallet.objects.filter(student=student)

    @action(detail=True, methods=['get']) # pk qui è lo student_id (essendo la chiave del Wallet)
    def transactions(self, request, pk=None):
        """ Mostra le transazioni per questo wallet. """
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
            reward__type=RewardTemplate.RewardType.REAL_WORLD, # Solo ricompense reali
            status=RewardPurchase.PurchaseStatus.PURCHASED # Solo quelle non ancora consegnate
        ).select_related('student', 'reward')

    @action(detail=False, methods=['get'], url_path='pending-delivery')
    def list_pending(self, request):
        """ Lista gli acquisti in attesa di consegna. """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='mark-delivered')
    def mark_delivered(self, request, pk=None):
        """ Segna un acquisto come consegnato. """
        purchase = get_object_or_404(self.get_queryset(), pk=pk) # Assicura che sia pendente e del docente

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
