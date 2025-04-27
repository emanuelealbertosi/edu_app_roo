from rest_framework import generics, status, permissions, mixins, viewsets # Import generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import IntegrityError
import secrets
from django.conf import settings
from urllib.parse import urljoin, urlencode

from .models import StudentGroup, StudentGroupMembership
from apps.users.models import Student, UserRole # Importa UserRole
from .serializers import (
    StudentGroupSerializer,
    StudentGroupDetailSerializer,
    StudentGroupMembershipSerializer,
    GenerateTokenSerializer,
    AddStudentSerializer,
)
from apps.users.serializers import StudentBasicSerializer # Importa il serializer per gli studenti
# Assicurati che esista un file permissions.py o importa i permessi standard
# from .permissions import IsTeacherOwnerOrReadOnly # Esempio permesso custom
from rest_framework.permissions import IsAuthenticated # Usiamo permessi standard per ora

class IsTeacherOwner(permissions.BasePermission):
    """
    Permesso per consentire solo al docente proprietario di modificare/eliminare.
    """
    def has_object_permission(self, request, view, obj):
        # Permessi di lettura sono concessi a tutti gli autenticati (o da definire)
        # if request.method in permissions.SAFE_METHODS:
        #     return True # O logica più specifica se necessario

        # Permessi di scrittura solo al docente proprietario
        return obj.teacher == request.user

# Semplifichiamo il ViewSet per debuggare l'errore 405 su POST
# Usiamo solo i mixin per list e create
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
    queryset = StudentGroup.objects.all()
    permission_classes = [IsAuthenticated, IsTeacherOwner] # Ripristina permesso originale

    # Esplicita i metodi HTTP permessi (anche se dovrebbero essere default per ModelViewSet)
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    # Explicitly define create to ensure it's recognized
    def create(self, request, *args, **kwargs):
        """Handles POST requests to create a new StudentGroup."""
        return super().create(request, *args, **kwargs)

    # Rimuoviamo l'override temporaneo, ora usiamo get_serializer_class
    # serializer_class = StudentGroupSerializer # Usiamo sempre il serializer base per ora

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'update' or self.action == 'partial_update':
            return StudentGroupDetailSerializer
        return StudentGroupSerializer

    def get_queryset(self):
        """Filtra i gruppi per mostrare solo quelli del docente autenticato."""
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'role') and user.role == UserRole.TEACHER: # Usa UserRole.TEACHER per il confronto
             # Assumendo che il modello User abbia un campo 'role'
             # o un modo per identificare i docenti.
            return StudentGroup.objects.filter(teacher=user).prefetch_related('memberships__student') # Usa il related_name corretto 'memberships'
        return StudentGroup.objects.none() # Non mostrare nulla se non è un docente

    def perform_create(self, serializer):
        """Associa automaticamente il docente autenticato durante la creazione."""
        serializer.save(teacher=self.request.user)

    # --- Azioni Custom ---

    @action(detail=True, methods=['get'], url_path='students', serializer_class=StudentBasicSerializer)
    def students(self, request, pk=None):
        """
        Restituisce l'elenco degli studenti membri del gruppo.
        """
        group = self.get_object() # Ottiene il gruppo corrente (gestisce 404 e permessi)
        # Ottieni gli studenti tramite la tabella di membership
        students = Student.objects.filter(group_memberships__group=group) # Usa il related_name corretto
        # Serializza gli studenti esplicitamente con StudentBasicSerializer
        serializer = StudentBasicSerializer(students, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], serializer_class=AddStudentSerializer, url_path='add-student')
    def add_student(self, request, pk=None):
        """ Aggiunge uno studente specificato nel body al gruppo. """
        # print(f"[DEBUG] Entered add_student action for group pk={pk}") # DEBUG REMOVED
        group = self.get_object()
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

        student = get_object_or_404(Student, pk=student_id, teacher=request.user) # Assicura che lo studente appartenga al docente

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


    @action(detail=True, methods=['post'], url_path='remove-student/(?P<student_pk>[^/.]+)') # Usa POST per coerenza RESTful (DELETE sarebbe ideale ma più complesso da implementare qui)
    def remove_student(self, request, pk=None, student_pk=None):
        """ Rimuove uno studente specificato nell'URL dal gruppo. """
        group = self.get_object()
        student = get_object_or_404(Student, pk=student_pk, teacher=request.user) # Verifica appartenenza studente al docente

        membership = get_object_or_404(StudentGroupMembership, group=group, student=student)
        membership.delete()
        return Response({'status': 'student removed'}, status=status.HTTP_204_NO_CONTENT)


    @action(detail=True, methods=['post'], serializer_class=GenerateTokenSerializer, url_path='generate-token')
    def generate_token(self, request, pk=None):
        """ Genera o rigenera un token di registrazione per il gruppo. """
        group = self.get_object()
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


    @action(detail=True, methods=['delete'], url_path='delete-token') # Modificato per accettare DELETE
    def delete_token(self, request, pk=None):
        """ Elimina (invalida) il token di registrazione del gruppo. """
        group = self.get_object()
        if group.registration_token:
            # Usa il metodo del modello per eliminare il token associato
            group.delete_token()
            return Response({'status': 'token deleted'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'status': 'no active token to delete'}, status=status.HTTP_404_NOT_FOUND)

# --- Vista per la registrazione tramite token (da implementare separatamente, magari in apps.users) ---
# class RegisterStudentByTokenView(generics.CreateAPIView):
#     ...