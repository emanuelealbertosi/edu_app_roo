import logging # Import logging
from rest_framework import viewsets, permissions, status, serializers, generics, parsers # Import generics AND parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied as DRFPermissionDenied # Aggiunto import e rinominato per chiarezza
from django.db import transaction, models, IntegrityError # Import IntegrityError
from django.db.models import Max # Import Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import PermissionDenied # Import PermissionDenied Django
from django.db.models import F, OuterRef, Subquery, Count, Prefetch, Avg, Case, When, FloatField # Import Avg, Case, When, FloatField
from apps.users.permissions import IsAdminUser, IsTeacherUser, IsStudentAuthenticated # Import permessi specifici
from apps.users.models import User, Student # Import User e Student
from .models import (
    QuizTemplate, QuestionTemplate, AnswerOptionTemplate,
    Quiz, Question, AnswerOption, Pathway, PathwayQuiz,
    QuizAttempt, StudentAnswer, PathwayProgress, QuestionType,
    QuizAssignment, PathwayAssignment, PathwayTemplate, PathwayQuizTemplate # Importa i modelli Assignment e Template Percorsi
)
from .serializers import (
    QuizTemplateSerializer, QuestionTemplateSerializer, AnswerOptionTemplateSerializer,
    QuizSerializer, QuestionSerializer, AnswerOptionSerializer, PathwaySerializer, PathwayQuizSerializer, # Aggiunto PathwayQuizSerializer
    QuizAttemptSerializer, StudentAnswerSerializer, PathwayProgressSerializer,
    QuizAttemptDetailSerializer, # Importa il nuovo serializer
    StudentQuizDashboardSerializer, StudentPathwayDashboardSerializer, # Importa i nuovi serializer
    QuizUploadSerializer, # Aggiunto QuizUploadSerializer
    SimpleQuizAttemptSerializer, # Importa SimpleQuizAttemptSerializer
    PathwayAttemptDetailSerializer, # Importa il serializer per la nuova view
    NextPathwayQuizSerializer, # Aggiunto import mancante
    # Nuovi Serializer per Template Percorsi e Assegnazioni
    PathwayTemplateSerializer, PathwayQuizTemplateSerializer,
    QuizAssignmentSerializer, PathwayAssignmentSerializer, QuizAssignmentDetailSerializer, PathwayAssignmentDetailSerializer, # Importa nuovi serializer
    QuizTemplateStatsSerializer, PathwayTemplateStatsSerializer # Importa i serializer per le statistiche
)
from .permissions import (
    IsAdminOrReadOnly, IsQuizTemplateOwnerOrAdmin, IsQuizOwnerOrAdmin, IsPathwayOwnerOrAdmin, # Updated IsPathwayOwner -> IsPathwayOwnerOrAdmin
    IsStudentOwnerForAttempt, IsTeacherOfStudentForAttempt, IsAnswerOptionOwner # Aggiunto IsAnswerOptionOwner
    # Rimosso IsTeacherOwner che non esiste
)
from apps.users.permissions import IsAdminUser, IsTeacherUser, IsStudent, IsStudentAuthenticated # Import IsStudentAuthenticated
from apps.users.models import UserRole, Student, User # Import modelli utente e User
from apps.rewards.models import Wallet, PointTransaction # Import Wallet e PointTransaction
from .models import QuizAssignment, PathwayAssignment, QuizAttempt, PathwayProgress # Assicurati che siano importati

# Get an instance of a logger
logger = logging.getLogger(__name__)

# --- ViewSets per Admin (Templates) ---
class QuizTemplateViewSet(viewsets.ModelViewSet):
    """ API endpoint per i Quiz Templates (Admin). """
    serializer_class = QuizTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser] # Solo Admin

    def get_queryset(self):
        return QuizTemplate.objects.all()

    def perform_create(self, serializer):
        serializer.save(admin=self.request.user)

class QuestionTemplateViewSet(viewsets.ModelViewSet):
    """ API endpoint per le Question Templates (gestite nel contesto di un QuizTemplate). """
    serializer_class = QuestionTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        # Filtra per il quiz template specificato nell'URL
        return QuestionTemplate.objects.filter(quiz_template_id=self.kwargs['quiz_template_pk'])

    def perform_create(self, serializer):
        quiz_template = get_object_or_404(QuizTemplate, pk=self.kwargs['quiz_template_pk'])
        serializer.save(quiz_template=quiz_template)

class AnswerOptionTemplateViewSet(viewsets.ModelViewSet):
     """ API endpoint per le Answer Option Templates (gestite nel contesto di una QuestionTemplate). """
     serializer_class = AnswerOptionTemplateSerializer
     permission_classes = [permissions.IsAuthenticated, IsAdminUser]

     def get_queryset(self):
         return AnswerOptionTemplate.objects.filter(question_template_id=self.kwargs['question_template_pk'])

     def perform_create(self, serializer):
         question_template = get_object_or_404(QuestionTemplate, pk=self.kwargs['question_template_pk'])
         serializer.save(question_template=question_template)

