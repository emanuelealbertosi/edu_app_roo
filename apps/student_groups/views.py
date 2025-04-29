from rest_framework import generics, status, permissions, mixins, viewsets # Import generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import IntegrityError
import secrets
from django.conf import settings
from urllib.parse import urljoin, urlencode
from django.db.models import Q # Import Q for complex lookups

from .models import StudentGroup, StudentGroupMembership, GroupAccessRequest # Importa nuovi modelli
from apps.users.models import Student, UserRole # Importa UserRole
from .serializers import (
    StudentGroupSerializer,
    StudentGroupDetailSerializer,
    StudentGroupMembershipSerializer,
    GenerateTokenSerializer,
    AddStudentSerializer,
    GroupAccessRequestSerializer, # Importa nuovo serializer
    RespondGroupAccessRequestSerializer, # Importa nuovo serializer
)
from apps.users.serializers import StudentBasicSerializer # Importa il serializer per gli studenti
# Importa i permessi custom dal nuovo file
from .permissions import IsGroupOwner, HasGroupAccess, IsOwnerOrHasAccess, IsRequestingTeacher
from rest_framework.permissions import IsAuthenticated

# La classe IsGroupOwner è stata spostata in permissions.py

# ViewSet principale per i gruppi
class StudentGroupViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    """
    ViewSet per gestire i gruppi di studenti (CRUD).
    Accessibile solo ai docenti autenticati.
    """
    # queryset = StudentGroup.objects.all() # Rimosso, gestito da get_queryset
    # Impostiamo permessi di base, poi li specifichiamo per azione
    permission_classes = [IsAuthenticated]

    # Esplicita i metodi HTTP permessi (anche se dovrebbero essere default per ModelViewSet)
    # http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace'] # Lasciamo i default per ora

    # Explicitly define create to ensure it's recognized
    def create(self, request, *args, **kwargs):
        """Handles POST requests to create a new StudentGroup."""
        return super().create(request, *args, **kwargs)

    # Rimuoviamo l'override temporaneo, ora usiamo get_serializer_class
    # serializer_class = StudentGroupSerializer # Usiamo sempre il serializer base per ora

    def get_permissions(self):
        """ Imposta permessi specifici per azione. """
        if self.action in ['update', 'partial_update', 'destroy', 'generate_token', 'delete_token', 'list_access_requests', 'respond_access_request']:
            # Solo il proprietario può modificare, eliminare, gestire token e richieste
            return [IsAuthenticated(), IsGroupOwner()]
        elif self.action in ['retrieve', 'students', 'add_student', 'remove_student']:
            # Proprietario o chi ha accesso può vedere dettagli, membri e aggiungere/rimuovere membri
            return [IsAuthenticated(), IsOwnerOrHasAccess()]
        # Per 'list' e 'create', basta IsAuthenticated (la queryset e perform_create gestiscono il resto)
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'update' or self.action == 'partial_update':
            return StudentGroupDetailSerializer
        # Aggiungiamo azioni che usano serializer specifici
        if self.action == 'add_student':
            return AddStudentSerializer
        if self.action == 'generate_token':
            return GenerateTokenSerializer
        if self.action == 'list_access_requests':
            return GroupAccessRequestSerializer
        if self.action == 'respond_access_request':
            return RespondGroupAccessRequestSerializer
        if self.action == 'students':
            return StudentBasicSerializer
        # Default serializer
        return StudentGroupSerializer

    def get_queryset(self):
        """
        Filtra i gruppi per mostrare:
        1. Quelli di cui l'utente autenticato è proprietario (`owner`).
        2. Quelli a cui l'utente autenticato ha accesso approvato tramite `GroupAccessRequest`.
        """
        user = self.request.user
        if not user.is_authenticated:
            return StudentGroup.objects.none()

        # Gruppi di cui l'utente è proprietario
        owned_groups = Q(owner=user)

        # Gruppi a cui l'utente ha accesso approvato
        # Trova gli ID dei gruppi per cui esiste una richiesta approvata per l'utente
        approved_group_ids = GroupAccessRequest.objects.filter(
            requesting_teacher=user,
            status=GroupAccessRequest.AccessStatus.APPROVED
        ).values_list('group_id', flat=True)
        accessible_groups = Q(pk__in=approved_group_ids)

        # Combina le query e prefetch per ottimizzare
        return StudentGroup.objects.filter(owned_groups | accessible_groups).prefetch_related(
            'memberships__student', 'owner' # Aggiunto owner per efficienza
        ).distinct() # distinct() è importante quando si usano OR e join/prefetch

    def perform_create(self, serializer):
        """Associa automaticamente il docente autenticato come proprietario (`owner`)."""
        # Verifica se l'utente ha il permesso di creare gruppi pubblici se is_public=True
        is_public = serializer.validated_data.get('is_public', False)
        if is_public and not self.request.user.can_create_public_groups:
             raise permissions.PermissionDenied("Non hai il permesso di creare gruppi pubblici.")
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        """Controlla il permesso se si tenta di rendere pubblico un gruppo."""
        instance = serializer.instance
        is_public_new = serializer.validated_data.get('is_public', instance.is_public) # Considera il nuovo valore

        # Controlla solo se si sta cercando di impostare is_public a True
        # e l'utente non ha il permesso
        if is_public_new and not instance.is_public and not self.request.user.can_create_public_groups:
             raise permissions.PermissionDenied("Non hai il permesso di rendere pubblico questo gruppo.")
        serializer.save()

    # --- Azioni Custom ---
    # TODO: Rivedere i permessi per ogni azione custom (Owner o Accesso Approvato?)

    # Permessi specificati in get_permissions
    @action(detail=True, methods=['get'], url_path='students') # serializer_class gestito da get_serializer_class
    def students(self, request, pk=None):
        """
        Restituisce l'elenco degli studenti membri del gruppo.
        Accessibile a Owner e utenti con accesso approvato.
        """
        group = self.get_object() # Ottiene il gruppo corrente (gestisce 404 e permessi)
        # Ottieni gli studenti tramite la tabella di membership
        students = Student.objects.filter(group_memberships__group=group) # Usa il related_name corretto
        # Serializza gli studenti esplicitamente con StudentBasicSerializer
        serializer = StudentBasicSerializer(students, many=True, context={'request': request})
        return Response(serializer.data)

    # Permessi specificati in get_permissions
    @action(detail=True, methods=['post'], url_path='add-student') # serializer_class gestito da get_serializer_class
    def add_student(self, request, pk=None):
        """
        Aggiunge uno studente specificato nel body al gruppo.
        Accessibile a Owner e utenti con accesso approvato.
        """
        group = self.get_object() # get_object applica IsOwnerOrHasAccess
        # print(f"[DEBUG] add_student view - Request data received: {request.data}") # DEBUG REMOVED
        # Istanzia esplicitamente AddStudentSerializer per evitare confusione
        serializer = AddStudentSerializer(data=request.data, context={'request': request})
        try:
            # print("[DEBUG] Calling serializer.is_valid()...") # DEBUG REMOVED
            serializer.is_valid(raise_exception=True) # Qui avviene la validazione e l'errore 400
            # print("[DEBUG] Serializer is valid.") # DEBUG REMOVED
        except Exception as e:
            # print(f"[DEBUG] Validation failed: {e}") # DEBUG REMOVED
            raise e # Rilancia l'eccezione per mantenere il comportamento 400
        student_id = serializer.validated_data['student_id']

        # Rimosso controllo teacher=request.user perché Student.teacher è stato rimosso
        # La logica di permesso si basa sull'accesso al gruppo (verificato da get_object)
        student = get_object_or_404(Student, pk=student_id)

        # Crea la membership, gestendo potenziali duplicati
        try:
            membership, created = StudentGroupMembership.objects.get_or_create(
                group=group,
                student=student,
                defaults={'joined_at': timezone.now()} # Imposta joined_at solo se creato
            )
            if created:
                return Response({'status': 'student added'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'status': 'student already in group'}, status=status.HTTP_200_OK)
        except IntegrityError: # Potrebbe non essere necessario con get_or_create, ma per sicurezza
             return Response({'error': 'Database integrity error.'}, status=status.HTTP_400_BAD_REQUEST)


    # Permessi specificati in get_permissions
    @action(detail=True, methods=['post'], url_path='remove-student/(?P<student_pk>[^/.]+)')
    def remove_student(self, request, pk=None, student_pk=None):
        """
        Rimuove uno studente specificato nell'URL dal gruppo.
        Accessibile a Owner e utenti con accesso approvato.
        """
        group = self.get_object() # get_object applica IsOwnerOrHasAccess
        # Rimosso controllo teacher=request.user
        student = get_object_or_404(Student, pk=student_pk)

        membership = get_object_or_404(StudentGroupMembership, group=group, student=student)
        membership.delete()
        return Response({'status': 'student removed'}, status=status.HTTP_204_NO_CONTENT)


    # Permessi specificati in get_permissions
    @action(detail=True, methods=['post'], url_path='generate-token') # serializer_class gestito da get_serializer_class
    def generate_token(self, request, pk=None):
        """
        Genera o rigenera un token di registrazione per il gruppo.
        Accessibile solo all'Owner.
        """
        group = self.get_object() # get_object applica IsGroupOwner
        # Usa il metodo del modello per generare/rigenerare il token UUID
        group.generate_token() # Questo ora crea/aggiorna la relazione

        # Ottieni il link dal token appena generato/associato
        registration_link = group.registration_link

        if registration_link:
            # Istanzia GenerateTokenSerializer con il link completo
            serializer = GenerateTokenSerializer(data={'registration_link': registration_link})
            serializer.is_valid(raise_exception=True) # Valida i dati (URLField)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            # Caso di errore imprevisto (il token non è stato creato/associato correttamente)
            return Response({'error': 'Impossibile generare il link di registrazione.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    # Permessi specificati in get_permissions
    @action(detail=True, methods=['delete'], url_path='delete-token')
    def delete_token(self, request, pk=None):
        """
        Elimina (invalida) il token di registrazione del gruppo.
        Accessibile solo all'Owner.
        """
        group = self.get_object() # get_object applica IsGroupOwner
        if group.registration_token:
            # Usa il metodo del modello per eliminare il token associato
            group.delete_token()
            return Response({'status': 'token deleted'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'status': 'no active token to delete'}, status=status.HTTP_404_NOT_FOUND)

    # --- Azioni per la gestione delle richieste di accesso ---

    # Permessi specificati in get_permissions
    @action(detail=True, methods=['get'], url_path='access-requests') # serializer_class gestito da get_serializer_class
    def list_access_requests(self, request, pk=None):
        """
        Restituisce l'elenco delle richieste di accesso PENDENTI per questo gruppo.
        Accessibile solo all'Owner.
        Accessibile solo all'owner del gruppo.
        """
        group = self.get_object() # get_object applica IsGroupOwner
        # Filtra per richieste pendenti per questo gruppo specifico
        requests = GroupAccessRequest.objects.filter(group=group, status=GroupAccessRequest.AccessStatus.PENDING)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

    # Permessi specificati in get_permissions
    @action(detail=True, methods=['post'], url_path='respond-request') # serializer_class gestito da get_serializer_class
    def respond_access_request(self, request, pk=None):
        """
        Permette all'Owner del gruppo di approvare o rifiutare una richiesta di accesso.
        Richiede 'request_id' e 'status' ('approved' o 'rejected') nel body.
        """
        group = self.get_object() # get_object applica IsGroupOwner
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request_id = serializer.validated_data['request_id']
        new_status = serializer.validated_data['status'] # Già validato dal serializer

        # Trova la richiesta specifica per questo gruppo
        access_request = get_object_or_404(GroupAccessRequest, pk=request_id, group=group)

        # Verifica che la richiesta sia pendente
        if access_request.status != GroupAccessRequest.AccessStatus.PENDING:
            return Response({'error': 'Questa richiesta è già stata processata.'}, status=status.HTTP_400_BAD_REQUEST)

        # Aggiorna lo stato
        access_request.status = new_status
        access_request.responded_at = timezone.now()
        access_request.save()

        return Response({'status': f'Richiesta {access_request.id} aggiornata a {new_status}.'}, status=status.HTTP_200_OK)


# --- ViewSet per le richieste di accesso (dal punto di vista del richiedente) ---
# Da creare come prossimo passo (Fase 2, punto 1.4)
# class GroupAccessRequestViewSet(mixins.CreateModelMixin,
#                                mixins.ListModelMixin,
#                                mixins.RetrieveModelMixin,
#                                viewsets.GenericViewSet):
#     serializer_class = GroupAccessRequestSerializer
#     permission_classes = [IsAuthenticated] # O permessi più specifici
#     queryset = GroupAccessRequest.objects.all() # Sarà filtrato in get_queryset

#     def get_queryset(self):
#         # Mostra solo le richieste fatte dall'utente autenticato
#         return self.queryset.filter(requesting_teacher=self.request.user)

#     def perform_create(self, serializer):
#         # Associa automaticamente l'utente richiedente
#         # Assicurati che il gruppo richiesto sia pubblico
#         group_id = serializer.validated_data['group'].id
#         group = get_object_or_404(StudentGroup, pk=group_id, is_public=True)
#         # Controlla che non esista già una richiesta pendente o approvata
#         existing_request = GroupAccessRequest.objects.filter(
#             group=group,
#             requesting_teacher=self.request.user,
#             status__in=[GroupAccessRequest.AccessStatus.PENDING, GroupAccessRequest.AccessStatus.APPROVED]
#         ).exists()
#         if existing_request:
#              raise serializers.ValidationError("Hai già una richiesta pendente o approvata per questo gruppo.")
#         serializer.save(requesting_teacher=self.request.user, group=group)


# --- Vista per la registrazione tramite token (da implementare separatamente, magari in apps.users) ---
# class RegisterStudentByTokenView(generics.CreateAPIView):
#     ...
# --- ViewSet per le richieste di accesso (dal punto di vista del richiedente) ---
class GroupAccessRequestViewSet(mixins.CreateModelMixin,
                               mixins.ListModelMixin,
                               mixins.RetrieveModelMixin,
                               viewsets.GenericViewSet):
    """
    ViewSet per gestire le richieste di accesso ai gruppi.
    Permette ai docenti autenticati di:
    - Creare richieste per gruppi pubblici.
    - Visualizzare le proprie richieste inviate.
    """
    serializer_class = GroupAccessRequestSerializer
    permission_classes = [IsAuthenticated] # Base permission
    # queryset = GroupAccessRequest.objects.all() # Rimosso, gestito da get_queryset

    def get_permissions(self):
        """ Aggiunge IsRequestingTeacher per azioni su oggetti specifici. """
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']: # Se aggiungeremo update/destroy
             return [IsAuthenticated(), IsRequestingTeacher()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Mostra solo le richieste fatte dall'utente autenticato."""
        user = self.request.user
        if not user.is_authenticated:
            return GroupAccessRequest.objects.none()
        return GroupAccessRequest.objects.filter(requesting_teacher=user).select_related('group', 'group__owner')

    def perform_create(self, serializer):
        """
        Associa automaticamente l'utente richiedente e valida la richiesta.
        - Verifica che il gruppo target esista e sia pubblico.
        - Impedisce richieste duplicate (pendenti o approvate).
        - Impedisce richieste al proprio gruppo.
        """
        user = self.request.user
        group_id = serializer.validated_data['group'].id # Ottiene l'ID dal serializer validato

        # Verifica che il gruppo esista, sia pubblico e non sia dell'utente stesso
        try:
            group = StudentGroup.objects.get(pk=group_id, is_public=True)
        except StudentGroup.DoesNotExist:
             # Usiamo serializers.ValidationError per un messaggio più pulito al frontend
             from rest_framework import serializers
             raise serializers.ValidationError("Gruppo non trovato o non pubblico.")

        if group.owner == user:
            from rest_framework import serializers
            raise serializers.ValidationError("Non puoi richiedere l'accesso a un tuo gruppo.")

        # Controlla che non esista già una richiesta pendente o approvata per lo stesso utente/gruppo
        existing_request = GroupAccessRequest.objects.filter(
            group=group,
            requesting_teacher=user,
            status__in=[GroupAccessRequest.AccessStatus.PENDING, GroupAccessRequest.AccessStatus.APPROVED]
        ).exists()
        if existing_request:
             from rest_framework import serializers
             raise serializers.ValidationError("Hai già una richiesta pendente o approvata per questo gruppo.")

        # Se tutto ok, salva la richiesta associando l'utente e il gruppo corretto
        serializer.save(requesting_teacher=user, group=group)

# --- Vista per la registrazione tramite token (da implementare separatamente, magari in apps.users) ---
# class RegisterStudentByTokenView(generics.CreateAPIView):
#     ...


# --- Vista per elencare i gruppi pubblici disponibili per la richiesta ---
class PublicGroupsListView(generics.ListAPIView):
    """
    Restituisce un elenco di gruppi pubblici a cui l'utente autenticato
    può richiedere l'accesso. Esclude:
    - Gruppi non pubblici.
    - Gruppi di cui l'utente è già proprietario.
    - Gruppi per cui l'utente ha già una richiesta pendente o approvata.
    """
    serializer_class = StudentGroupSerializer # Usiamo il serializer base per l'elenco
    permission_classes = [IsAuthenticated] # Solo utenti autenticati possono sfogliare

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return StudentGroup.objects.none()

        # Trova gli ID dei gruppi per cui l'utente ha già una richiesta (pendente o approvata)
        existing_request_group_ids = GroupAccessRequest.objects.filter(
            requesting_teacher=user,
            status__in=[GroupAccessRequest.AccessStatus.PENDING, GroupAccessRequest.AccessStatus.APPROVED]
        ).values_list('group_id', flat=True)

        # Filtra i gruppi:
        # - Devono essere pubblici
        # - L'owner non deve essere l'utente corrente
        # - L'utente non deve avere richieste esistenti per quel gruppo
        queryset = StudentGroup.objects.filter(
            is_public=True
        ).exclude(
            owner=user
        ).exclude(
            pk__in=existing_request_group_ids
        ).select_related('owner') # Ottimizza includendo l'owner

        return queryset