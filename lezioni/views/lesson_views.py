from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from django.shortcuts import get_object_or_404

from ..models import Lesson, LessonContent, Topic
# Assumiamo che il modello User abbia un campo 'role'
# e che il modello Student sia importabile o gestito tramite request.user
# from apps.users.models import Student # Verificare path
from ..serializers import (
    LessonSerializer, LessonWriteSerializer, LessonContentSerializer,
    LessonAssignmentSerializer, AssignLessonSerializer # Aggiunto AssignLessonSerializer
)
from ..permissions import (
    IsTeacherOwner, IsAdminOrTeacherOwner, IsAssignedStudentOrTeacherOwner,
    IsAdminOrTeacher
)
# Import necessario per l'assegnazione
from ..models import LessonAssignment
try:
    from apps.users.models import Student
    from apps.student_groups.models import StudentGroup # Aggiunto import StudentGroup
except ImportError:
    Student = None
    StudentGroup = None # Gestiremo il caso in cui non siano importabili

class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet per visualizzare e modificare le Lezioni (Lesson).
    - I Docenti possono creare, leggere, aggiornare, eliminare le proprie lezioni.
    - Gli Studenti possono leggere solo le lezioni a loro assegnate (tramite endpoint custom).
    - Gli Admin possono leggere/eliminare tutte le lezioni.
    """
    queryset = Lesson.objects.select_related('topic__subject', 'creator').prefetch_related('contents').all().order_by('-created_at')

    def get_serializer_class(self):
        # Usa un serializer diverso per la scrittura (create/update)
        if self.action in ['create', 'update', 'partial_update']:
            return LessonWriteSerializer
        return LessonSerializer # Usa il serializer completo per la lettura

    def get_permissions(self):
        """
        Imposta permessi diversi in base all'azione.
        """
        if self.action in ['create']:
            # Solo Docenti autenticati possono creare
            permission_classes = [permissions.IsAuthenticated, IsAdminOrTeacher] # Modificato per permettere anche Admin? No, piano dice solo Docenti. Rivedere.
            # Per ora, assumiamo che solo i Docenti creino lezioni come da piano originale.
            # Se anche Admin deve creare, modificare IsAdminOrTeacher o creare IsTeacher.
            # Usiamo un controllo esplicito sul ruolo qui per chiarezza.
            if self.request.user.is_authenticated and self.request.user.role.upper() in ['DOCENTE', 'TEACHER']:
                 permission_classes = [permissions.IsAuthenticated]
            else:
                 # Blocca esplicitamente se non Docente/Teacher
                 permission_classes = [permissions.DenyAll]

        elif self.action in ['update', 'partial_update', 'destroy', 'assign_students']:
            # Solo il Docente proprietario può modificare, eliminare o assegnare
            # O l'Admin può eliminare (ma non modificare/assegnare?) - Rivedere permessi Admin
            # Per ora: solo TeacherOwner per update/assign, AdminOrTeacherOwner per destroy
            if self.action == 'destroy':
                 permission_classes = [permissions.IsAuthenticated, IsAdminOrTeacherOwner]
            else:
                 permission_classes = [permissions.IsAuthenticated, IsTeacherOwner]
        elif self.action in ['retrieve', 'list_contents']:
            # Docente proprietario o Studente assegnato possono vedere i dettagli
            # Admin può vedere tutto? Aggiungere IsAdminUser se necessario.
            permission_classes = [permissions.IsAuthenticated, IsAssignedStudentOrTeacherOwner]
        elif self.action == 'list':
             # Chi può listare tutte le lezioni? Solo Admin/Docenti?
             permission_classes = [permissions.IsAuthenticated, IsAdminOrTeacher]
        else:
            # Permessi di default (es. per azioni custom non definite)
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filtra il queryset base:
        - I Docenti vedono solo le proprie lezioni.
        - Gli Admin vedono tutte le lezioni.
        - Gli Studenti non usano questo queryset direttamente (usano endpoint custom).
        """
        user = self.request.user
        # Check if user exists and is authenticated
        if not user or not user.is_authenticated:
            return Lesson.objects.none()

        queryset = super().get_queryset() # Prende il queryset base definito sopra

        # Per la vista di dettaglio (retrieve), restituiamo il queryset base.
        # Il controllo dei permessi a livello di oggetto (IsAssignedStudentOrTeacherOwner)
        # gestirà chi può vedere cosa.
        if self.action == 'retrieve':
            return queryset

        # Controlla il ruolo in modo sicuro, gestendo diversi tipi di utente (per altre azioni come list)
        user_role = getattr(user, 'role', None) # Ottiene 'role' se esiste

        if user_role:
            role_upper = user_role.upper()
            if role_upper in ['DOCENTE', 'TEACHER']:
                 # Assume che per Docente/Teacher, request.user sia il modello User con FK 'creator'
                 return queryset.filter(creator=user)
            elif role_upper == 'ADMIN':
                 return queryset # Admin vede tutto
            # Altri ruoli autenticati (se esistono) non vedono la lista generale
            return Lesson.objects.none()
        else:
            # Se user non ha 'role', probabilmente è l'oggetto Student.
            # Gli studenti non accedono alla lista generale qui.
            # Per 'retrieve', get_object() e IsAssignedStudentOrTeacherOwner gestiranno l'accesso.
            return Lesson.objects.none()

    def perform_create(self, serializer):
        """ Imposta il creatore sul Docente loggato. """
        if self.request.user.role.upper() not in ['DOCENTE', 'TEACHER']:
             raise PermissionDenied("Solo Docenti o Teacher possono creare lezioni.")
        # Verifica che l'argomento esista (anche se il serializer dovrebbe farlo)
        topic_id = serializer.validated_data.get('topic').id
        if not Topic.objects.filter(id=topic_id).exists():
             raise NotFound(f"Argomento con ID {topic_id} non trovato.")
        serializer.save(creator=self.request.user)

    # --- Azione per Assegnazione a Studenti/Gruppi ---
    @action(detail=True, methods=['post'], url_path='assign', permission_classes=[permissions.IsAuthenticated, IsTeacherOwner])
    def assign(self, request, pk=None):
        """
        Assegna questa Lezione (pk) a una lista di Studenti e/o Gruppi.
        Richiede 'student_ids' (lista di ID) e/o 'group_ids' (lista di ID) nel corpo della richiesta.
        Restituisce un riepilogo delle assegnazioni create, già esistenti o fallite.
        """
        lesson = self.get_object() # Verifica ownership e recupera lezione
        student_ids = request.data.get('student_ids', [])
        group_ids = request.data.get('group_ids', [])

        if not isinstance(student_ids, list) or not all(isinstance(sid, int) for sid in student_ids):
            return Response({'detail': "'student_ids' deve essere una lista di interi."}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(group_ids, list) or not all(isinstance(gid, int) for gid in group_ids):
            return Response({'detail': "'group_ids' deve essere una lista di interi."}, status=status.HTTP_400_BAD_REQUEST)

        if not student_ids and not group_ids:
            return Response({'detail': "È necessario fornire almeno uno 'student_ids' o 'group_ids'."}, status=status.HTTP_400_BAD_REQUEST)

        # Validazione ID e Ownership
        valid_students = []
        invalid_student_ids = []
        if Student and student_ids:
            students = Student.objects.filter(id__in=student_ids, user_id=request.user.id) # Solo studenti del docente
            valid_students = list(students)
            valid_student_ids = {s.id for s in valid_students}
            invalid_student_ids = [sid for sid in student_ids if sid not in valid_student_ids]

        valid_groups = []
        invalid_group_ids = []
        if StudentGroup and group_ids:
            groups = StudentGroup.objects.filter(id__in=group_ids, teacher=request.user) # Solo gruppi del docente
            valid_groups = list(groups)
            valid_group_ids = {g.id for g in valid_groups}
            invalid_group_ids = [gid for gid in group_ids if gid not in valid_group_ids]

        # Costruzione risultati
        results = {
            "student_assignments": {"created": [], "already_assigned": [], "failed": invalid_student_ids},
            "group_assignments": {"created": [], "already_assigned": [], "failed": invalid_group_ids}
        }

        # Assegnazione Studenti
        for student in valid_students:
            try:
                assignment, created = LessonAssignment.objects.get_or_create(
                    lesson=lesson,
                    student=student,
                    defaults={'group': None} # Assicura che group sia None se si crea per studente
                )
                if created:
                    results["student_assignments"]["created"].append({'student': student.id})
                else:
                    results["student_assignments"]["already_assigned"].append(student.id)
            except Exception as e:
                 # Loggare l'errore specifico se necessario
                 results["student_assignments"]["failed"].append(student.id) # Aggiunge a falliti se c'è errore in get_or_create

        # Assegnazione Gruppi
        for group in valid_groups:
             try:
                assignment, created = LessonAssignment.objects.get_or_create(
                    lesson=lesson,
                    group=group,
                    defaults={'student': None} # Assicura che student sia None se si crea per gruppo
                )
                if created:
                    results["group_assignments"]["created"].append({'group': group.id})
                else:
                    results["group_assignments"]["already_assigned"].append(group.id)
             except Exception as e:
                 results["group_assignments"]["failed"].append(group.id)

        # Determina lo status code finale
        final_status = status.HTTP_201_CREATED if results["student_assignments"]["created"] or results["group_assignments"]["created"] else status.HTTP_200_OK

        return Response(results, status=final_status)


# Rimosso @action list_contents perché gestito dal LessonContentViewSet annidato

class LessonContentViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestire i Contenuti (LessonContent) di una Lezione.
    Questo ViewSet è pensato per essere usato con router annidati (nested routers)
    sotto una specifica lezione (es. /api/lezioni/lessons/{lesson_pk}/contents/).
    L'accesso è limitato al Docente proprietario della lezione padre.
    """
    serializer_class = LessonContentSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherOwner] # Solo il Docente proprietario può modificare i contenuti

    def get_queryset(self):
        """
        Filtra i contenuti per la lezione specificata nell'URL.
        """
        lesson_pk = self.kwargs.get('lesson_pk')
        if not lesson_pk:
             # Questo non dovrebbe accadere con un router annidato configurato correttamente
             return LessonContent.objects.none()

        # Filtra per la lezione padre
        queryset = LessonContent.objects.filter(lesson_id=lesson_pk)

        # Verifica che l'utente sia il proprietario della lezione padre
        try:
            lesson = Lesson.objects.get(pk=lesson_pk)
            if lesson.creator != self.request.user:
                 # Se l'utente non è il creatore, non può vedere/modificare i contenuti
                 # (Anche se il permesso IsTeacherOwner dovrebbe già bloccare)
                 return LessonContent.objects.none()
        except Lesson.DoesNotExist:
            return LessonContent.objects.none() # Lezione non trovata

        return queryset.order_by('order')

    def perform_create(self, serializer):
        """
        Associa il nuovo contenuto alla lezione specificata nell'URL.
        Verifica che l'utente sia il proprietario della lezione.
        """
        lesson_pk = self.kwargs.get('lesson_pk')
        # Recupera la lezione associata dall'URL
        # Usiamo get_object_or_404 per gestire il caso in cui la lezione non esista
        lesson = get_object_or_404(Lesson, pk=lesson_pk)

        # Verifica permesso (doppio controllo oltre a permission_classes)
        # Assicurati che l'utente loggato sia il creatore della lezione padre
        if lesson.creator != self.request.user:
            raise PermissionDenied("Non hai il permesso di aggiungere contenuti a questa lezione.")

        # Aggiungere validazione specifica per content_type?
        # Es: se type='pdf', assicurarsi che 'file' sia presente.
        # Il serializer potrebbe gestire parte di questa logica.

        # Associa il nuovo contenuto alla lezione e salva
        serializer.save(lesson=lesson)

        # Verifica permesso (doppio controllo oltre a permission_classes)
        if lesson.creator != self.request.user:
            raise PermissionDenied("Non hai il permesso di aggiungere contenuti a questa lezione.")

        # Aggiungere validazione specifica per content_type?
        # Es: se type='pdf', assicurarsi che 'file' sia presente.
        # Il serializer potrebbe gestire parte di questa logica.

        serializer.save(lesson=lesson)

    def perform_update(self, serializer):
        """ Salva le modifiche al contenuto. """
        # Il queryset è già filtrato per la lezione corretta e i permessi verificati
        serializer.save()

    def perform_destroy(self, instance):
        """ Elimina il contenuto. """
        # Il queryset è già filtrato e i permessi verificati
        instance.delete()