# ViewSet per Template Percorsi (simile a QuizTemplateViewSet)
class PathwayTemplateViewSet(viewsets.ModelViewSet):
    """ API endpoint per i Pathway Templates (Docente). """
    serializer_class = PathwayTemplateSerializer
    # Chi può creare/modificare template di percorso? Per ora solo Docenti.
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser] # O aggiungere IsAdminUser?

    def get_queryset(self):
        user = self.request.user
        if isinstance(user, User) and user.is_admin:
            # Se decidiamo che Admin può vedere/gestire tutti i template
            # return PathwayTemplate.objects.all().select_related('teacher')
            # Per ora, Admin non gestisce template percorsi, solo Docenti
             return PathwayTemplate.objects.filter(teacher=user).select_related('teacher') # Admin vede solo i propri? O nessuno?
        elif isinstance(user, User) and user.is_teacher:
            return PathwayTemplate.objects.filter(teacher=user).select_related('teacher')
        return PathwayTemplate.objects.none()

    def perform_create(self, serializer):
        if not isinstance(self.request.user, User) or not self.request.user.is_teacher:
             raise serializers.ValidationError("Solo i Docenti possono creare template di percorsi.")
        serializer.save(teacher=self.request.user)

    @action(detail=True, methods=['get'], url_path='statistics', permission_classes=[permissions.IsAuthenticated, IsTeacherUser])
    def statistics(self, request, pk=None):
        """
        Restituisce statistiche aggregate per un PathwayTemplate specifico.
        """
        template = self.get_object() # Applica permessi e recupera l'oggetto

        # Query per le statistiche aggregate sulle istanze di Pathway generate
        pathway_instances = Pathway.objects.filter(source_template=template)
        stats = pathway_instances.aggregate(
            total_instances_created=Count('id', distinct=True),
            total_assignments=Count('assignments', distinct=True),
            # Conta gli studenti unici che hanno iniziato il percorso (status != NOT_STARTED)
            total_progress_started=Count(
                'progresses__student',
                filter=~models.Q(progresses__status=PathwayProgress.ProgressStatus.NOT_STARTED),
                distinct=True
            ),
            # Conta gli studenti unici che hanno completato il percorso
            total_progress_completed=Count(
                'progresses__student',
                filter=models.Q(progresses__status=PathwayProgress.ProgressStatus.COMPLETED),
                distinct=True
            )
        )

        # Calcola completion rate
        total_started = stats.get('total_progress_started', 0)
        total_completed = stats.get('total_progress_completed', 0)
        completion_rate = (total_completed / total_started * 1.0) if total_started > 0 else None

        # Prepara i dati per il serializer
        data = {
            'template_id': template.id,
            'template_title': template.title,
            'total_instances_created': stats.get('total_instances_created', 0),
            'total_assignments': stats.get('total_assignments', 0),
            'total_progress_started': total_started,
            'total_progress_completed': total_completed,
            'completion_rate': completion_rate,
        }

        serializer = PathwayTemplateStatsSerializer(data)
        return Response(serializer.data)

    # --- Funzioni Helper per Creazione da Template ---
    def _create_pathway_instance_from_template(self, template: PathwayTemplate, teacher: User, title_override: str = None) -> Pathway:
        """
        Crea una nuova istanza di Pathway (con Quiz concreti) a partire da un PathwayTemplate.
        """
        try:
            with transaction.atomic():
                # 1. Crea l'istanza Pathway
                new_pathway = Pathway.objects.create(
                    teacher=teacher,
                    source_template=template,
                    title=title_override or template.title,
                    description=template.description,
                    metadata=template.metadata.copy() if template.metadata else {}
                )

                # 2. Itera sui QuizTemplate del PathwayTemplate
                pathway_quiz_templates = template.pathwayquiztemplate_set.select_related('quiz_template').order_by('order')
                quiz_viewset = QuizViewSet() # Istanza per usare il suo helper
                quiz_viewset.request = self.request # Passa il contesto della richiesta

                pathway_quizzes_to_create = []
                for pqt in pathway_quiz_templates:
                    quiz_template = pqt.quiz_template
                    # 3. Crea istanza Quiz concreta usando l'helper di QuizViewSet
                    # Assicurati che _create_quiz_instance_from_template sia accessibile o spostalo
                    try:
                        new_quiz_instance = quiz_viewset._create_quiz_instance_from_template(
                            template=quiz_template,
                            teacher=teacher # Il docente che assegna è il proprietario del quiz concreto
                        )
                    except Exception as quiz_creation_error:
                         logger.error(f"Errore creazione istanza Quiz da template {quiz_template.id} per pathway {new_pathway.id}: {quiz_creation_error}", exc_info=True)
                         raise quiz_creation_error # Rilancia per far fallire la transazione

                    # 4. Prepara l'oggetto PathwayQuiz per il bulk create
                    pathway_quizzes_to_create.append(
                        PathwayQuiz(
                            pathway=new_pathway,
                            quiz=new_quiz_instance,
                            order=pqt.order
                        )
                    )

                # 5. Crea le relazioni PathwayQuiz in blocco
                if pathway_quizzes_to_create:
                    PathwayQuiz.objects.bulk_create(pathway_quizzes_to_create)

                logger.info(f"Creata istanza Pathway ID {new_pathway.id} da Template ID {template.id} per Docente {teacher.id}")
                return new_pathway
        except Exception as e:
            logger.error(f"Errore atomico durante creazione Pathway da template {template.id}: {e}", exc_info=True)
            raise # Rilancia per far fallire la richiesta API esterna


    @action(detail=True, methods=['post'], url_path='assign-student', permission_classes=[permissions.IsAuthenticated, IsTeacherUser])
    def assign_student_pathway(self, request, pk=None):
        """
        Assegna un Percorso a uno studente, creandolo da questo template.
        Richiede 'student_id' e opzionalmente 'due_date' nel body.
        """
        template = self.get_object() # Recupera il PathwayTemplate
        # Importa i serializer necessari qui dentro per evitare problemi di import circolari
        from .serializers import PathwayAssignActionSerializer, PathwayAssignmentSerializer
        action_serializer = PathwayAssignActionSerializer(data=request.data, context={'request': request})

        if action_serializer.is_valid():
            student = action_serializer.validated_data.get('student')
            due_date = action_serializer.validated_data.get('due_date')

            # Verifica ownership del template (o se è admin) - get_object dovrebbe già farlo con IsTeacherUser?
            # if not request.user.is_admin and template.teacher != request.user:
            #     raise DRFPermissionDenied("Non puoi usare questo template di percorso.")

            # Crea l'istanza Pathway dal template
            try:
                new_pathway_instance = self._create_pathway_instance_from_template(template, request.user)
            except Exception as e:
                logger.error(f"Fallimento creazione Pathway da template {template.id} durante assegnazione a studente {student.id}: {e}", exc_info=True)
                return Response({'detail': f'Errore durante la creazione del percorso dal template: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Verifica se l'assegnazione esiste già per questa *istanza* (improbabile se appena creata, ma per sicurezza)
            existing_assignment = PathwayAssignment.objects.filter(pathway=new_pathway_instance, student=student).first()
            if existing_assignment:
                 logger.warning(f"Tentativo di riassegnare il percorso istanza {new_pathway_instance.id} (da template {template.id}) allo studente {student.id}")
                 # Potremmo aggiornare la due_date o semplicemente restituire l'assegnazione esistente?
                 # Per ora, restituiamo un errore per evitare duplicati impliciti.
                 return Response({'detail': 'Assegnazione già esistente per questa istanza di percorso e studente.'}, status=status.HTTP_409_CONFLICT)
            else:
                # Crea l'assegnazione
                assignment_data = {
                    'pathway': new_pathway_instance.id,
                    'student': student.id,
                    'assigned_by': request.user.id,
                    'due_date': due_date
                }
                assignment_serializer = PathwayAssignmentSerializer(data=assignment_data)
                if assignment_serializer.is_valid():
                    assignment = assignment_serializer.save()
                    logger.info(f"Docente {request.user.id} ha assegnato il percorso {new_pathway_instance.id} (da template {template.id}) allo studente {student.id}")
                    return Response(assignment_serializer.data, status=status.HTTP_201_CREATED)
                else:
                    logger.error(f"Errore validazione PathwayAssignmentSerializer durante assegnazione percorso {new_pathway_instance.id} a studente {student.id}: {assignment_serializer.errors}")
                    # Considerare eliminazione istanza pathway creata se l'assegnazione fallisce?
                    # new_pathway_instance.delete()
                    return Response(assignment_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
             logger.warning(f"Errore validazione PathwayAssignActionSerializer da utente {request.user.id}: {action_serializer.errors}")
             return Response(action_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data)


# ViewSet per gestire le istanze concrete di Pathway (necessario per il frontend e disassegnazione)
class PathwayViewSet(viewsets.ModelViewSet): # Cambiato da ReadOnlyModelViewSet a ModelViewSet
    """
    API endpoint che permette di visualizzare e gestire (limitatamente) i Percorsi concreti.
    - Permette la visualizzazione (list/retrieve).
    - Permette la disassegnazione tramite l'azione 'unassign_student_pathway'.
    La creazione avviene tramite assegnazione da template (PathwayTemplateViewSet).
    """
    queryset = Pathway.objects.all().prefetch_related(
        'quizzes',
        'assignments', # Mantenuto per poter filtrare le assegnazioni
        'progresses'
    )
    serializer_class = PathwaySerializer
    # Permessi più restrittivi: solo admin/docenti possono interagire
    permission_classes = [permissions.IsAuthenticated, IsAdminUser | IsTeacherUser] # Corretto IsTeacher -> IsTeacherUser

    # Limitare azioni a quelle necessarie (list, retrieve, unassign)
    http_method_names = ['get', 'post', 'delete', 'head', 'options'] # Aggiunto 'delete' per l'azione unassign

    def get_queryset(self):
        """
        Filtra i percorsi per docente o admin.
        Mostra solo i percorsi che hanno almeno un'assegnazione attiva.
        """
        user = self.request.user
        base_queryset = Pathway.objects.prefetch_related('quizzes', 'assignments', 'progresses')

        if user.is_staff: # Admin vede tutti i percorsi assegnati
            return base_queryset.filter(assignments__isnull=False).distinct()
        elif getattr(user, 'is_teacher', False): # Docente
            # Mostra solo i percorsi creati da questo docente CHE SONO STATI ASSEGNATI
            return base_queryset.filter(
                teacher=user,
                assignments__isnull=False # Filtra per quelli con almeno un'assegnazione
            ).distinct()
        return Pathway.objects.none() # Altri utenti non vedono nulla

    # Modificata per accettare DELETE e assignment_pk nell'URL
    @action(detail=False, methods=['delete'], url_path=r'unassign-student/(?P<assignment_pk>\d+)', permission_classes=[IsAdminUser | IsTeacherUser])
    def unassign_student_pathway(self, request, assignment_pk=None):
        """
        Disassegna uno studente specifico da un percorso eliminando l'assegnazione.
        Identifica l'assegnazione tramite assignment_pk nell'URL.
        """
        try:
            # Recupera l'assegnazione e il percorso associato per il controllo dei permessi
            assignment = PathwayAssignment.objects.select_related('pathway__teacher', 'student').get(pk=assignment_pk)
        except PathwayAssignment.DoesNotExist:
            return Response({'detail': 'Assegnazione non trovata.'}, status=status.HTTP_404_NOT_FOUND)

        # Verifica permessi: Admin può sempre, Docente solo se è il proprietario del percorso associato
        if not request.user.is_staff and assignment.pathway.teacher != request.user:
             raise DRFPermissionDenied("Non puoi disassegnare studenti da questo percorso.")

        student_id = assignment.student.id
        pathway_id = assignment.pathway.id
        assignment.delete()
        logger.info(f"Docente/Admin {request.user.id} ha disassegnato lo studente {student_id} (Assignment ID: {assignment_pk}) dal percorso {pathway_id}")
        return Response({'detail': 'Studente disassegnato con successo dal percorso.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='assignments', permission_classes=[IsAdminUser | IsTeacherUser])
    def get_assignments(self, request, pk=None):
        """ Recupera l'elenco degli studenti a cui è assegnato questo percorso. """
        # Importa il serializer qui per evitare import circolari
        from .serializers import PathwayAssignmentDetailSerializer
        pathway = self.get_object() # Applica permessi
        assignments = PathwayAssignment.objects.filter(pathway=pathway).select_related('student')

        # Log per debug
        logger.debug(f"[get_assignments - Pathway] Pathway ID: {pathway.id}, Found assignments queryset: {assignments}")

        # Calcola statistiche (opzionale, ma utile)
        # Conta studenti unici che hanno completato il percorso
        completed_count = PathwayProgress.objects.filter(
            pathway=pathway,
            status=PathwayProgress.ProgressStatus.COMPLETED
        ).values('student').distinct().count()

        # Conta studenti unici che hanno iniziato il percorso
        # Conta studenti unici che hanno un record di progresso (quindi hanno iniziato)
        started_count = PathwayProgress.objects.filter(
            pathway=pathway
        ).values('student').distinct().count()


        serializer = PathwayAssignmentDetailSerializer(assignments, many=True)
        logger.debug(f"[get_assignments - Pathway] Serialized data for assignments: {serializer.data}")

        data = {
            'assignments': serializer.data,
            'stats': { # Aggiunge statistiche alla risposta
                 'assigned_count': assignments.count(),
                 'started_count': started_count,
                 'completed_count': completed_count,
            }
        }
        return Response(data)
# Rimosso return errato e indentato

        assignment.delete()
        logger.info(f"Docente/Admin {request.user.id} ha disassegnato lo studente {student_id} dal percorso {pathway.id}")
        return Response({'detail': 'Studente disassegnato con successo dal percorso.'}, status=status.HTTP_204_NO_CONTENT)



# ViewSet per gestire i QuizTemplate dentro un PathwayTemplate (simile a PathwayQuizViewSet)
class PathwayQuizTemplateViewSet(viewsets.ModelViewSet):
    """ API endpoint per gestire i QuizTemplate all'interno di un PathwayTemplate. """
    serializer_class = PathwayQuizTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser] # Solo Docenti proprietari del PathwayTemplate

    def get_queryset(self):
        # Filtra per il pathway template specificato nell'URL
        pathway_template = get_object_or_404(PathwayTemplate, pk=self.kwargs['pathway_template_pk'])
        # Verifica ownership
        if pathway_template.teacher != self.request.user and not self.request.user.is_admin: # Admin può vedere? Per ora no.
             raise DRFPermissionDenied("Non hai accesso a questo template di percorso.")
        return PathwayQuizTemplate.objects.filter(pathway_template=pathway_template).select_related('quiz_template')

    def perform_create(self, serializer):
        pathway_template = get_object_or_404(PathwayTemplate, pk=self.kwargs['pathway_template_pk'])
        if pathway_template.teacher != self.request.user:
             raise DRFPermissionDenied("Non puoi aggiungere quiz a questo template di percorso.")

        quiz_template_id = self.request.data.get('quiz_template_id')
        order = self.request.data.get('order')

        if not quiz_template_id or order is None:
            raise ValidationError({'detail': 'quiz_template_id e order sono richiesti.'})

        quiz_template = get_object_or_404(QuizTemplate, pk=quiz_template_id) # Admin può usare qualsiasi template? Sì.

        try:
            order = int(order)
            if order < 0: raise ValueError()
        except (ValueError, TypeError):
            raise ValidationError({'order': 'L\'ordine deve essere un intero non negativo.'})

        # Verifica ordine esistente
        existing_entry = PathwayQuizTemplate.objects.filter(
            pathway_template=pathway_template,
            order=order
        ).first()
        if existing_entry:
             raise ValidationError({'order': f'L\'ordine {order} è già utilizzato dal template quiz "{existing_entry.quiz_template.title}".'})

        # Verifica se il quiz template è già nel percorso template
        existing_link = PathwayQuizTemplate.objects.filter(
            pathway_template=pathway_template,
            quiz_template=quiz_template
        ).first()
        if existing_link:
             raise ValidationError({'quiz_template_id': 'Questo template di quiz è già presente nel percorso.'})

        serializer.save(pathway_template=pathway_template, quiz_template=quiz_template, order=order)

    # Potrebbe servire un perform_update per gestire il cambio di 'order'
    # Potrebbe servire un perform_destroy per riordinare dopo eliminazione

# --- ViewSet per Docenti (Template Quiz) ---
class TeacherQuizTemplateViewSet(viewsets.ModelViewSet):
    """ API endpoint per i Quiz Templates gestiti dai Docenti. """
    serializer_class = QuizTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser] # Solo Docenti

    def get_queryset(self):
        """ Filtra i template per mostrare solo quelli creati dal docente loggato. """
        user = self.request.user
        # Assicurati che l'utente sia un docente
        if isinstance(user, User) and user.is_teacher:
            return QuizTemplate.objects.filter(teacher=user)
        return QuizTemplate.objects.none() # Restituisce vuoto se non è un docente

    def perform_create(self, serializer):
        """ Associa automaticamente il docente creatore. """
        # Non è necessario controllare di nuovo il ruolo qui perché IsTeacherUser lo fa già
        serializer.save(teacher=self.request.user)

    # Le azioni per QuestionTemplate e AnswerOptionTemplate devono essere gestite
    # tramite router annidati specifici per questo ViewSet se necessario,
    # oppure si può decidere che la gestione delle domande avvenga solo
    # dopo la creazione del template, modificando il template esistente.

    @action(detail=False, methods=['post'], url_path='upload', permission_classes=[permissions.IsAuthenticated, IsTeacherUser], parser_classes=[parsers.MultiPartParser, parsers.FormParser])
    def upload_template(self, request, *args, **kwargs):
        """
        Permette a un docente di caricare un file (PDF, DOCX, MD) per creare un QuizTemplate.
        Richiede 'file' e 'title' nei dati della richiesta (form-data).
        """
        # Importa il nuovo serializer qui o all'inizio del file
        from .serializers import QuizTemplateUploadSerializer

        serializer = QuizTemplateUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                # Il metodo create del serializer gestisce l'estrazione, il parsing e la creazione del template
                template_data = serializer.save() # .save() chiama .create()
                # Restituisce i dati del template creato (formattati da QuizTemplateSerializer dentro QuizTemplateUploadSerializer)
                return Response(template_data, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                # Se il serializer.create solleva ValidationError (es. parsing fallito, testo vuoto)
                logger.warning(f"Errore di validazione durante upload template da utente {request.user.id}: {e.detail}")
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                # Cattura altri errori imprevisti durante la creazione
                logger.error(f"Errore imprevisto durante l'upload del template da utente {request.user.id}: {e}", exc_info=True)
                return Response({"detail": "Errore interno durante la creazione del template dal file."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Errori di validazione del serializer (es. file mancante, titolo mancante, tipo file errato)
            logger.warning(f"Errore di validazione dati upload template da utente {request.user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='statistics', permission_classes=[permissions.IsAuthenticated, IsTeacherUser])
    def statistics(self, request, pk=None):
        """
        Restituisce statistiche aggregate per un QuizTemplate specifico.
        """
        template = self.get_object() # get_object applica i permessi e get_queryset

        # Calcola le statistiche aggregando sui Quiz generati dal template
        stats = Quiz.objects.filter(source_template=template).aggregate(
            total_instances_created=Count('id', distinct=True), # Conta le istanze uniche di Quiz
            total_assignments=Count('assignments', distinct=True), # Conta le assegnazioni uniche
            total_attempts=Count('attempts', distinct=True),       # Conta i tentativi unici
            # Media punteggi sui tentativi completati
            average_score=Avg(
                'attempts__score',
                filter=models.Q(attempts__status=QuizAttempt.AttemptStatus.COMPLETED)
            ),
            # Conteggio tentativi completati
            completed_attempts=Count(
                'attempts',
                filter=models.Q(attempts__status=QuizAttempt.AttemptStatus.COMPLETED),
                distinct=True
            )
        )

        # Calcola completion rate (evita divisione per zero)
        total_attempts = stats.get('total_attempts', 0)
        completed_attempts = stats.get('completed_attempts', 0)
        completion_rate = (completed_attempts / total_attempts * 1.0) if total_attempts > 0 else None

        # Prepara i dati per il serializer
        data = {
            'template_id': template.id,
            'template_title': template.title,
            'total_instances_created': stats.get('total_instances_created', 0),
            'total_assignments': stats.get('total_assignments', 0),
            'total_attempts': total_attempts,
            'average_score': stats.get('average_score'),
            'completion_rate': completion_rate,
        }

        serializer = QuizTemplateStatsSerializer(data)
        return Response(serializer.data)

# --- ViewSets Nidificati per Docenti (Gestione Domande/Opzioni Template Quiz) ---

class TeacherQuestionTemplateViewSet(viewsets.ModelViewSet): # Aggiunta azione question_ids
    """ API endpoint per le Question Templates gestite da Docenti nel contesto di un loro QuizTemplate. """
    serializer_class = QuestionTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser] # Solo Docenti

    def get_queryset(self):
        """ Filtra le domande per il template specificato e verifica ownership. """
        quiz_template = get_object_or_404(QuizTemplate, pk=self.kwargs['quiz_template_pk'])
        # Verifica che il docente loggato sia il proprietario del template
        if quiz_template.teacher != self.request.user:
             raise DRFPermissionDenied("Non hai accesso a questo template di quiz.")
        return QuestionTemplate.objects.filter(quiz_template=quiz_template).order_by('order')

    def perform_create(self, serializer):
        """ Associa la domanda al template corretto e calcola l'ordine. """
        quiz_template = get_object_or_404(QuizTemplate, pk=self.kwargs['quiz_template_pk'])
        if quiz_template.teacher != self.request.user:
             raise DRFPermissionDenied("Non puoi aggiungere domande a questo template di quiz.")
        # Calcola il prossimo ordine disponibile
        last_order = QuestionTemplate.objects.filter(quiz_template=quiz_template).aggregate(Max('order'))['order__max']
        next_order = 0 if last_order is None else last_order + 1 # Ordine 0-based
        serializer.save(quiz_template=quiz_template, order=next_order)

    @transaction.atomic
    def perform_destroy(self, instance):
        """ Elimina la domanda template e riordina le successive. """
        quiz_template = instance.quiz_template
        # Verifica ownership prima di eliminare (doppio controllo)
        if quiz_template.teacher != self.request.user:
             raise DRFPermissionDenied("Non puoi eliminare domande da questo template di quiz.")

        deleted_order = instance.order
        instance.delete()

        # Riordina le domande template successive
        questions_to_reorder = QuestionTemplate.objects.filter(
            quiz_template=quiz_template,
            order__gt=deleted_order
        ).order_by('order')
        updated_count = questions_to_reorder.update(order=F('order') - 1)
        logger.info(f"Riordinate {updated_count} domande nel template quiz {quiz_template.id} dopo eliminazione ordine {deleted_order}.")

    # Modificato: detail=False perché l'azione opera sul template (tramite quiz_template_pk), non su una singola domanda (pk)
    @action(detail=False, methods=['get'], url_path='question-ids', permission_classes=[permissions.IsAuthenticated, IsTeacherUser])
    def question_ids(self, request, quiz_template_pk=None): # Rimosso pk non necessario
        """
        Restituisce un elenco ordinato degli ID delle domande template
        per il template quiz specificato (quiz_template_pk).
        Utile per la navigazione sequenziale nel frontend.
        """
        quiz_template = get_object_or_404(QuizTemplate, pk=quiz_template_pk)
        # Verifica ownership
        if quiz_template.teacher != self.request.user:
             raise DRFPermissionDenied("Non hai accesso a questo template di quiz.")

        # Recupera gli ID ordinati
        ordered_ids = list(QuestionTemplate.objects.filter(quiz_template=quiz_template)
                                                .order_by('order')
                                                .values_list('id', flat=True))

        return Response(ordered_ids, status=status.HTTP_200_OK)


class TeacherAnswerOptionTemplateViewSet(viewsets.ModelViewSet):
     """ API endpoint per le Answer Option Templates gestite da Docenti. """
     serializer_class = AnswerOptionTemplateSerializer
     permission_classes = [permissions.IsAuthenticated, IsTeacherUser] # Solo Docenti

     def get_queryset(self):
         """ Filtra le opzioni per la domanda template specificata e verifica ownership. """
         question_template = get_object_or_404(QuestionTemplate, pk=self.kwargs['question_template_pk'])
         # Verifica ownership tramite il quiz template padre
         if question_template.quiz_template.teacher != self.request.user:
              raise DRFPermissionDenied("Non hai accesso a questa domanda template.")
         return AnswerOptionTemplate.objects.filter(question_template=question_template).order_by('order')

     def perform_create(self, serializer):
         """ Associa l'opzione alla domanda template corretta e calcola l'ordine. """
         question_template = get_object_or_404(QuestionTemplate, pk=self.kwargs['question_template_pk'])
         if question_template.quiz_template.teacher != self.request.user:
              raise DRFPermissionDenied("Non puoi aggiungere opzioni a questa domanda template.")
         # Calcola il prossimo ordine disponibile
         last_order = AnswerOptionTemplate.objects.filter(question_template=question_template).aggregate(Max('order'))['order__max']
         next_order = 1 if last_order is None else last_order + 1
         serializer.save(question_template=question_template, order=next_order)

     def perform_destroy(self, instance):
         """ Elimina l'opzione template. """
         # Verifica ownership prima di eliminare
         if instance.question_template.quiz_template.teacher != self.request.user:
              raise DRFPermissionDenied("Non puoi eliminare opzioni da questa domanda template.")
         instance.delete()





# --- ViewSets per Docenti (Contenuti Concreti) ---
class QuizViewSet(viewsets.ModelViewSet):
    """ API endpoint per i Quiz concreti (Docente). """
    serializer_class = QuizSerializer
    # Modificato: Usiamo permessi più generali a livello di ViewSet.
    # IsAuthenticated garantisce che l'utente sia loggato.
    # (IsTeacherUser | IsAdminUser) garantisce che sia un docente o un admin.
    # La logica di get_queryset e i permessi a livello di oggetto (controllati da DRF per retrieve/update/delete)
    # gestiranno l'accesso specifico ai dati.
    # Usiamo IsQuizOwnerOrAdmin per gestire l'accesso a livello di oggetto
    permission_classes = [permissions.IsAuthenticated, IsQuizOwnerOrAdmin]

    def get_queryset(self):
        """
        Filtra i quiz: l'admin vede tutto, il docente vede solo i propri.
        IsQuizOwnerOrAdmin gestirà l'accesso specifico per retrieve/update/delete.
        """
        user = self.request.user

        if isinstance(user, User) and user.is_admin:
            # Admin vede tutto
            return Quiz.objects.all().select_related('teacher')
        elif isinstance(user, User) and user.is_teacher: # Manteniamo user.is_teacher se è corretto nel contesto
            # Docente vede solo i propri quiz
            # Docente vede solo i propri quiz CHE SONO STATI ASSEGNATI almeno una volta
            # Usiamo assignments__isnull=False per filtrare e distinct() per evitare duplicati
            # se un quiz è assegnato a più studenti.
            return Quiz.objects.filter(
                teacher=user,
                assignments__isnull=False # Filtra per quelli con almeno un'assegnazione
            ).select_related('teacher').distinct()
        # Altri tipi di utenti (es. Studente) non dovrebbero poter accedere a questa view
        # a causa dei permessi, ma per sicurezza restituiamo un queryset vuoto.
        return Quiz.objects.none()

    def perform_create(self, serializer):
        if not isinstance(self.request.user, User) or not self.request.user.is_teacher:
             raise serializers.ValidationError("Solo i Docenti possono creare quiz.")
        serializer.save(teacher=self.request.user)

    # --- Funzioni Helper per Creazione da Template ---
    def _create_quiz_instance_from_template(self, template: QuizTemplate, teacher: User, title_override: str = None) -> Quiz:
        """
        Crea una nuova istanza di Quiz (con domande e opzioni) a partire da un QuizTemplate.
        """
        try:
            with transaction.atomic():
                new_quiz = Quiz.objects.create(
                    teacher=teacher,
                    source_template=template,
                    title=title_override or template.title, # Usa override se fornito
                    description=template.description,
                    # Copia i metadati, ma potremmo volerli modificare/filtrare
                    metadata=template.metadata.copy() if template.metadata else {}
                )
                questions_to_create = []
                options_to_create_map = {} # Mappa: q_template.id -> lista di opzioni da creare

                question_order_counter = 0 # Inizializza contatore ordine a 0 PRIMA del ciclo
                for q_template in template.question_templates.prefetch_related('answer_option_templates').order_by('order'):
                    new_question = Question(
                        quiz=new_quiz,
                        text=q_template.text,
                        question_type=q_template.question_type,
                        order=question_order_counter, # Assegna ordine sequenziale 0-based
                        metadata=q_template.metadata.copy() if q_template.metadata else {}
                    )
                    questions_to_create.append(new_question)
                    question_order_counter += 1 # Incrementa contatore per la prossima domanda
                    # Prepara le opzioni per il bulk create dopo aver creato le domande
                    options_to_create_map[q_template.id] = []
                    for opt_template in q_template.answer_option_templates.order_by('order'):
                         options_to_create_map[q_template.id].append(
                             AnswerOption(
                                 # question sarà impostato dopo la creazione delle domande
                                 text=opt_template.text,
                                 is_correct=opt_template.is_correct,
                                 order=opt_template.order
                             )
                         )

                # Crea le domande in blocco
                created_questions = Question.objects.bulk_create(questions_to_create)

                # Mappa per recuperare le domande create e associare le opzioni
                created_question_map = {q.order: q for q in created_questions}
                options_final_list = []

                # Associa le opzioni alle domande appena create
                for q_template_id, options_list in options_to_create_map.items():
                    # Trova la domanda corrispondente basandosi sull'ordine (assumendo che l'ordine sia preservato)
                    # Questo è un punto debole se l'ordine non è garantito o unico durante la creazione.
                    # Un approccio più robusto potrebbe usare un identificatore temporaneo.
                    q_template_order = QuestionTemplate.objects.get(id=q_template_id).order # Recupera l'ordine originale
                    newly_created_question = created_question_map.get(q_template_order)

                    if newly_created_question:
                        for option in options_list:
                            option.question = newly_created_question
                            options_final_list.append(option)
                    else:
                         logger.warning(f"Impossibile trovare la domanda creata corrispondente al template Q ID {q_template_id} per il quiz {new_quiz.id}")


                # Crea le opzioni in blocco
                if options_final_list:
                    AnswerOption.objects.bulk_create(options_final_list)

                logger.info(f"Creata istanza Quiz ID {new_quiz.id} da Template ID {template.id} per Docente {teacher.id}")
                return new_quiz
        except Exception as e:
            logger.error(f"Errore atomico durante creazione Quiz da template {template.id}: {e}", exc_info=True)
            # Rilancia l'eccezione per far fallire la richiesta API esterna
            raise


    # L'azione create_from_template ora usa l'helper
    @action(detail=False, methods=['post'], url_path='create-from-template', permission_classes=[permissions.IsAuthenticated, IsTeacherUser])
    def create_from_template(self, request):
        template_id = request.data.get('template_id')
        title_override = request.data.get('title') # Titolo opzionale per l'istanza

        if not template_id:
            return Response({'template_id': 'Questo campo è richiesto.'}, status=status.HTTP_400_BAD_REQUEST)

        template = get_object_or_404(QuizTemplate, pk=template_id)

        try:
            new_quiz = self._create_quiz_instance_from_template(template, request.user, title_override)
            serializer = self.get_serializer(new_quiz)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # L'helper ora rilancia l'eccezione
            logger.error(f"Fallimento creazione Quiz da template {template_id} per utente {request.user.id}: {e}", exc_info=True)
            return Response({'detail': f'Errore durante la creazione da template: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # --- Azioni Specifiche Docente ---

    @action(detail=False, methods=['post'], url_path='upload', permission_classes=[permissions.IsAuthenticated, IsTeacherUser], parser_classes=[parsers.MultiPartParser, parsers.FormParser])
    def upload_quiz(self, request, *args, **kwargs):
        """
        Permette a un docente di caricare un file (PDF, DOCX, MD) per creare un quiz.
        Richiede 'file' e 'title' nei dati della richiesta (form-data).
        """
        serializer = QuizUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                # Il metodo create del serializer gestisce l'estrazione, il parsing e la creazione
                quiz_data = serializer.save() # .save() chiama .create()
                # Restituisce i dati del quiz creato (formattati da QuizSerializer dentro QuizUploadSerializer)
                return Response(quiz_data, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                # Se il serializer.create solleva ValidationError (es. parsing fallito, testo vuoto)
                logger.warning(f"Errore di validazione durante upload quiz da utente {request.user.id}: {e.detail}")
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                # Cattura altri errori imprevisti durante la creazione
                logger.error(f"Errore imprevisto durante l'upload del quiz da utente {request.user.id}: {e}", exc_info=True)
                return Response({"detail": "Errore interno durante la creazione del quiz dal file."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Errori di validazione del serializer (es. file mancante, titolo mancante, tipo file errato)
            logger.warning(f"Errore di validazione dati upload quiz da utente {request.user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Modificata per usare QuizAssignmentSerializer e gestire creazione da template
    @action(detail=False, methods=['post'], url_path='assign-student', permission_classes=[permissions.IsAuthenticated, IsTeacherUser])
    def assign_student(self, request):
        """Assegna un Quiz a uno studente, creandolo da un template."""
        # Usa il serializer specifico per l'azione di assegnazione da template
        from .serializers import QuizAssignActionSerializer, QuizAssignmentSerializer # Importa entrambi
        action_serializer = QuizAssignActionSerializer(data=request.data, context={'request': request})

        if action_serializer.is_valid():
            quiz_template_id = action_serializer.validated_data.get('quiz_template_id')
            student = action_serializer.validated_data.get('student')
            due_date = action_serializer.validated_data.get('due_date')

            quiz_to_assign = None
            template = get_object_or_404(QuizTemplate, pk=quiz_template_id)

            # Verifica ownership del template (o se è admin)
            if not request.user.is_admin and template.teacher != request.user and template.admin != request.user:
                raise DRFPermissionDenied("Non puoi usare questo template di quiz.")

            # Crea l'istanza Quiz dal template
            try:
                quiz_to_assign = self._create_quiz_instance_from_template(template, request.user)
            except Exception as e:
                logger.error(f"Fallimento creazione Quiz da template {quiz_template_id} durante assegnazione a studente {student.id}: {e}", exc_info=True)
                return Response({'detail': f'Errore durante la creazione del quiz dal template: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Verifica se l'assegnazione esiste già
            existing_assignment = QuizAssignment.objects.filter(quiz=quiz_to_assign, student=student).first()
            if existing_assignment:
                # Se esiste già, potremmo aggiornare la due_date o restituire un errore/successo specifico
                pass # Aggiunto per risolvere IndentationError
            # Se l'assegnazione non esiste, creala
            else:
                assignment_data = {
                    'quiz': quiz_to_assign.id,
                    'student': student.id,
                    'assigned_by': request.user.id,
                    'due_date': due_date
                }
                # Usa QuizAssignmentSerializer per creare l'assegnazione
                assignment_serializer = QuizAssignmentSerializer(data=assignment_data)
                if assignment_serializer.is_valid():
                    assignment = assignment_serializer.save()
                    logger.info(f"Docente {request.user.id} ha assegnato il quiz {quiz_to_assign.id} (da template {quiz_template_id}) allo studente {student.id}")
                    return Response(assignment_serializer.data, status=status.HTTP_201_CREATED)
                else:
                    logger.error(f"Errore validazione QuizAssignmentSerializer durante assegnazione quiz {quiz_to_assign.id} a studente {student.id}: {assignment_serializer.errors}")
                    # Se la creazione dell'assegnazione fallisce dopo aver creato il quiz,
                    # potremmo voler eliminare il quiz appena creato per evitare istanze orfane?
                    # quiz_to_assign.delete() # Considerare questa opzione
                    return Response(assignment_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
             # Se action_serializer non è valido
             logger.warning(f"Errore validazione QuizAssignActionSerializer da utente {request.user.id}: {action_serializer.errors}")
             return Response(action_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Modificata per accettare DELETE e assignment_pk nell'URL
    @action(detail=False, methods=['delete'], url_path=r'unassign-student/(?P<assignment_pk>\d+)', permission_classes=[IsAdminUser | IsTeacherUser])
    def unassign_student(self, request, assignment_pk=None):
        """
        Disassegna uno studente specifico da un quiz eliminando l'assegnazione.
        Identifica l'assegnazione tramite assignment_pk nell'URL.
        """
        try:
            # Recupera l'assegnazione e il quiz associato per il controllo dei permessi
            assignment = QuizAssignment.objects.select_related('quiz__teacher', 'student').get(pk=assignment_pk)
        except QuizAssignment.DoesNotExist:
            return Response({'detail': 'Assegnazione non trovata.'}, status=status.HTTP_404_NOT_FOUND)

        # Verifica permessi: Admin può sempre, Docente solo se è il proprietario del quiz associato
        # Nota: IsTeacherUser nei permission_classes dell'action garantisce che sia un docente o admin
        if not request.user.is_staff and assignment.quiz.teacher != request.user:
             raise DRFPermissionDenied("Non puoi disassegnare studenti da questo quiz.")

        student_id = assignment.student.id
        quiz_id = assignment.quiz.id
        assignment.delete()
        logger.info(f"Docente/Admin {request.user.id} ha disassegnato lo studente {student_id} (Assignment ID: {assignment_pk}) dal quiz {quiz_id}")
        return Response({'detail': 'Studente disassegnato con successo dal quiz.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='assignments', permission_classes=[IsAdminUser | IsTeacherUser])
    def get_assignments(self, request, pk=None):
        """
        Recupera l'elenco degli studenti a cui è assegnato questo quiz.
        Gestisce il caso in cui il quiz potrebbe non avere più assegnazioni.
        """
        # Recupera il quiz direttamente per evitare il filtro del get_queryset
        try:
            quiz = Quiz.objects.select_related('teacher').get(pk=pk)
        except Quiz.DoesNotExist:
            return Response({'detail': 'Quiz non trovato.'}, status=status.HTTP_404_NOT_FOUND)

        # Applica manualmente i permessi a livello di oggetto
        self.check_object_permissions(request, quiz)

        assignments = QuizAssignment.objects.filter(quiz=quiz).select_related('student')

        # Calcola quanti hanno completato (con successo)
        completion_threshold = quiz.metadata.get('completion_threshold', 100)
        max_score = quiz.get_max_possible_score()
        required_score = (completion_threshold / 100.0) * max_score if max_score > 0 else 0

        completed_count = QuizAttempt.objects.filter(
            quiz=quiz,
            status=QuizAttempt.AttemptStatus.COMPLETED,
            score__gte=required_score
        ).values('student').distinct().count()

        logger.debug(f"[get_assignments] Quiz ID: {quiz.id}, Found assignments queryset: {assignments}")
        serializer = QuizAssignmentDetailSerializer(assignments, many=True)
        logger.debug(f"[get_assignments] Serialized data for assignments: {serializer.data}")
        data = {
            'assignments': serializer.data,
            'total_assigned': assignments.count(), # Questo sarà 0 se non ci sono assegnazioni
            'total_completed': completed_count,
        }
        # Restituisce 200 OK anche se 'assignments' è vuoto
        return Response(data)


    @action(detail=True, methods=['delete'], url_path='remove-quiz/(?P<pathway_quiz_pk>[^/.]+)', permission_classes=[permissions.IsAuthenticated, IsPathwayOwnerOrAdmin])
    def remove_quiz(self, request, pk=None, pathway_quiz_pk=None):
        """ Rimuove un Quiz da un Percorso e riordina quelli successivi. """
        pathway = self.get_object() # Verifica permesso sul percorso

        try:
            pathway_quiz_entry = get_object_or_404(
                PathwayQuiz,
                pk=pathway_quiz_pk,
                pathway=pathway # Assicura che l'entry appartenga al percorso corretto
            )

            deleted_order = pathway_quiz_entry.order
            quiz_title = pathway_quiz_entry.quiz.title
            pathway_quiz_entry.delete()

            # Riordina i quiz successivi nello stesso percorso
            quizzes_to_reorder = PathwayQuiz.objects.filter(
                pathway=pathway,
                order__gt=deleted_order
            ).order_by('order')

            with transaction.atomic():
                for i, entry in enumerate(quizzes_to_reorder):
                    entry.order = deleted_order + i # Ricalcola ordine sequenziale
                    entry.save(update_fields=['order'])

            logger.info(f"Rimosso quiz '{quiz_title}' dal percorso {pathway.id} e riordinati {quizzes_to_reorder.count()} quiz successivi.")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            return Response({'detail': 'Quiz non trovato in questo percorso.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
             logger.error(f"Errore durante rimozione quiz {pathway_quiz_pk} da percorso {pk}: {e}", exc_info=True)
             return Response({'detail': 'Errore interno durante la rimozione del quiz.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- ViewSets per Studenti ---

class StudentDashboardViewSet(viewsets.ViewSet):
     """ Endpoint per lo studente per vedere cosa gli è stato assegnato. """
     permission_classes = [permissions.IsAuthenticated, IsStudentAuthenticated] # Usa il permesso specifico

     def list(self, request):
         student = request.user # Ora request.user è l'istanza Student grazie al middleware/auth backend

         # Recupera Quiz assegnati non ancora completati o falliti (se possono essere ritentati)
         assigned_quizzes = QuizAssignment.objects.filter(
             student=student
         ).select_related('quiz', 'quiz__teacher')\
          .exclude(quiz__attempts__student=student, quiz__attempts__status__in=[QuizAttempt.AttemptStatus.COMPLETED, QuizAttempt.AttemptStatus.FAILED]) # Escludi se c'è un tentativo COMPLETED o FAILED
          # TODO: Aggiungere logica per tentativi multipli se implementata

         # Recupera Percorsi assegnati non ancora completati
         assigned_pathways = PathwayAssignment.objects.filter(
             student=student
         ).select_related('pathway', 'pathway__teacher')\
          .exclude(pathway__progresses__student=student, pathway__progresses__status=PathwayProgress.ProgressStatus.COMPLETED)

         # Annotazione per l'ultimo tentativo/progresso (potrebbe essere ottimizzata)
         # Nota: Questa logica è complessa e potrebbe essere spostata in manager custom o servizi
         latest_quiz_attempt = QuizAttempt.objects.filter(
             quiz=OuterRef('quiz_id'), student=student
         ).order_by('-start_time')
         assigned_quizzes = assigned_quizzes.annotate(
             latest_attempt_data=Subquery(latest_quiz_attempt.values('pk')[:1]) # Subquery per ID ultimo tentativo
         )
         # Recupera gli oggetti QuizAttempt effettivi basati sugli ID
         latest_attempt_ids = [a.latest_attempt_data for a in assigned_quizzes if a.latest_attempt_data]
         latest_attempts_dict = {a.id: a for a in QuizAttempt.objects.filter(pk__in=latest_attempt_ids)}

         latest_pathway_progress = PathwayProgress.objects.filter(
             pathway=OuterRef('pathway_id'), student=student
         ).order_by('-start_time')
         assigned_pathways = assigned_pathways.annotate(
             latest_progress_data=Subquery(latest_pathway_progress.values('pk')[:1])
         )
         latest_progress_ids = [p.latest_progress_data for p in assigned_pathways if p.latest_progress_data]
         latest_progress_dict = {p.id: p for p in PathwayProgress.objects.filter(pk__in=latest_progress_ids)}


         # Serializza i dati passando l'ultimo tentativo/progresso nel contesto o direttamente
         # Questo approccio con subquery e recupero separato è un po' macchinoso.
         # Un approccio alternativo è usare SerializerMethodField nei serializer Dashboard.

         quiz_serializer = StudentQuizDashboardSerializer(
             [a.quiz for a in assigned_quizzes], # Passa gli oggetti Quiz
             many=True,
             context={'request': request, 'latest_attempts': latest_attempts_dict} # Passa i tentativi nel contesto
         )
         pathway_serializer = StudentPathwayDashboardSerializer(
             [p.pathway for p in assigned_pathways], # Passa gli oggetti Pathway
             many=True,
             context={'request': request, 'latest_progress': latest_progress_dict} # Passa i progressi nel contesto
         )

         return Response({
             'assigned_quizzes': quiz_serializer.data,
             'assigned_pathways': pathway_serializer.data
         })


class StudentQuizAttemptViewSet(viewsets.GenericViewSet):
    """ Gestisce l'inizio di un Quiz da parte dello Studente (spostato da QuizViewSet). """
    permission_classes = [permissions.IsAuthenticated, IsStudentAuthenticated]
    serializer_class = QuizAttemptSerializer # Serializer di default

    # Azione per iniziare un nuovo tentativo
    @action(detail=False, methods=['post'], url_path='start-attempt') # Impostato detail=False, agisce sulla collezione per un quiz
    def start_attempt(self, request, pk=None): # pk ora è quiz_pk
         quiz = get_object_or_404(Quiz, pk=pk)
         student = request.user # Assicurato da IsStudentAuthenticated

         # 1. Verifica Assegnazione (Quiz singolo o tramite Percorso)
         is_assigned_directly = QuizAssignment.objects.filter(quiz=quiz, student=student).exists()
         # Verifica se il quiz fa parte di un percorso assegnato allo studente
         is_in_assigned_pathway = Pathway.objects.filter(
             pathwayquiz__quiz=quiz, # Il quiz è in un PathwayQuiz...
             assignments__student=student # ...e quel Pathway è assegnato allo studente
         ).exists()

         if not is_assigned_directly and not is_in_assigned_pathway:
              logger.warning(f"Studente {student.id} ha tentato di iniziare il quiz {quiz.id} non assegnato.")
              raise DRFPermissionDenied("Non sei autorizzato a iniziare questo quiz.")

         # 2. Verifica Disponibilità Temporale (se impostata)
         now = timezone.now()
         if quiz.available_from and now < quiz.available_from:
             raise ValidationError("Questo quiz non è ancora disponibile.")
         if quiz.available_until and now > quiz.available_until:
             raise ValidationError("Questo quiz non è più disponibile.")

         # 3. Verifica Tentativi Precedenti (Logica tentativi multipli non implementata)
         existing_attempt = QuizAttempt.objects.filter(
             quiz=quiz,
             student=student,
             status__in=[QuizAttempt.AttemptStatus.IN_PROGRESS, QuizAttempt.AttemptStatus.COMPLETED, QuizAttempt.AttemptStatus.FAILED]
         ).first()
         if existing_attempt:
              # Se esiste già un tentativo (in corso, completato o fallito), non permettere di iniziarne un altro
              # TODO: Gestire logica tentativi multipli se necessaria
              logger.warning(f"Studente {student.id} ha tentato di iniziare nuovamente il quiz {quiz.id} (tentativo esistente: {existing_attempt.id})")
              return Response({'detail': 'Hai già iniziato o completato questo quiz.'}, status=status.HTTP_400_BAD_REQUEST)

         # 4. Crea il nuovo tentativo
         try:
             with transaction.atomic(): # Assicura atomicità
                 attempt = QuizAttempt.objects.create(quiz=quiz, student=student)
                 # Crea StudentAnswer vuoti per ogni domanda (opzionale, ma utile per tracciare)
                 # questions = quiz.questions.all()
                 # StudentAnswer.objects.bulk_create([
                 #     StudentAnswer(quiz_attempt=attempt, question=q) for q in questions
                 # ])
                 logger.info(f"Studente {student.id} ha iniziato il tentativo {attempt.id} per il quiz {quiz.id}")
                 serializer = self.get_serializer(attempt)
                 return Response(serializer.data, status=status.HTTP_201_CREATED)
         except Exception as e:
              logger.error(f"Errore durante la creazione del tentativo per quiz {quiz.id}, studente {student.id}: {e}", exc_info=True)
              return Response({'detail': 'Errore interno durante l\'inizio del tentativo.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AttemptViewSet(viewsets.GenericViewSet):
    """ Gestisce le azioni su un tentativo di quiz specifico (submit, complete). """
    queryset = QuizAttempt.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsStudentOwnerForAttempt] # Solo lo studente proprietario

    def get_serializer_class(self):
        if self.action == 'details':
            return QuizAttemptDetailSerializer
        # Altre azioni potrebbero usare serializer specifici o nessuno
        return QuizAttemptSerializer # Default

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """ Restituisce i dettagli completi di un tentativo, incluse le risposte. """
        attempt = self.get_object() # Applica IsStudentOwnerForAttempt
        serializer = self.get_serializer(attempt)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='current-question')
    def current_question(self, request, pk=None):
        """ Restituisce la prossima domanda non risposta per il tentativo specificato. """
        attempt = self.get_object()
        if attempt.status != QuizAttempt.AttemptStatus.IN_PROGRESS:
            return Response({'detail': 'Questo tentativo non è in corso.'}, status=status.HTTP_400_BAD_REQUEST)

        answered_question_ids = StudentAnswer.objects.filter(quiz_attempt=attempt).values_list('question_id', flat=True)
        next_question = Question.objects.filter(
            quiz=attempt.quiz
        ).exclude(
            id__in=answered_question_ids
        ).order_by('order').first()

        if next_question:
            # Serializza la domanda (senza la risposta corretta)
            serializer = QuestionSerializer(next_question, context={'request': request})
            # Rimuovi 'is_correct' dalle opzioni prima di inviare
            data = serializer.data
            if 'answer_options' in data:
                 for option in data['answer_options']:
                     option.pop('is_correct', None)
            return Response(data)
        else:
            # Nessuna domanda successiva, il quiz dovrebbe essere completato
            return Response({'detail': 'Tutte le domande sono state risposte.'}, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'], url_path='submit-answer')
    def submit_answer(self, request, pk=None):
        """
        Invia la risposta dello studente per una specifica domanda del tentativo.
        Calcola subito il punteggio se la domanda è a correzione automatica.
        """
        attempt = self.get_object()
        if attempt.status != QuizAttempt.AttemptStatus.IN_PROGRESS:
            return Response({'detail': 'Questo tentativo non è in corso.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = StudentAnswerSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            question_id = serializer.validated_data['question'].id
            question = get_object_or_404(Question, pk=question_id, quiz=attempt.quiz) # Assicura che la domanda sia del quiz giusto

            # Verifica se è già stata data una risposta per questa domanda nel tentativo
            if StudentAnswer.objects.filter(quiz_attempt=attempt, question=question).exists():
                return Response({'detail': 'Hai già risposto a questa domanda.'}, status=status.HTTP_400_BAD_REQUEST)

            student_answer: StudentAnswer = serializer.save(quiz_attempt=attempt)

            # Calcola punteggio e correttezza per tipi auto-correggibili
            points_awarded = 0
            is_correct = None # Null per manuale, True/False per automatico

            if question.question_type in [QuestionType.MULTIPLE_CHOICE_SINGLE, QuestionType.TRUE_FALSE]:
                correct_option = question.answer_options.filter(is_correct=True).first()
                selected_option_id = serializer.validated_data.get('selected_options', [None])[0] # Prende il primo ID
                is_correct = (correct_option is not None and selected_option_id == correct_option.id)
                if is_correct:
                    points_awarded = question.metadata.get('points', 1) # Default a 1 punto

            elif question.question_type == QuestionType.MULTIPLE_CHOICE_MULTIPLE:
                correct_option_ids = set(question.answer_options.filter(is_correct=True).values_list('id', flat=True))
                selected_option_ids = set(serializer.validated_data.get('selected_options', []))
                is_correct = (correct_option_ids == selected_option_ids) # Devono corrispondere esattamente
                if is_correct:
                    points_awarded = question.metadata.get('points', 1)

            elif question.question_type == QuestionType.FILL_BLANK:
                correct_answers = [ans.strip().lower() for ans in question.metadata.get('correct_answers', []) if ans]
                submitted_answer = serializer.validated_data.get('answer_text', '').strip().lower()
                is_correct = submitted_answer in correct_answers
                if is_correct:
                    points_awarded = question.metadata.get('points', 1)

            elif question.question_type == QuestionType.OPEN_ANSWER_MANUAL:
                # Lascia is_correct=None e points_awarded=0, verranno impostati dal docente
                is_correct = None
                points_awarded = 0
            else:
                 logger.error(f"Tipo domanda non gestito {question.question_type} per domanda {question.id}")
                 # Considera cosa fare qui, forse sollevare un errore?

            # Aggiorna la risposta dello studente
            student_answer.is_correct = is_correct
            student_answer.points_awarded = points_awarded
            student_answer.save()

            # Restituisci la risposta salvata (o solo un successo?)
            response_serializer = StudentAnswerSerializer(student_answer)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['post'], url_path='complete')
    def complete_attempt(self, request, pk=None):
        """
        Marca un tentativo come completato dallo studente.
        Calcola il punteggio finale se tutte le domande sono auto-correggibili.
        Altrimenti, imposta lo stato a PENDING_GRADING.
        Assegna punti al wallet e badge.
        """
        attempt = self.get_object()
        if attempt.status != QuizAttempt.AttemptStatus.IN_PROGRESS:
            return Response({'detail': 'Questo tentativo non è in corso o è già stato completato.'}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        attempt.end_time = now

        # Verifica se ci sono risposte manuali non ancora valutate
        has_pending_manual = attempt.student_answers.filter(
            question__question_type=QuestionType.OPEN_ANSWER_MANUAL,
            is_correct__isnull=True # Cerca quelle non ancora valutate
        ).exists()

        if has_pending_manual:
            attempt.status = QuizAttempt.AttemptStatus.PENDING_GRADING
            attempt.score = None # Il punteggio finale verrà calcolato dopo la valutazione manuale
            logger.info(f"Tentativo {attempt.id} impostato a PENDING_GRADING.")
        else:
            # Tutte le domande sono auto-corrette o già valutate manualmente
            final_score = attempt.calculate_final_score() # Usa il metodo del modello
            attempt.score = final_score

            # Determina lo stato finale (COMPLETED o FAILED)
            completion_threshold = attempt.quiz.metadata.get('completion_threshold', 50) # Default 50%
            max_score = attempt.get_max_possible_score()
            percentage_score = (final_score / max_score * 100) if max_score > 0 else 0

            if percentage_score >= completion_threshold:
                 attempt.status = QuizAttempt.AttemptStatus.COMPLETED
                 logger.info(f"Tentativo {attempt.id} COMPLETATO con punteggio {final_score}/{max_score} ({percentage_score:.1f}%)")
            else:
                 attempt.status = QuizAttempt.AttemptStatus.FAILED
                 logger.info(f"Tentativo {attempt.id} FALLITO con punteggio {final_score}/{max_score} ({percentage_score:.1f}%)")

            # Assegna punti e badge solo se completato con successo
            if attempt.status == QuizAttempt.AttemptStatus.COMPLETED:
                 earned_badges = attempt.assign_completion_points() # Questo metodo ora restituisce i badge
                 # Aggiungi i badge guadagnati all'istanza per il serializer
                 attempt.newly_earned_badges = earned_badges # Assicurati che il serializer lo gestisca
                 # Aggiorna il progresso del percorso, se applicabile
                 attempt.update_pathway_progress()


        attempt.save()

        # Restituisci i dettagli del tentativo aggiornato
        serializer = self.get_serializer(attempt) # Usa il serializer di default o QuizAttemptDetailSerializer?
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- ViewSet per Docenti (Valutazione Manuale) ---

class TeacherGradingViewSet(viewsets.GenericViewSet):
    """ Endpoint per Docenti per visualizzare e correggere risposte manuali. """
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser]
    # Non usiamo un queryset standard qui, le azioni recuperano i dati necessari

    def get_queryset(self):
        # Restituisce le risposte manuali non valutate per i quiz del docente
        user = self.request.user
        if not user.is_teacher:
            return StudentAnswer.objects.none()
        return StudentAnswer.objects.filter(
            quiz_attempt__quiz__teacher=user,
            question__question_type=QuestionType.OPEN_ANSWER_MANUAL,
            is_correct__isnull=True
        ).select_related(
            'quiz_attempt', 'quiz_attempt__student', 'question', 'quiz_attempt__quiz'
        ).order_by('quiz_attempt__started_at', 'question__order') # Corretto start_time -> started_at


    @action(detail=False, methods=['get'], url_path='pending')
    def list_pending(self, request):
        """ Elenca le risposte manuali pendenti per il docente. """
        # Applicare manualmente il controllo dei permessi qui se necessario
        # (anche se IsTeacherUser dovrebbe bastare a livello di ViewSet)
        # if not request.user.is_teacher:
        #     return Response({"detail": "Accesso negato."}, status=status.HTTP_403_FORBIDDEN)

        queryset = self.get_queryset()
        # Serializza usando StudentAnswerSerializer o uno dedicato?
        # StudentAnswerSerializer va bene, ma potremmo volere più contesto.
        serializer = StudentAnswerSerializer(queryset, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=['post'], url_path='grade')
    def grade_answer(self, request, pk=None):
        """ Permette al docente di assegnare un punteggio a una risposta manuale. """
        try:
            student_answer = StudentAnswer.objects.select_related(
                'quiz_attempt', 'quiz_attempt__quiz', 'question'
            ).get(pk=pk)
        except StudentAnswer.DoesNotExist:
            raise Http404("Risposta non trovata.")

        # Verifica permessi: il docente deve essere il proprietario del quiz associato
        quiz_teacher = student_answer.quiz_attempt.quiz.teacher
        if not request.user.is_admin and quiz_teacher != request.user:
             logger.warning(f"Docente {request.user.id} ha tentato di valutare risposta {pk} non sua.")
             # Usiamo DRFPermissionDenied per coerenza con altri controlli
             raise DRFPermissionDenied("Non puoi valutare questa risposta.")

        if student_answer.question.question_type != QuestionType.OPEN_ANSWER_MANUAL:
            return Response({'detail': 'Questa risposta non richiede valutazione manuale.'}, status=status.HTTP_400_BAD_REQUEST)
        if student_answer.is_correct is not None:
            return Response({'detail': 'Questa risposta è già stata valutata.'}, status=status.HTTP_400_BAD_REQUEST)

        # Valida l'input del docente
        is_correct_input = request.data.get('is_correct')
        points_awarded_input = request.data.get('points_awarded')

        if is_correct_input is None or points_awarded_input is None:
            return Response({'detail': 'I campi "is_correct" (boolean) e "points_awarded" (integer) sono richiesti.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            is_correct = bool(is_correct_input)
            points_awarded = int(points_awarded_input)
            # Verifica che i punti non superino il massimo per la domanda (se definito)
            max_points = student_answer.question.metadata.get('points', 1) # Default a 1 se non specificato
            if points_awarded < 0 or points_awarded > max_points:
                 raise ValueError(f"I punti devono essere tra 0 e {max_points}.")
        except (ValueError, TypeError) as e:
            return Response({'detail': f'Input non valido: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        # Aggiorna la risposta dello studente
        student_answer.is_correct = is_correct
        student_answer.points_awarded = points_awarded
        student_answer.save()
        logger.info(f"Docente {request.user.id} ha valutato risposta {student_answer.id}: correct={is_correct}, points={points_awarded}")


        # Controlla se tutte le risposte manuali del tentativo sono state valutate
        attempt = student_answer.quiz_attempt
        all_manual_answers_graded = not attempt.student_answers.filter(
            question__question_type=QuestionType.OPEN_ANSWER_MANUAL,
            is_correct__isnull=True
        ).exists()

        if all_manual_answers_graded and attempt.status == QuizAttempt.AttemptStatus.PENDING_GRADING:
            # Ricalcola punteggio finale e aggiorna stato tentativo
            final_score = attempt.calculate_final_score()
            attempt.score = final_score

            # Determina stato finale
            completion_threshold = attempt.quiz.metadata.get('completion_threshold', 50)
            max_score = attempt.get_max_possible_score()
            percentage_score = (final_score / max_score * 100) if max_score > 0 else 0

            if percentage_score >= completion_threshold:
                 attempt.status = QuizAttempt.AttemptStatus.COMPLETED
                 logger.info(f"Tentativo {attempt.id} COMPLETATO (post-grading) con punteggio {final_score}/{max_score} ({percentage_score:.1f}%)")
                 # Assegna punti e badge
                 earned_badges = attempt.assign_completion_points()
                 attempt.newly_earned_badges = earned_badges # Per eventuale risposta API
                 # Aggiorna progresso percorso
                 attempt.update_pathway_progress()
            else:
                 attempt.status = QuizAttempt.AttemptStatus.FAILED
                 logger.info(f"Tentativo {attempt.id} FALLITO (post-grading) con punteggio {final_score}/{max_score} ({percentage_score:.1f}%)")
                 # Non assegnare punti/badge se fallito

            attempt.save()
            logger.info(f"Stato tentativo {attempt.id} aggiornato a {attempt.status} dopo valutazione manuale.")


        # Restituisci la risposta aggiornata
        serializer = StudentAnswerSerializer(student_answer)
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- Viste Generiche per Studente (Elenco Assegnazioni) ---

class StudentAssignedQuizzesView(generics.ListAPIView):
    """
    Restituisce l'elenco dei Quiz assegnati allo studente autenticato,
    insieme allo stato dell'ultimo tentativo.
    """
    serializer_class = StudentQuizDashboardSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudentAuthenticated]

    def get_queryset(self):
        student = self.request.user # Assicurato da IsStudentAuthenticated

        # Ottieni gli ID dei quiz assegnati direttamente
        direct_assignment_ids = QuizAssignment.objects.filter(
            student=student
        ).values_list('quiz_id', flat=True)

        # Ottieni gli ID dei quiz assegnati tramite percorsi
        pathway_assignment_quiz_ids = PathwayQuiz.objects.filter(
            pathway__assignments__student=student # Filtra per percorsi assegnati allo studente
        ).values_list('quiz_id', flat=True)

        # Combina gli ID e rendili unici
        assigned_quiz_ids = set(direct_assignment_ids) | set(pathway_assignment_quiz_ids)

        # Filtra i Quiz in base agli ID assegnati
        queryset = Quiz.objects.filter(id__in=assigned_quiz_ids).select_related('teacher').prefetch_related(
             Prefetch(
                 'attempts',
                 queryset=QuizAttempt.objects.filter(student=student).order_by('-started_at'),
                 to_attr='student_attempts_ordered' # Nome attributo per accedere ai tentativi ordinati
             )
        )
        # Annotazione rimossa, gestita nel serializer o con prefetch
        return queryset.order_by('-created_at') # O altro ordinamento desiderato

    def get_serializer_context(self):
        # Passa la request per accedere all'utente nel serializer (se necessario)
        return {'request': self.request}


class StudentAssignedPathwaysView(generics.ListAPIView):
    """
    Restituisce l'elenco dei Percorsi assegnati allo studente autenticato,
    insieme allo stato dell'ultimo progresso.
    """
    serializer_class = StudentPathwayDashboardSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudentAuthenticated]

    def get_queryset(self):
        student = self.request.user
        assigned_pathway_ids = PathwayAssignment.objects.filter(
            student=student
        ).values_list('pathway_id', flat=True)

        queryset = Pathway.objects.filter(id__in=assigned_pathway_ids).select_related('teacher').prefetch_related(
             Prefetch(
                 'progresses', # Usa il related_name corretto 'progresses'
                 queryset=PathwayProgress.objects.filter(student=student).order_by('-started_at'),
                 to_attr='student_progress_ordered'
             )
        )
        return queryset.order_by('-created_at')

    def get_serializer_context(self):
        return {'request': self.request}


# --- Vista Dettaglio Svolgimento Percorso ---

class PathwayAttemptDetailView(generics.RetrieveAPIView):
    """
    Restituisce i dettagli di un percorso per lo studente che lo sta svolgendo,
    includendo informazioni sul prossimo quiz.
    """
    queryset = Pathway.objects.prefetch_related(
        'pathwayquiz_set__quiz', # Precarica i quiz nel percorso
        # Precarica anche i tentativi dello studente per i quiz di questo percorso
        Prefetch(
            'pathwayquiz_set__quiz__attempts',
             queryset=QuizAttempt.objects.filter(student=OuterRef(OuterRef('student_id'))).order_by('-started_at'), # Filtra per studente (richiede contesto) - NON FUNZIONA DIRETTAMENTE QUI
             to_attr='student_attempts'
        )
    )
    serializer_class = PathwayAttemptDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudentAuthenticated]

    def get_object(self):
        """ Recupera il percorso e verifica che sia assegnato allo studente. """
        pathway_id = self.kwargs.get('pathway_id')
        student = self.request.user
        pathway = get_object_or_404(self.get_queryset(), pk=pathway_id)

        # Verifica assegnazione
        is_assigned = PathwayAssignment.objects.filter(pathway=pathway, student=student).exists()
        if not is_assigned:
            raise Http404("Percorso non assegnato a questo studente.")

        # Filtra i tentativi DOPO aver recuperato il percorso
        # Questo è meno efficiente ma necessario perché OuterRef non funziona come sperato qui
        pathway.student_attempts_for_pathway = QuizAttempt.objects.filter(
            student=student,
            quiz__pathwayquiz__pathway=pathway
        ).order_by('-start_time')

        # Recupera l'ultimo progresso per questo studente e percorso
        pathway.latest_progress = PathwayProgress.objects.filter(
            pathway=pathway, student=student
        ).order_by('-start_time').first()


        return pathway

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Passa lo studente nel contesto per get_next_quiz
        serializer = self.get_serializer(instance, context={'request': request})
        return Response(serializer.data)
