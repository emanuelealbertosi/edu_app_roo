import logging
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied as DRFPermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.db.models import Max, F

from .models import Subject, Topic, Lesson, LessonContent, LessonAssignment
from .serializers import (
    SubjectSerializer, TopicSerializer, LessonSerializer, LessonWriteSerializer,
    LessonContentSerializer, LessonAssignmentSerializer, AssignLessonSerializer
)
# Importa permessi standard e custom (se esistono)
from rest_framework.permissions import IsAuthenticated
from apps.users.permissions import IsTeacherUser, IsAdminUser, IsStudentAuthenticated # Assumendo che esistano
# Importa modelli utente e gruppo
from apps.users.models import User, Student
from apps.student_groups.models import StudentGroup
# Importa il Revoke serializer da education se vogliamo riusarlo
try:
    from apps.education.views import QuizViewSet as EducationQuizViewSet # Alias per evitare conflitti
    RevokeAssignmentSerializer = EducationQuizViewSet.RevokeAssignmentSerializer
except (ImportError, AttributeError):
    # Fallback: definisci un serializer di revoca qui se non importabile
    class RevokeAssignmentSerializer(serializers.Serializer):
        assignment_id = serializers.IntegerField(required=True, help_text="ID dell'assegnazione da revocare.")


logger = logging.getLogger(__name__)

# --- Permessi Custom (Esempio, adattare se necessario) ---

class IsLessonOwnerOrAdmin(permissions.BasePermission):
    """ Permesso per verificare se l'utente è il creatore della Lezione o Admin. """
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            if request.user.is_admin:
                return True
            # Assumendo che Lesson abbia un campo 'creator' FK a User
            return obj.creator == request.user
        return False

class IsTopicOwnerOrAdmin(permissions.BasePermission):
     """ Permesso per verificare se l'utente è il creatore dell'Argomento o Admin. """
     def has_object_permission(self, request, view, obj):
         if request.user.is_authenticated:
             if request.user.is_admin:
                 return True
             return obj.creator == request.user
         return False

class IsSubjectOwnerOrAdmin(permissions.BasePermission):
     """ Permesso per verificare se l'utente è il creatore della Materia o Admin. """
     def has_object_permission(self, request, view, obj):
         if request.user.is_authenticated:
             if request.user.is_admin:
                 return True
             return obj.creator == request.user
         return False


# --- ViewSets ---

class SubjectViewSet(viewsets.ModelViewSet):
    """ API endpoint per le Materie (Subjects). """
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated, (IsTeacherUser | IsAdminUser)] # Solo Docenti o Admin possono creare/modificare

    def get_queryset(self):
        """ Docenti/Admin vedono tutte le materie? O solo le proprie?
            Per ora, assumiamo che vedano tutte. Filtrare se necessario. """
        # if self.request.user.is_teacher:
        #     return Subject.objects.filter(creator=self.request.user)
        # elif self.request.user.is_admin:
        #     return Subject.objects.all()
        # return Subject.objects.none()
        # Semplificato: IsAuthenticated + (IsTeacherUser | IsAdminUser) dovrebbe bastare
        return Subject.objects.all()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    # Applica IsSubjectOwnerOrAdmin per update/delete a livello di oggetto
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSubjectOwnerOrAdmin()]
        return super().get_permissions()


class TopicViewSet(viewsets.ModelViewSet):
    """ API endpoint per gli Argomenti (Topics), nidificato sotto Subject. """
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated, (IsTeacherUser | IsAdminUser)]

    def get_queryset(self):
        """ Filtra argomenti per la materia specificata nell'URL. """
        subject_pk = self.kwargs.get('subject_pk')
        if not subject_pk:
            return Topic.objects.none() # O solleva errore?
        # Filtra per materia e opzionalmente per creatore se non admin
        queryset = Topic.objects.filter(subject_id=subject_pk)
        # if not self.request.user.is_admin:
        #     queryset = queryset.filter(creator=self.request.user) # Docente vede solo i suoi argomenti?
        return queryset.select_related('subject') # Ottimizza query

    def perform_create(self, serializer):
        subject = get_object_or_404(Subject, pk=self.kwargs['subject_pk'])
        # Verifica se il creatore della materia può creare argomenti (opzionale)
        # if not self.request.user.is_admin and subject.creator != self.request.user:
        #     raise DRFPermissionDenied("Non puoi creare argomenti per questa materia.")
        serializer.save(creator=self.request.user, subject=subject)

    # Applica IsTopicOwnerOrAdmin per update/delete
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsTopicOwnerOrAdmin()]
        return super().get_permissions()


