from rest_framework import viewsets, permissions, mixins, status # Aggiunto status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth import get_user_model # Utile per Admin/Docente
from django.db.models import Q # Import per query OR

from ..models import LessonAssignment, Lesson
# Importa Student per controllo tipo
# e che il modello Student sia importabile o gestito tramite request.user
# from apps.users.models import Student # Verificare path
from apps.users.models import Student # Assumiamo questo path
from ..serializers import LessonAssignmentSerializer
from ..permissions import IsAdminOrTeacher, IsTeacherOwner # Importa permessi necessari

class LessonAssignmentViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              # mixins.UpdateModelMixin, # Forse per marcare come visto?
                              viewsets.GenericViewSet):
    """
    ViewSet per visualizzare le Assegnazioni delle Lezioni (LessonAssignment).
    - I Docenti possono listare le assegnazioni per le lezioni che hanno creato.
    - Gli Studenti possono listare le proprie assegnazioni (tramite endpoint custom).
    - Gli Admin possono listare tutte le assegnazioni.
    - Non permette la creazione diretta (avviene tramite LessonViewSet.assign_students).
    - Non permette l'eliminazione diretta (gestire la rimozione di un'assegnazione?).
    """
    serializer_class = LessonAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated] # Permesso base, poi affinato nel queryset

    def get_queryset(self):
        """
        Filtra le assegnazioni in base al ruolo dell'utente.
        """
        user = self.request.user
        if not user.is_authenticated:
            return LessonAssignment.objects.none()

        queryset = LessonAssignment.objects.select_related(
            'lesson__topic__subject', # Precarica dati correlati per efficienza
            'lesson__creator',
            'student', # Assegnatario studente (se diretto)
            'group' # Gruppo assegnatario (se via gruppo)
            # 'assigned_by' rimosso perché non presente nel modello
        ).all()

        # Filtro per lezione specifica (se fornito come query param)
        lesson_id = self.request.query_params.get('lesson_id')
        if lesson_id:
             # Verifica che l'utente abbia il permesso di vedere questa lezione specifica
             try:
                 lesson = Lesson.objects.get(pk=lesson_id)
                 # Solo Admin o Docente proprietario possono filtrare per una lezione specifica
                 if not (user.role == 'Admin' or (user.role == 'Docente' and lesson.creator == user)):
                      return LessonAssignment.objects.none() # Non autorizzato a vedere questa lezione
                 queryset = queryset.filter(lesson_id=lesson_id)
             except Lesson.DoesNotExist:
                 return LessonAssignment.objects.none() # Lezione non trovata

        # Filtro per tipo utente/ruolo
        if isinstance(user, Student):
            # Lo studente vede le assegnazioni dirette O quelle dei suoi gruppi
            # Corretto related_name: 'group_memberships' come definito nel modello StudentGroupMembership
            student_group_ids = user.group_memberships.values_list('group_id', flat=True)
            queryset = queryset.filter(
                Q(student=user) | Q(group_id__in=student_group_ids)
            ).distinct() # distinct() per evitare duplicati se assegnato sia a studente che a gruppo
        # Controlla se l'utente ha l'attributo 'role' (per Docente/Admin)
        elif hasattr(user, 'role'):
            if user.role == 'Docente':
                # Il docente vede le assegnazioni delle lezioni che ha creato
                queryset = queryset.filter(lesson__creator=user)
            elif user.role == 'Admin':
                # Admin vede tutto (il queryset non viene ulteriormente filtrato)
                pass
            else:
                # Altri ruoli (non Student, non Docente, non Admin) non vedono nulla
                return LessonAssignment.objects.none()
        else:
            # Utente autenticato ma non è Studente e non ha ruolo? Stato invalido.
            return LessonAssignment.objects.none()


        return queryset.order_by('-assigned_at')

    # Azione custom per marcare un'assegnazione come vista dallo studente
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='mark-viewed')
    def mark_as_viewed(self, request, pk=None):
        """
        Permette a uno studente di marcare un'assegnazione come vista.
        """
        assignment = self.get_object() # Ottiene l'assegnazione specifica

        # Verifica che l'utente sia uno studente e che sia l'assegnatario diretto O membro del gruppo assegnato
        is_authorized = False
        if request.user.is_authenticated and isinstance(request.user, Student):
            is_direct_assignee = (assignment.student == request.user)
            is_group_member = False
            if assignment.group:
                 # Verifica se lo studente è membro del gruppo assegnato
                 is_group_member = request.user.group_memberships.filter(group=assignment.group).exists()

            if is_direct_assignee or is_group_member:
                is_authorized = True

        if not is_authorized:
             return Response({"detail": "Non autorizzato a marcare questa assegnazione come vista."}, status=status.HTTP_403_FORBIDDEN)

        # Marca come vista solo se non è già stata marcata
        if assignment.viewed_at is None:
            assignment.viewed_at = timezone.now()
            assignment.save(update_fields=['viewed_at'])

        serializer = self.get_serializer(assignment)
        return Response(serializer.data)