class LessonViewSet(viewsets.ModelViewSet):
    """ API endpoint per le Lezioni (Lessons), nidificato sotto Topic. """
    permission_classes = [IsAuthenticated, (IsTeacherUser | IsAdminUser)]

    def get_serializer_class(self):
        # Usa serializer diversi per lettura e scrittura
        if self.action in ['create', 'update', 'partial_update']:
            return LessonWriteSerializer
        return LessonSerializer # Per list, retrieve

    def get_queryset(self):
        """ Filtra lezioni per l'argomento specificato nell'URL. """
        topic_pk = self.kwargs.get('topic_pk')
        if not topic_pk:
            return Lesson.objects.none()
        queryset = Lesson.objects.filter(topic_id=topic_pk)
        # if not self.request.user.is_admin:
        #     queryset = queryset.filter(creator=self.request.user) # Docente vede solo le sue lezioni?
        return queryset.select_related('topic__subject', 'creator').prefetch_related('contents')

    def perform_create(self, serializer):
        topic = get_object_or_404(Topic, pk=self.kwargs['topic_pk'])
        # if not self.request.user.is_admin and topic.creator != self.request.user:
        #     raise DRFPermissionDenied("Non puoi creare lezioni per questo argomento.")
        serializer.save(creator=self.request.user, topic=topic)

    # Applica IsLessonOwnerOrAdmin per update/delete
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsLessonOwnerOrAdmin()]
        # Permessi specifici per assign/revoke
        if self.action in ['assign', 'revoke']:
             return [IsAuthenticated(), IsLessonOwnerOrAdmin()] # Solo il creatore può assegnare/revocare
        return super().get_permissions()

    # --- Azioni per Assegnazione/Revoca ---

    @action(detail=True, methods=['post'], url_path='assign', permission_classes=[IsAuthenticated, IsLessonOwnerOrAdmin])
    def assign(self, request, pk=None, topic_pk=None): # topic_pk non serve qui ma DRF lo passa
        """
        Assegna questa Lezione (pk) a uno Studente o a un Gruppo.
        Richiede 'student_id' o 'group_id' nel corpo della richiesta.
        """
        lesson = self.get_object() # Verifica ownership e recupera lezione
        serializer = AssignLessonSerializer(data=request.data, context={'request': request, 'lesson': lesson})

        if serializer.is_valid():
            try:
                assignment = serializer.save()
                # Usa LessonAssignmentSerializer per la risposta (fatto da to_representation)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                logger.warning(f"Errore validazione assegnazione lezione {pk} da utente {request.user.id}: {e.detail}")
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            except IntegrityError as e:
                 logger.error(f"Errore integrità assegnazione lezione {pk} da utente {request.user.id}: {e}", exc_info=True)
                 return Response({'detail': 'Errore durante il salvataggio dell\'assegnazione.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                 logger.error(f"Errore imprevisto assegnazione lezione {pk} da utente {request.user.id}: {e}", exc_info=True)
                 return Response({'detail': 'Errore interno durante l\'assegnazione.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Errore dati richiesta assegnazione lezione {pk} da utente {request.user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='revoke', permission_classes=[IsAuthenticated, IsLessonOwnerOrAdmin])
    def revoke(self, request, pk=None, topic_pk=None):
        """
        Revoca un'assegnazione specifica (identificata da 'assignment_id') per questa Lezione (pk).
        """
        lesson = self.get_object() # Verifica ownership lezione
        serializer = RevokeAssignmentSerializer(data=request.data) # Riusa serializer

        if serializer.is_valid():
            assignment_id = serializer.validated_data['assignment_id']
            try:
                assignment = get_object_or_404(LessonAssignment, id=assignment_id, lesson=lesson)
                assignment.delete()
                logger.info(f"Assegnazione Lezione ID {assignment_id} (Lezione ID {pk}) revocata da utente {request.user.id}")
                return Response(status=status.HTTP_204_NO_CONTENT)
            except LessonAssignment.DoesNotExist:
                 logger.warning(f"Tentativo revoca assegnazione lezione non trovata ID {assignment_id} per lezione {pk} da utente {request.user.id}")
                 return Response({'detail': 'Assegnazione non trovata per questa lezione.'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                 logger.error(f"Errore imprevisto revoca assegnazione lezione {assignment_id} (Lezione {pk}) da utente {request.user.id}: {e}", exc_info=True)
                 return Response({'detail': 'Errore interno durante la revoca.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Errore dati richiesta revoca assegnazione lezione {pk} da utente {request.user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LessonContentViewSet(viewsets.ModelViewSet):
    """ API endpoint per i Contenuti (LessonContent), nidificato sotto Lesson. """
    serializer_class = LessonContentSerializer
    permission_classes = [IsAuthenticated, (IsTeacherUser | IsAdminUser)]

    def get_queryset(self):
        """ Filtra contenuti per la lezione specificata nell'URL. """
        lesson_pk = self.kwargs.get('lesson_pk')
        if not lesson_pk:
            return LessonContent.objects.none()
        queryset = LessonContent.objects.filter(lesson_id=lesson_pk)
        # Verifica ownership della lezione padre
        lesson = get_object_or_404(Lesson, pk=lesson_pk)
        if not self.request.user.is_admin and lesson.creator != self.request.user:
             raise DRFPermissionDenied("Non hai accesso ai contenuti di questa lezione.")
        return queryset.order_by('order') # Ordina per coerenza

    def perform_create(self, serializer):
        lesson = get_object_or_404(Lesson, pk=self.kwargs['lesson_pk'])
        if not self.request.user.is_admin and lesson.creator != self.request.user:
             raise DRFPermissionDenied("Non puoi aggiungere contenuti a questa lezione.")
        # Calcola ordine
        last_order = LessonContent.objects.filter(lesson=lesson).aggregate(Max('order'))['order__max']
        next_order = 0 if last_order is None else last_order + 1
        serializer.save(lesson=lesson, order=next_order)

    @transaction.atomic
    def perform_destroy(self, instance):
        """ Elimina il contenuto e riordina i successivi. """
        lesson = instance.lesson
        # Verifica ownership (doppio controllo)
        if not self.request.user.is_admin and lesson.creator != self.request.user:
             raise DRFPermissionDenied("Non puoi eliminare contenuti da questa lezione.")

        deleted_order = instance.order
        instance.delete()

        # Riordina
        contents_to_reorder = LessonContent.objects.filter(
            lesson=lesson,
            order__gt=deleted_order
        ).order_by('order')
        updated_count = contents_to_reorder.update(order=F('order') - 1)
        logger.info(f"Riordinati {updated_count} contenuti nella lezione {lesson.id} dopo eliminazione ordine {deleted_order}.")

    # Applica IsLessonOwnerOrAdmin (tramite la lezione padre) per update/delete
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            # Recupera la lezione associata per verificare ownership
            lesson_pk = self.kwargs.get('lesson_pk')
            lesson = get_object_or_404(Lesson, pk=lesson_pk)
            if not self.request.user.is_admin and lesson.creator != self.request.user:
                 self.permission_denied(self.request, message="Non sei il proprietario della lezione.")
        return super().get_permissions()


# --- ViewSet Assegnazioni ---

class LessonAssignmentViewSet(viewsets.ReadOnlyModelViewSet): # ReadOnly perché create/delete avvengono tramite azioni su LessonViewSet
    """
    API endpoint per visualizzare le assegnazioni delle lezioni.
    Filtra automaticamente per lo studente loggato.
    Include azione per marcare come vista.
    """
    serializer_class = LessonAssignmentSerializer
    permission_classes = [IsAuthenticated] # Tutti gli utenti autenticati possono vedere le proprie assegnazioni

    def get_queryset(self):
        """
        Restituisce le assegnazioni per lo studente loggato (dirette o via gruppo).
        Docenti/Admin potrebbero vedere altro? Per ora focus sullo studente.
        """
        user = self.request.user
        if hasattr(user, 'student_profile'): # Verifica se l'utente è uno studente
            student = user.student_profile
            # Trova ID gruppi dello studente
            group_ids = student.studentgroupmembership_set.values_list('group_id', flat=True)
            # Filtra assegnazioni dirette allo studente O a uno dei suoi gruppi
            queryset = LessonAssignment.objects.filter(
                models.Q(student=student) | models.Q(group_id__in=group_ids)
            ).select_related(
                'lesson__topic__subject', # Precarica dati correlati per efficienza
                'lesson__creator',
                'assigned_by', # Utente che ha assegnato (potrebbe essere admin o docente)
                'student', # Assegnatario studente (se diretto)
                'group' # Gruppo assegnatario (se via gruppo)
            ).distinct() # Evita duplicati se assegnato sia a studente che a gruppo (improbabile ma sicuro)
            return queryset.order_by('-assigned_at') # Ordina per data assegnazione decrescente
        elif user.is_teacher or user.is_admin:
             # TODO: Definire cosa vedono Docenti/Admin qui?
             # Potrebbero vedere tutte le assegnazioni relative alle loro lezioni?
             # O tutte le assegnazioni dei loro studenti?
             # Per ora, restituiamo un queryset vuoto per non esporre dati non previsti.
             logger.warning(f"Accesso a LessonAssignmentViewSet da non-studente (ID: {user.id}, Ruolo: {user.role}). Queryset vuoto restituito.")
             return LessonAssignment.objects.none()
        else:
            # Utente non studente, non docente, non admin?
             logger.error(f"Accesso a LessonAssignmentViewSet da utente con ruolo imprevisto (ID: {user.id}, Ruolo: {user.role}).")
             return LessonAssignment.objects.none()

    @action(detail=True, methods=['post'], url_path='mark-viewed', permission_classes=[IsAuthenticated]) # Permesso base, il filtro queryset protegge
    def mark_viewed(self, request, pk=None):
        """ Marca un'assegnazione specifica come vista dallo studente. """
        assignment = self.get_object() # get_object usa get_queryset, quindi filtra per utente

        # Verifica ulteriore: solo lo studente assegnatario (o membro del gruppo) può marcare come visto?
        # get_queryset dovrebbe già garantire questo se l'utente è studente.
        if not hasattr(request.user, 'student_profile') or \
           (assignment.student != request.user.student_profile and \
            not request.user.student_profile.studentgroupmembership_set.filter(group=assignment.group).exists()):
             logger.warning(f"Utente {request.user.id} ha tentato di marcare come vista assegnazione {pk} non sua.")
             raise DRFPermissionDenied("Non puoi marcare come vista questa assegnazione.")

        if assignment.viewed_at is None:
            assignment.viewed_at = timezone.now()
            assignment.save(update_fields=['viewed_at'])
            logger.info(f"Assegnazione Lezione ID {pk} marcata come vista da utente {request.user.id}")
            # Restituisce l'assegnazione aggiornata
            serializer = self.get_serializer(assignment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Già vista, restituisce 200 OK senza modifiche o 304 Not Modified?
            # Restituiamo 200 con i dati esistenti per semplicità.
            logger.info(f"Assegnazione Lezione ID {pk} era già vista da utente {request.user.id}. Nessuna modifica.")
            serializer = self.get_serializer(assignment)
            return Response(serializer.data, status=status.HTTP_200_OK)


# --- Viste per Studenti ---

# La logica sopra in LessonAssignmentViewSet.get_queryset copre la necessità di questa vista commentata.
# Rimuovere/lasciare commentata la definizione di esempio sotto.
# Aggiungere qui una vista simile a StudentAssignedQuizzesView/StudentAssignedPathwaysView
# per permettere agli studenti di vedere le lezioni a loro assegnate (direttamente o tramite gruppo)
# Esempio:
# class StudentAssignedLessonsView(generics.ListAPIView):
#     serializer_class = LessonSerializer # O un serializer specifico per la dashboard studente
#     permission_classes = [IsStudentAuthenticated]
#
#     def get_queryset(self):
#         student = self.request.user # Assumendo che request.user sia l'oggetto Student
#         # Trova ID lezioni assegnate direttamente
#         direct_lesson_ids = LessonAssignment.objects.filter(student=student).values_list('lesson_id', flat=True)
#         # Trova ID gruppi dello studente
#         group_ids = student.studentgroupmembership_set.values_list('group_id', flat=True)
#         # Trova ID lezioni assegnate ai gruppi dello studente
#         group_lesson_ids = LessonAssignment.objects.filter(group_id__in=group_ids).values_list('lesson_id', flat=True)
#         # Unisci gli ID e rimuovi duplicati
#         all_lesson_ids = set(direct_lesson_ids) | set(group_lesson_ids)
#
#         queryset = Lesson.objects.filter(id__in=all_lesson_ids, is_published=True) # Mostra solo lezioni pubblicate
#         # Aggiungere prefetch/select_related se necessario
#         return queryset.select_related('topic__subject', 'creator').prefetch_related('contents')
#
#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         context['student'] = self.request.user # Passa lo studente al contesto se serve nel serializer
#         return context

# Aggiungere vista dettaglio lezione per studente?
# Aggiungere azione per marcare lezione come vista?
