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
from apps.rewards.serializers import SimpleBadgeSerializer # Importa il serializer per i badge
from .models import (
    QuizTemplate, QuestionTemplate, AnswerOptionTemplate,
    Quiz, Question, AnswerOption, Pathway, PathwayQuiz,
    QuizAttempt, StudentAnswer, PathwayProgress, QuestionType,
    QuizAssignment, PathwayAssignment, PathwayTemplate, PathwayQuizTemplate # Importa i modelli Assignment e Template Percorsi
)
from .serializers import (
    QuizTemplateSerializer, QuestionTemplateSerializer, AnswerOptionTemplateSerializer,
    QuizSerializer, QuestionSerializer, AnswerOptionSerializer, PathwaySerializer, PathwayQuizSerializer, # Aggiunto PathwayQuizSerializer
    QuizAttemptSerializer, StudentAnswerSerializer, PathwayProgressSerializer, # Importa StudentAnswerSerializer
    QuizAttemptDetailSerializer, # Importa il nuovo serializer
    StudentQuizDashboardSerializer, StudentPathwayDashboardSerializer, # Importa i nuovi serializer
    QuizUploadSerializer, # Aggiunto QuizUploadSerializer
    SimpleQuizAttemptSerializer, # Importa SimpleQuizAttemptSerializer
    PathwayAttemptDetailSerializer, # Importa il serializer per la nuova view
    NextPathwayQuizSerializer, # Aggiunto import mancante
    # Nuovi Serializer per Template Percorsi e Assegnazioni
    PathwayTemplateSerializer, PathwayQuizTemplateSerializer,
    QuizAssignmentSerializer, PathwayAssignmentSerializer, QuizAssignmentDetailSerializer, PathwayAssignmentDetailSerializer, # Importa nuovi serializer
    QuizTemplateStatsSerializer, PathwayTemplateStatsSerializer, # Importa i serializer per le statistiche
    # SimpleBadgeSerializer è importato sopra
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

        # Calcola completion rate (basato sui tentativi)
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
            'completed_attempts': completed_attempts,
            'average_score': stats.get('average_score'),
            'completion_rate': completion_rate,
        }

        serializer = QuizTemplateStatsSerializer(data)
        return Response(serializer.data)


# --- ViewSet per Docenti (Gestione Questioni/Opzioni Template) ---

class TeacherQuestionTemplateViewSet(viewsets.ModelViewSet): # Aggiunta azione question_ids
    """ API endpoint per le Question Templates gestite da Docenti nel contesto di un loro QuizTemplate. """
    serializer_class = QuestionTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser] # Solo Docenti

    def get_queryset(self):
        """ Filtra per mostrare solo le domande del template specificato e appartenente al docente. """
        quiz_template_pk = self.kwargs.get('quiz_template_pk')
        quiz_template = get_object_or_404(QuizTemplate, pk=quiz_template_pk, teacher=self.request.user)
        return QuestionTemplate.objects.filter(quiz_template=quiz_template).order_by('order')

    def perform_create(self, serializer):
        """ Associa la domanda al template del docente e gestisce l'ordine. """
        quiz_template_pk = self.kwargs.get('quiz_template_pk')
        quiz_template = get_object_or_404(QuizTemplate, pk=quiz_template_pk, teacher=self.request.user)
        # Calcola il prossimo ordine disponibile
        last_order = QuestionTemplate.objects.filter(quiz_template=quiz_template).aggregate(max_order=AggregateMax('order'))['max_order']
        next_order = 0 if last_order is None else last_order + 1
        serializer.save(quiz_template=quiz_template, order=next_order)

    @transaction.atomic
    def perform_destroy(self, instance):
        """ Elimina la domanda template e riordina le successive. """
        quiz_template = instance.quiz_template
        deleted_order = instance.order
        instance.delete()
        # Riordina le domande successive nello stesso template
        questions_to_reorder = QuestionTemplate.objects.filter(
            quiz_template=quiz_template,
            order__gt=deleted_order
        ).order_by('order')
        for question in questions_to_reorder:
            question.order -= 1
            question.save(update_fields=['order'])

    # Azione per ottenere solo gli ID delle domande in ordine
    @action(detail=False, methods=['get'], url_path='question-ids', permission_classes=[permissions.IsAuthenticated, IsTeacherUser])
    def question_ids(self, request, quiz_template_pk=None): # Rimosso pk non necessario
        """ Restituisce un elenco ordinato degli ID delle domande per un dato template del docente. """
        quiz_template = get_object_or_404(QuizTemplate, pk=quiz_template_pk, teacher=request.user)
        question_ids = QuestionTemplate.objects.filter(quiz_template=quiz_template).order_by('order').values_list('id', flat=True)
        return Response(list(question_ids))


class TeacherAnswerOptionTemplateViewSet(viewsets.ModelViewSet):
    """ API endpoint per le Answer Option Templates gestite da Docenti. """ # Corretta indentazione (4 spazi)
    serializer_class = AnswerOptionTemplateSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser] # Solo Docenti

    def get_queryset(self): # Corretta indentazione (4 spazi)
        """ Filtra per le opzioni della domanda specificata, verificando che appartenga al docente. """
        question_template_pk = self.kwargs.get('question_template_pk')
        # Verifica che la domanda appartenga a un template del docente
        question_template = get_object_or_404(
            QuestionTemplate.objects.select_related('quiz_template'), # Ottimizza query
            pk=question_template_pk,
            quiz_template__teacher=self.request.user
        )
        return AnswerOptionTemplate.objects.filter(question_template=question_template).order_by('order')

    def perform_create(self, serializer): # Corretta indentazione (4 spazi)
        """ Associa l'opzione alla domanda template del docente e gestisce l'ordine. """
        question_template_pk = self.kwargs.get('question_template_pk')
        question_template = get_object_or_404(QuestionTemplate, pk=question_template_pk, quiz_template__teacher=self.request.user)
        # Calcola il prossimo ordine disponibile per questa domanda
        last_order = AnswerOptionTemplate.objects.filter(question_template=question_template).aggregate(max_order=AggregateMax('order'))['max_order']
        next_order = 0 if last_order is None else last_order + 1
        serializer.save(question_template=question_template, order=next_order)

    def perform_destroy(self, instance): # Assicura 4 spazi qui
        """ Elimina l'opzione e riordina le successive per la stessa domanda. """
        question_template = instance.question_template
        deleted_order = instance.order
        instance.delete()
        # Riordina le opzioni successive per la stessa domanda
        options_to_reorder = AnswerOptionTemplate.objects.filter( # Assicura 8 spazi qui
            question_template=question_template,
            order__gt=deleted_order
        ).order_by('order')
        for option in options_to_reorder:
            option.order -= 1
            option.save(update_fields=['order'])


# --- ViewSet per Docenti (Quiz Concreti) ---

class QuizViewSet(viewsets.ModelViewSet):
    """ API endpoint per i Quiz concreti (Docente). """
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser] # Solo Docenti

    # Rimosso get_permissions per usare permission_classes standard

    def get_queryset(self):
        """ Filtra per mostrare solo i quiz creati dal docente loggato. """
        user = self.request.user
        # Assicurati che l'utente sia un docente
        if isinstance(user, User) and user.is_teacher:
            # Precarica le domande per ottimizzare (se necessario nel list view)
            return Quiz.objects.filter(teacher=user).prefetch_related('questions')
        return Quiz.objects.none()

    def perform_create(self, serializer):
        """ Associa automaticamente il docente creatore. """
        # Non è necessario controllare di nuovo il ruolo qui perché IsTeacherUser lo fa già
        # Imposta available_from/until se forniti, altrimenti potrebbero essere null
        available_from = serializer.validated_data.get('available_from')
        available_until = serializer.validated_data.get('available_until')
        serializer.save(teacher=self.request.user, available_from=available_from, available_until=available_until)

    # --- Funzioni Helper per Creazione da Template ---
    def _create_quiz_instance_from_template(self, template: QuizTemplate, teacher: User, title_override: str = None) -> Quiz:
        """
        Crea una nuova istanza di Quiz (con domande e opzioni concrete)
        a partire da un QuizTemplate.
        Questa funzione è pensata per essere chiamata internamente da altre azioni (es. assign_student).
        """
        try:
            with transaction.atomic():
                # 1. Crea l'istanza Quiz
                new_quiz = Quiz.objects.create(
                    teacher=teacher, # Il docente che assegna/crea è il proprietario
                    source_template=template,
                    title=title_override or template.title,
                    description=template.description,
                    metadata=template.metadata.copy() if template.metadata else {}
                    # available_from/until possono essere impostati dopo o durante l'assegnazione
                )

                # 2. Itera sulle QuestionTemplate del QuizTemplate
                question_templates = template.question_templates.prefetch_related('answer_option_templates').order_by('order')

                questions_to_create = []
                options_to_create = []
                question_map = {} # Mappa temporanea per collegare opzioni a domande appena create

                for qt in question_templates:
                    # 3. Prepara l'oggetto Question concreto
                    new_question = Question(
                        quiz=new_quiz,
                        text=qt.text,
                        question_type=qt.question_type,
                        order=qt.order,
                        metadata=qt.metadata.copy() if qt.metadata else {}
                    )
                    questions_to_create.append(new_question)
                    # Memorizza riferimento temporaneo per le opzioni
                    question_map[qt.id] = {'instance': new_question, 'options': list(qt.answer_option_templates.order_by('order'))}

                # 4. Crea le Question in blocco
                created_questions = Question.objects.bulk_create(questions_to_create)

                # Aggiorna la mappa con gli ID reali delle domande create
                # Ricostruisci la mappa basata sugli oggetti creati per sicurezza
                final_question_map = {}
                for created_q in created_questions:
                     # Trova il template corrispondente (assumendo testo+ordine univoco nel template)
                     matching_template_id = None
                     for qt_id, q_map_item in question_map.items():
                         if q_map_item['instance'].text == created_q.text and q_map_item['instance'].order == created_q.order:
                             matching_template_id = qt_id
                             break
                     if matching_template_id:
                         final_question_map[matching_template_id] = {'instance': created_q, 'options': question_map[matching_template_id]['options']}
                     else:
                          logger.warning(f"Impossibile trovare il template corrispondente per la domanda creata: '{created_q.text}' (Quiz: {new_quiz.id})")


                # 5. Itera sulle AnswerOptionTemplate e prepara le AnswerOption concrete
                for qt_id, q_map_item in final_question_map.items():
                    question_instance = q_map_item['instance']
                    for aot in q_map_item['options']:
                        options_to_create.append(
                            AnswerOption(
                                question=question_instance,
                                text=aot.text,
                                is_correct=aot.is_correct,
                                order=aot.order
                            )
                        )

                # 6. Crea le AnswerOption in blocco
                if options_to_create:
                    AnswerOption.objects.bulk_create(options_to_create)

                logger.info(f"Creata istanza Quiz ID {new_quiz.id} da Template ID {template.id} per Docente {teacher.id}")
                return new_quiz
        except Exception as e:
            logger.error(f"Errore atomico durante creazione Quiz da template {template.id}: {e}", exc_info=True)
            raise # Rilancia per far fallire la richiesta API esterna


    # --- Azioni Specifiche ---

    @action(detail=False, methods=['post'], url_path='create-from-template', permission_classes=[permissions.IsAuthenticated, IsTeacherUser])
    def create_from_template(self, request):
        """
        Crea una nuova istanza di Quiz a partire da un QuizTemplate esistente.
        Richiede 'template_id' e opzionalmente 'title_override' nel body.
        """
        template_id = request.data.get('template_id')
        title_override = request.data.get('title_override')

        if not template_id:
            return Response({'detail': 'template_id è richiesto.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Il docente può usare solo i propri template o quelli globali (admin=None)?
            # Per ora, assumiamo possa usare solo i propri o quelli admin.
            template = get_object_or_404(
                QuizTemplate,
                Q(pk=template_id) & (Q(teacher=request.user) | Q(admin__isnull=False, teacher__isnull=True))
            )
        except QuizTemplate.DoesNotExist:
             return Response({'detail': 'Template non trovato o non accessibile.'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
             return Response({'detail': 'template_id non valido.'}, status=status.HTTP_400_BAD_REQUEST)


        try:
            new_quiz = self._create_quiz_instance_from_template(template, request.user, title_override)
            serializer = self.get_serializer(new_quiz)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # _create_quiz_instance_from_template logga già l'errore
            return Response({'detail': f'Errore durante la creazione del quiz dal template: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['post'], url_path='upload', permission_classes=[permissions.IsAuthenticated, IsTeacherUser], parser_classes=[parsers.MultiPartParser, parsers.FormParser])
    def upload_quiz(self, request, *args, **kwargs):
        """
        Permette a un docente di caricare un file (PDF, DOCX, MD) per creare un Quiz concreto.
        Richiede 'file' e 'title' nei dati della richiesta (form-data).
        """
        # Usa QuizUploadSerializer definito in serializers.py
        serializer = QuizUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                # Il metodo create del serializer gestisce l'estrazione, il parsing e la creazione del quiz
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


    @action(detail=False, methods=['post'], url_path='assign-student', permission_classes=[permissions.IsAuthenticated, IsTeacherUser])
    def assign_student(self, request):
        """
        Assegna un Quiz esistente (o uno creato da template al volo) a uno o più studenti.
        Input:
        {
            "quiz_id": <id_quiz_esistente> (opzionale, alternativo a template_id)
            "template_id": <id_template> (opzionale, alternativo a quiz_id, crea nuovo quiz)
            "title_override": "Titolo specifico per questo quiz" (opzionale, usato con template_id)
            "student_ids": [<id_studente_1>, <id_studente_2>, ...],
            "due_date": "YYYY-MM-DDTHH:MM:SSZ" (opzionale)
        }
        """
        # Importa i serializer necessari qui per evitare import circolari
        from .serializers import QuizAssignActionSerializer, QuizAssignmentSerializer

        action_serializer = QuizAssignActionSerializer(data=request.data, context={'request': request})
        if not action_serializer.is_valid():
            logger.warning(f"Errore validazione QuizAssignActionSerializer da utente {request.user.id}: {action_serializer.errors}")
            return Response(action_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = action_serializer.validated_data
        quiz_instance_from_id = validated_data.get('quiz_id') # Oggetto Quiz o None
        template_object = validated_data.get('quiz_template_id') # Oggetto QuizTemplate o None
        title_override = validated_data.get('title_override') # Stringa o None
        students = validated_data.get('students') # Lista di oggetti Student
        due_date = validated_data.get('due_date')
        teacher = request.user

        quiz_instance = None

        # --- Logica per ottenere/creare il Quiz ---
        if quiz_instance_from_id:
            # Usa l'istanza del quiz esistente validata dal serializer
            quiz_instance = quiz_instance_from_id
            # Il controllo ownership è già stato fatto nel serializer
            logger.debug(f"Using existing quiz instance ID: {quiz_instance.id}")

        elif template_object:
            # Crea un nuovo quiz dal template object validato dal serializer
            # Il controllo ownership è già stato fatto nel serializer
            logger.debug(f"Creating new quiz instance from template ID: {template_object.id}")
            try:
                quiz_instance = self._create_quiz_instance_from_template(template_object, teacher, title_override)
                logger.debug(f"Successfully created new quiz instance ID: {quiz_instance.id}")
            except Exception as e:
                logger.error(f"Error creating quiz instance from template {template_object.id}: {e}", exc_info=True)
                return Response({'detail': f'Errore durante la creazione del quiz dal template: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Questo caso non dovrebbe mai essere raggiunto grazie alla validazione del serializer
            logger.error("assign_student reached 'else' block after serializer validation. This should not happen.")
            return Response({'detail': 'Errore interno: Specificare quiz_id o template_id.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- Logica di Assegnazione ---
        assignments_created = []
        assignments_failed = []
        assignments_existing = []

        for student in students:
            # Verifica se l'assegnazione esiste già
            existing_assignment = QuizAssignment.objects.filter(quiz=quiz_instance, student=student).first()
            if existing_assignment:
                logger.warning(f"Tentativo di riassegnare quiz {quiz_instance.id} a studente {student.id}")
                assignments_existing.append({'student_id': student.id, 'assignment_id': existing_assignment.id})
                # Potremmo aggiornare la due_date? Per ora saltiamo.
                continue

            # Crea l'assegnazione
            assignment_data = {
                'quiz': quiz_instance.id,
                'student': student.id,
                'assigned_by': teacher.id,
                'due_date': due_date
            }
            assignment_serializer = QuizAssignmentSerializer(data=assignment_data)
            if assignment_serializer.is_valid():
                try:
                    assignment = assignment_serializer.save()
                    assignments_created.append(assignment_serializer.data)
                    logger.info(f"Docente {teacher.id} ha assegnato il quiz {quiz_instance.id} allo studente {student.id}")
                except IntegrityError as e: # Cattura potenziali errori di integrità (es. vincoli DB)
                     logger.error(f"Errore DB durante creazione assegnazione quiz {quiz_instance.id} a studente {student.id}: {e}")
                     assignments_failed.append({'student_id': student.id, 'error': str(e)})
                except Exception as e: # Cattura altri errori imprevisti
                     logger.error(f"Errore imprevisto durante creazione assegnazione quiz {quiz_instance.id} a studente {student.id}: {e}", exc_info=True)
                     assignments_failed.append({'student_id': student.id, 'error': 'Errore sconosciuto'})
            else:
                logger.error(f"Errore validazione QuizAssignmentSerializer per studente {student.id}: {assignment_serializer.errors}")
                assignments_failed.append({'student_id': student.id, 'error': assignment_serializer.errors})

        # --- Risposta Riassuntiva ---
        response_status = status.HTTP_201_CREATED if assignments_created and not assignments_failed else status.HTTP_207_MULTI_STATUS
        return Response({
            'quiz_id': quiz_instance.id,
            'quiz_title': quiz_instance.title,
            'assignments_created': assignments_created,
            'assignments_existing': assignments_existing,
            'assignments_failed': assignments_failed
        }, status=response_status)


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
        if not request.user.is_staff and assignment.quiz.teacher != request.user:
             raise DRFPermissionDenied("Non puoi disassegnare studenti da questo quiz.")

        student_id = assignment.student.id
        quiz_id = assignment.quiz.id
        assignment.delete()
        logger.info(f"Docente/Admin {request.user.id} ha disassegnato lo studente {student_id} (Assignment ID: {assignment_pk}) dal quiz {quiz_id}")
        return Response({'detail': 'Studente disassegnato con successo dal quiz.'}, status=status.HTTP_204_NO_CONTENT)


    @action(detail=True, methods=['get'], url_path='assignments', permission_classes=[IsAdminUser | IsTeacherUser])
    def get_assignments(self, request, pk=None):
        """ Recupera l'elenco degli studenti a cui è assegnato questo quiz. """
        # Importa il serializer qui per evitare import circolari
        from .serializers import QuizAssignmentDetailSerializer
        quiz = self.get_object() # Applica permessi
        assignments = QuizAssignment.objects.filter(quiz=quiz).select_related('student')

        # Log per debug
        logger.debug(f"[get_assignments - Quiz] Quiz ID: {quiz.id}, Found assignments queryset: {assignments}")

        # Calcola statistiche (opzionale, ma utile)
        # Conta tentativi completati per questo quiz
        completed_attempts_count = QuizAttempt.objects.filter(
            quiz=quiz,
            status__in=[QuizAttempt.AttemptStatus.COMPLETED, QuizAttempt.AttemptStatus.FAILED] # Considera sia passati che falliti
        ).values('student').distinct().count()

        # Calcola punteggio medio sui tentativi completati (solo quelli con punteggio)
        average_score_agg = QuizAttempt.objects.filter(
            quiz=quiz,
            status__in=[QuizAttempt.AttemptStatus.COMPLETED, QuizAttempt.AttemptStatus.FAILED],
            score__isnull=False
        ).aggregate(average_score=Avg('score'))
        average_score = average_score_agg.get('average_score')

        serializer = QuizAssignmentDetailSerializer(assignments, many=True)
        logger.debug(f"[get_assignments - Quiz] Serialized data for assignments: {serializer.data}")

        data = {
            'assignments': serializer.data,
            'stats': { # Aggiunge statistiche alla risposta
                 'assigned_count': assignments.count(),
                 'completed_attempts_count': completed_attempts_count,
                 'average_score': round(average_score, 2) if average_score is not None else None,
            }
        }
        return Response(data)


    # Azione per rimuovere un Quiz da un Pathway (agisce sul modello PathwayQuiz)
    @action(detail=True, methods=['delete'], url_path='remove-quiz/(?P<pathway_quiz_pk>[^/.]+)', permission_classes=[permissions.IsAuthenticated, IsPathwayOwnerOrAdmin])
    def remove_quiz(self, request, pk=None, pathway_quiz_pk=None):
        """
        Rimuove questo Quiz da un Percorso specifico.
        Richiede l'ID della relazione PathwayQuiz nell'URL.
        Verifica che l'utente sia il proprietario del Percorso.
        """
        quiz = self.get_object() # Quiz su cui si agisce (pk)

        try:
            # Trova la relazione specifica Pathway-Quiz
            pathway_quiz_entry = get_object_or_404(
                PathwayQuiz.objects.select_related('pathway'), # Precarica il percorso per controllo permessi
                pk=pathway_quiz_pk,
                quiz=quiz # Assicura che sia la relazione per questo quiz
            )
        except (ValueError, TypeError):
             return Response({'detail': 'ID relazione Pathway-Quiz non valido.'}, status=status.HTTP_400_BAD_REQUEST)
        except PathwayQuiz.DoesNotExist: # Già gestito da get_object_or_404 ma esplicito
             return Response({'detail': 'Relazione Pathway-Quiz non trovata.'}, status=status.HTTP_404_NOT_FOUND)


        pathway = pathway_quiz_entry.pathway

        # Verifica permessi sul Percorso
        if not request.user.is_staff and pathway.teacher != request.user:
             raise DRFPermissionDenied("Non puoi modificare questo percorso.")

        deleted_order = pathway_quiz_entry.order
        pathway_quiz_entry.delete()

        # Riordina i quiz successivi nello stesso percorso
        quizzes_to_reorder = PathwayQuiz.objects.filter(
            pathway=pathway,
            order__gt=deleted_order
        ).order_by('order')
        for pq in quizzes_to_reorder:
            pq.order -= 1
            pq.save(update_fields=['order'])

        logger.info(f"Quiz {quiz.id} rimosso dal Percorso {pathway.id} (Relazione ID: {pathway_quiz_pk}) da utente {request.user.id}")
        return Response(status=status.HTTP_204_NO_CONTENT)

    # --- Azione per Studente: Iniziare un Tentativo ---
    # Spostato da StudentQuizAttemptViewSet
    @action(detail=True, methods=['post'], url_path='start-attempt', permission_classes=[permissions.IsAuthenticated, IsStudentAuthenticated]) # Aggiunto permesso IsStudentAuthenticated
    def start_attempt(self, request, pk=None): # pk è l'ID del Quiz
        """
        Permette a uno studente autenticato di iniziare un nuovo tentativo per un quiz specifico.
        Verifica che lo studente sia assegnato al quiz (direttamente o tramite percorso).
        Verifica che non ci siano tentativi in corso per lo stesso quiz.
        Verifica eventuali limiti di tentativi (se implementati).
        """
        student = request.user # Ora request.user è l'istanza Student
        quiz_pk = pk # L'ID del quiz è ora nel pk dell'URL

        try:
            quiz = Quiz.objects.get(pk=quiz_pk)
        except Quiz.DoesNotExist:
            return Response({'detail': 'Quiz non trovato.'}, status=status.HTTP_404_NOT_FOUND)

        # 1. Verifica Assegnazione (Diretta o Tramite Percorso)
        is_assigned_directly = QuizAssignment.objects.filter(
            quiz=quiz,
            student=student
        ).exists()

        is_in_assigned_pathway = Pathway.objects.filter(
            assignments__student=student, # Assegnato allo studente
            quizzes=quiz # Contiene questo quiz
        ).exists()

        if not is_assigned_directly and not is_in_assigned_pathway:
             logger.warning(f"Tentativo non autorizzato di iniziare quiz {quiz_pk} da studente {student.id} (non assegnato).")
             return Response({'detail': 'Non sei assegnato a questo quiz.'}, status=status.HTTP_403_FORBIDDEN)

        # 2. Verifica Date Disponibilità Quiz (se impostate)
        now = timezone.now()
        if quiz.available_from and now < quiz.available_from:
            return Response({'detail': f'Questo quiz non è ancora disponibile. Sarà disponibile dal {quiz.available_from.strftime("%d/%m/%Y %H:%M")}.'}, status=status.HTTP_403_FORBIDDEN)
        if quiz.available_until and now > quiz.available_until:
            return Response({'detail': f'Questo quiz non è più disponibile. La data limite era il {quiz.available_until.strftime("%d/%m/%Y %H:%M")}.'}, status=status.HTTP_403_FORBIDDEN)


        # 3. Verifica Tentativi Esistenti
        in_progress_attempt = QuizAttempt.objects.filter(
            quiz=quiz,
            student=student,
            status__in=[QuizAttempt.AttemptStatus.IN_PROGRESS, QuizAttempt.AttemptStatus.PENDING_GRADING]
        ).first()

        if in_progress_attempt:
            logger.info(f"Studente {student.id} ha tentato di iniziare quiz {quiz_pk} ma ha già un tentativo {in_progress_attempt.status} (ID: {in_progress_attempt.id}).")
            # Usa il serializer corretto per la risposta (QuizAttemptSerializer o uno specifico)
            # Assumiamo che QuizAttemptSerializer sia definito e importato
            from .serializers import QuizAttemptSerializer # Importa qui se non già fatto globalmente
            serializer = QuizAttemptSerializer(in_progress_attempt, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK) # Restituisce il tentativo esistente

        # 4. Verifica Limite Tentativi
        max_attempts = quiz.metadata.get('max_attempts')
        if max_attempts is not None:
             try:
                 max_attempts = int(max_attempts)
                 completed_attempts_count = QuizAttempt.objects.filter(
                     quiz=quiz,
                     student=student,
                     status__in=[QuizAttempt.AttemptStatus.COMPLETED, QuizAttempt.AttemptStatus.FAILED]
                 ).count()
                 if completed_attempts_count >= max_attempts:
                     logger.warning(f"Studente {student.id} ha raggiunto il limite di {max_attempts} tentativi per quiz {quiz_pk}.")
                     return Response({'detail': f'Hai raggiunto il numero massimo di tentativi ({max_attempts}) per questo quiz.'}, status=status.HTTP_403_FORBIDDEN)
             except (ValueError, TypeError):
                  logger.error(f"Valore non valido per 'max_attempts' nei metadati del quiz {quiz_pk}: {quiz.metadata.get('max_attempts')}")


        # 5. Crea Nuovo Tentativo
        try:
            with transaction.atomic():
                blocking_attempt = QuizAttempt.objects.select_for_update().filter(
                    quiz=quiz,
                    student=student,
                    status__in=[QuizAttempt.AttemptStatus.IN_PROGRESS, QuizAttempt.AttemptStatus.PENDING_GRADING]
                ).first()
                if blocking_attempt:
                     logger.warning(f"Race condition rilevata: Studente {student.id} ha già un tentativo {blocking_attempt.status} (ID: {blocking_attempt.id}) per quiz {quiz_pk}.")
                     from .serializers import QuizAttemptSerializer # Importa qui se non già fatto globalmente
                     serializer = QuizAttemptSerializer(blocking_attempt, context={'request': request})
                     return Response(serializer.data, status=status.HTTP_409_CONFLICT)

                new_attempt = QuizAttempt.objects.create(
                    student=student,
                    quiz=quiz,
                    status=QuizAttempt.AttemptStatus.IN_PROGRESS
                )
                logger.info(f"Studente {student.id} ha iniziato un nuovo tentativo {new_attempt.id} per il quiz {quiz_pk}")
                from .serializers import QuizAttemptSerializer # Importa qui se non già fatto globalmente
                serializer = QuizAttemptSerializer(new_attempt, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
             logger.error(f"Errore durante la creazione del tentativo per quiz {quiz_pk} da studente {student.id}: {e}", exc_info=True)
             return Response({'detail': 'Errore interno durante la creazione del tentativo.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- ViewSet per Dashboard Studente ---

class StudentDashboardViewSet(viewsets.ViewSet):
     """ Endpoint per lo studente per vedere cosa gli è stato assegnato. """
     permission_classes = [permissions.IsAuthenticated, IsStudentAuthenticated] # Solo studenti autenticati

     def list(self, request):
         student = request.user # Ora request.user è l'istanza Student grazie al middleware/auth backend
         if not isinstance(student, Student):
              logger.error(f"Errore: request.user non è un'istanza Student nella StudentDashboardViewSet per user ID {request.user.id}")
              return Response({"detail": "Errore interno: impossibile identificare lo studente."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

         # Recupera ID dei Quiz assegnati direttamente
         assigned_quiz_ids = QuizAssignment.objects.filter(
             student=student,
             # Filtra per date se necessario (es. quiz non ancora disponibili o scaduti?)
             # quiz__available_from__lte=timezone.now(),
             # quiz__available_until__gte=timezone.now(), # O gestisci null
         ).values_list('quiz_id', flat=True)

         # Recupera ID dei Percorsi assegnati
         assigned_pathway_ids = PathwayAssignment.objects.filter(
             student=student,
             # Filtra per date se necessario
         ).values_list('pathway_id', flat=True)

         # Recupera ID dei Quiz contenuti nei percorsi assegnati
         quiz_ids_in_assigned_pathways = PathwayQuiz.objects.filter(
             pathway_id__in=assigned_pathway_ids
         ).values_list('quiz_id', flat=True)

         # Combina tutti gli ID dei quiz rilevanti (diretti + da percorsi)
         unique_quiz_ids = set(assigned_quiz_ids) | set(quiz_ids_in_assigned_pathways)

         # Recupera gli oggetti Quiz e Pathway
         # Ottimizza precaricando i tentativi/progressi per lo studente corrente
         student_attempts_prefetch = Prefetch(
             'attempts',
             queryset=QuizAttempt.objects.filter(student=student).order_by('-started_at'),
             to_attr='student_attempts_for_dashboard' # Nome attributo per evitare conflitti
         )
         quizzes = Quiz.objects.filter(id__in=unique_quiz_ids).select_related('teacher').prefetch_related(
             student_attempts_prefetch
         )

         student_progress_prefetch = Prefetch(
             'progresses',
             queryset=PathwayProgress.objects.filter(student=student).order_by('-updated_at'),
             to_attr='student_progress_for_dashboard'
         )
         pathways = Pathway.objects.filter(id__in=assigned_pathway_ids).select_related('teacher').prefetch_related(
             student_progress_prefetch
         )

         # Serializza i dati per la risposta
         quiz_serializer = StudentQuizDashboardSerializer(quizzes, many=True, context={'request': request})
         pathway_serializer = StudentPathwayDashboardSerializer(pathways, many=True, context={'request': request})

         return Response({
             'assigned_quizzes': quiz_serializer.data,
             'assigned_pathways': pathway_serializer.data
         })


# --- ViewSet per Azioni Studente su Tentativo Specifico ---

class AttemptViewSet(viewsets.GenericViewSet):

        # 1. Verifica Assegnazione (Diretta o Tramite Percorso)
        is_assigned_directly = QuizAssignment.objects.filter(
            quiz=quiz,
            student=student
        ).exists()

        is_in_assigned_pathway = Pathway.objects.filter(
            assignments__student=student, # Assegnato allo studente
            quizzes=quiz # Contiene questo quiz
        ).exists()

        # 2. Verifica Date Disponibilità Quiz (se impostate)
        now = timezone.now()
# --- ViewSet per Azioni Studente su Tentativo Specifico ---

class AttemptViewSet(viewsets.GenericViewSet):
    pass # Aggiunto pass per risolvere IndentationError (può essere rimosso ora)
    """ Gestisce le azioni su un tentativo di quiz specifico (submit, complete). """
    queryset = QuizAttempt.objects.all()
    serializer_class = QuizAttemptSerializer # Serializer di base
    permission_classes = [permissions.IsAuthenticated, IsStudentOwnerForAttempt] # Solo lo studente proprietario

    # Override per usare serializer diversi in base all'azione
    def get_serializer_class(self):
        if self.action == 'submit_answer':
            return StudentAnswerSerializer
        elif self.action == 'details': # Aggiunta azione details
             return QuizAttemptDetailSerializer
        # Aggiungere altri casi se necessario
        return super().get_serializer_class()

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """ Restituisce i dettagli completi di un tentativo. """
        attempt = self.get_object() # Applica permessi
        serializer = self.get_serializer(attempt) # Usa QuizAttemptDetailSerializer
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='current-question')
    def current_question(self, request, pk=None):
        """ Restituisce la prossima domanda non risposta per il tentativo specificato. """
        attempt = self.get_object() # Applica permessi

        if attempt.status != QuizAttempt.AttemptStatus.IN_PROGRESS:
            return Response({'detail': 'Questo tentativo non è più in corso.'}, status=status.HTTP_400_BAD_REQUEST)

        # Trova l'ordine massimo tra le risposte già date per questo tentativo
        last_answered_order = attempt.student_answers.aggregate(max_order=AggregateMax('question__order'))['max_order']
        next_order = 0 if last_answered_order is None else last_answered_order + 1

        # Trova la prossima domanda nel quiz con quell'ordine
        next_question = Question.objects.filter(
            quiz=attempt.quiz,
            order=next_order
        ).prefetch_related('answer_options').first() # Precarica le opzioni

        if next_question:
            serializer = QuestionSerializer(next_question)
            return Response(serializer.data)
        else:
            # Non ci sono più domande
            logger.info(f"[current_question] Nessuna domanda successiva trovata per tentativo {pk}. Restituzione 404.")
            return Response({'detail': 'Tutte le domande sono state risposte.'}, status=status.HTTP_404_NOT_FOUND)


    @action(detail=True, methods=['post'], url_path='submit-answer')
    def submit_answer(self, request, pk=None):
        """
        Permette allo studente di inviare una risposta per una domanda specifica
        all'interno di un tentativo in corso.
        Input:
        {
            "question_id": <id_domanda>,
            "selected_answers": { ... dati specifici per tipo domanda ... }
            // Esempio MC_SINGLE: { "answer_option_id": <id_opzione_scelta> }
            // Esempio MC_MULTI: { "answer_option_ids": [<id1>, <id2>, ...] }
            // Esempio TF: { "is_true": true/false }
            // Esempio FILL_BLANK: { "answers": ["risposta1", "risposta2"] }
            // Esempio OPEN_MANUAL: { "answer_text": "Testo della risposta aperta" }
        }
        """
        attempt = self.get_object() # Applica permessi (IsStudentOwnerForAttempt)
        logger.debug(f"[SubmitAnswer Attempt {pk}] Received raw data: {request.data}")


        if attempt.status != QuizAttempt.AttemptStatus.IN_PROGRESS:
            return Response({'detail': 'Questo tentativo non è più in corso.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validazione dati input base
        question_id = request.data.get('question_id')
        selected_answers_data = request.data.get('selected_answers')

        if question_id is None or selected_answers_data is None:
            return Response({'detail': 'question_id e selected_answers sono richiesti.'}, status=status.HTTP_400_BAD_REQUEST)

        # Trova la domanda e verifica che appartenga al quiz del tentativo
        try:
            question = Question.objects.prefetch_related('answer_options').get(pk=question_id, quiz=attempt.quiz)
            logger.debug(f"[SubmitAnswer Attempt {pk}] Found Question ID: {question.id}, Type: {question.question_type}")
        except Question.DoesNotExist:
            return Response({'detail': 'Domanda non trovata o non appartenente a questo quiz.'}, status=status.HTTP_404_NOT_FOUND)
        except (ValueError, TypeError):
             return Response({'detail': 'question_id non valido.'}, status=status.HTTP_400_BAD_REQUEST)


        # Verifica se è la domanda corretta da rispondere (opzionale ma consigliato)
        last_answered_order = attempt.student_answers.aggregate(max_order=AggregateMax('question__order'))['max_order']
        expected_order = 0 if last_answered_order is None else last_answered_order + 1
        if question.order != expected_order:
             logger.warning(f"[SubmitAnswer Attempt {pk}] Tentativo di rispondere a domanda {question_id} (ordine {question.order}) fuori sequenza. Atteso ordine {expected_order}.")
             # Potremmo restituire un errore o semplicemente ignorare e procedere?
             # Per ora, restituiamo un errore per forzare la sequenza.
             return Response({'detail': f'Stai tentando di rispondere alla domanda {question.order} ma dovresti rispondere alla {expected_order}.'}, status=status.HTTP_400_BAD_REQUEST)


        # Validazione specifica per tipo di domanda e creazione/aggiornamento StudentAnswer
        serializer = self.get_serializer(data={
            'quiz_attempt': attempt.id,
            'question': question.id,
            'selected_answers': selected_answers_data
        })

        if not serializer.is_valid():
            logger.warning(f"[SubmitAnswer Attempt {pk}] Serializer validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        logger.debug(f"[SubmitAnswer Attempt {pk}] Serializer validation for selected_answers successful.")

        # --- Logica di Correzione e Calcolo Punteggio ---
        # Questa logica potrebbe essere spostata nel metodo save() di StudentAnswer
        # o rimanere qui per ora.
        is_correct = None
        score = 0.0
        validated_data = serializer.validated_data # Dati validati dal serializer

        try:
            if question.question_type in [QuestionType.MULTIPLE_CHOICE_SINGLE, QuestionType.TRUE_FALSE]:
                logger.debug(f"[SubmitAnswer Attempt {pk}] Handling MC_SINGLE/TF")
                correct_option = question.answer_options.filter(is_correct=True).first()
                selected_option_id = validated_data['selected_answers'].get('answer_option_id')
                logger.debug(f"[SubmitAnswer Attempt {pk}] Correct Option ID: {correct_option.id if correct_option else 'None'}, Selected Option ID: {selected_option_id}")
                if correct_option and selected_option_id == correct_option.id:
                    is_correct = True
                    score = float(question.metadata.get('points_per_correct_answer', 1.0))
                else:
                    is_correct = False
                    score = 0.0

            elif question.question_type == QuestionType.MULTIPLE_CHOICE_MULTIPLE:
                 logger.debug(f"[SubmitAnswer Attempt {pk}] Handling MC_MULTI")
                 correct_option_ids = set(question.answer_options.filter(is_correct=True).values_list('id', flat=True))
                 selected_option_ids = set(validated_data['selected_answers'].get('answer_option_ids', []))
                 logger.debug(f"[SubmitAnswer Attempt {pk}] Correct Option IDs: {correct_option_ids}, Selected Option IDs: {selected_option_ids}")
                 if selected_option_ids == correct_option_ids:
                     is_correct = True
                     score = float(question.metadata.get('points_per_correct_answer', 1.0))
                 else:
                     is_correct = False
                     score = 0.0 # O calcolare punteggio parziale? Per ora tutto o niente.

            elif question.question_type == QuestionType.FILL_BLANK:
                 logger.debug(f"[SubmitAnswer Attempt {pk}] Handling FILL_BLANK")
                 correct_answers_list = question.metadata.get('correct_answers', [])
                 case_sensitive = question.metadata.get('case_sensitive', False)
                 student_answers_list = validated_data['selected_answers'].get('answers', [])
                 points_per_blank = float(question.metadata.get('points_per_blank', 1.0))
                 correct_count = 0

                 logger.debug(f"[SubmitAnswer Attempt {pk}] Correct Answers: {correct_answers_list}, Case Sensitive: {case_sensitive}, Student Answers: {student_answers_list}")

                 # Assicura che ci sia lo stesso numero di risposte fornite e attese
                 if len(student_answers_list) == len(correct_answers_list):
                     all_correct = True
                     for i, correct_ans_options in enumerate(correct_answers_list):
                         student_ans = student_answers_list[i]
                         # correct_ans_options può essere una stringa o una lista di stringhe accettabili
                         is_blank_correct = False
                         possible_correct = [correct_ans_options] if isinstance(correct_ans_options, str) else correct_ans_options
                         for possible in possible_correct:
                             if case_sensitive:
                                 if student_ans == possible:
                                     is_blank_correct = True
                                     break
                             else:
                                 if student_ans.lower() == possible.lower():
                                     is_blank_correct = True
                                     break
                         if is_blank_correct:
                             correct_count += 1
                         else:
                             all_correct = False
                     is_correct = all_correct # True solo se tutti i blank sono corretti
                     score = correct_count * points_per_blank # Punteggio basato sui blank corretti
                 else:
                      logger.warning(f"[SubmitAnswer Attempt {pk}] Numero di risposte FILL_BLANK ({len(student_answers_list)}) non corrisponde al numero atteso ({len(correct_answers_list)}).")
                      is_correct = False
                      score = 0.0


            elif question.question_type == QuestionType.OPEN_ANSWER_MANUAL:
                 logger.debug(f"[SubmitAnswer Attempt {pk}] Handling OPEN_MANUAL")
                 # La correttezza e il punteggio verranno assegnati manualmente dal docente
                 is_correct = None
                 score = 0.0 # Default a 0, verrà aggiornato dal docente

            # Salva la risposta dello studente
            # Usiamo update_or_create per gestire eventuali reinvii della stessa domanda (anche se la logica dell'ordine dovrebbe prevenirlo)
            student_answer, created = StudentAnswer.objects.update_or_create(
                quiz_attempt=attempt,
                question=question,
                defaults={
                    'selected_answers': validated_data['selected_answers'],
                    'is_correct': is_correct,
                    'score': score,
                    'answered_at': timezone.now() # Aggiorna timestamp
                }
            )

            # Restituisci la risposta salvata (o aggiornata)
            # Usa un serializer diverso se vuoi restituire più dettagli
            response_serializer = StudentAnswerSerializer(student_answer)
            logger.info(f"[SubmitAnswer Attempt {pk}] Successfully submitted answer for Question {question.id}. Response: {response_serializer.data}")
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
             # Cattura eccezioni generiche che potrebbero verificarsi durante la logica di correzione o salvataggio
             logger.error(f"[SubmitAnswer Attempt {pk}] Error processing answer for Question {question.id}: {e}", exc_info=True)
             return Response({"detail": "Errore interno durante l'elaborazione della risposta."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=True, methods=['post'], url_path='complete')
    def complete_attempt(self, request, pk=None):
        """
        Marca un tentativo come completato.
        Calcola il punteggio finale se non ci sono domande a correzione manuale.
        Assegna punti al wallet se il quiz è superato.
        """
        attempt = self.get_object() # Applica permessi

        if attempt.status != QuizAttempt.AttemptStatus.IN_PROGRESS:
            return Response({'detail': 'Questo tentativo non è in corso o è già stato completato/valutato.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica se tutte le domande hanno una risposta
        answered_count = attempt.student_answers.count()
        total_questions = attempt.quiz.questions.count()
        if answered_count < total_questions:
             # Potremmo permettere il completamento anche con domande mancanti? Per ora no.
             return Response({'detail': f'Non puoi completare il tentativo finché non hai risposto a tutte le {total_questions} domande (risposte date: {answered_count}).'}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica se ci sono domande in attesa di valutazione manuale
        has_pending_manual = attempt.student_answers.filter(
            question__question_type=QuestionType.OPEN_ANSWER_MANUAL,
            is_correct__isnull=True # Non ancora valutate
        ).exists()

        if has_pending_manual:
            # Se ci sono domande manuali non valutate, imposta lo stato su PENDING_GRADING
            attempt.status = QuizAttempt.AttemptStatus.PENDING_GRADING
            attempt.completed_at = timezone.now() # Registra comunque il tempo di completamento
            attempt.save(update_fields=['status', 'completed_at'])
            logger.info(f"Tentativo {attempt.id} per Quiz {attempt.quiz.id} marcato come PENDING_GRADING.")
            # Restituisci i dettagli aggiornati del tentativo
            serializer = self.get_serializer(attempt) # Usa il serializer di default o QuizAttemptDetailSerializer?
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Se non ci sono domande manuali o sono già state valutate, calcola il punteggio finale e completa
            try:
                with transaction.atomic():
                    # Calcola punteggio finale (somma degli score delle singole risposte)
                    final_score = attempt.calculate_final_score() # Usa il metodo del modello
                    attempt.score = final_score
                    attempt.completed_at = timezone.now()

                    # Determina lo stato finale (COMPLETED o FAILED) e assegna punti/badge
                    # Questa logica è ora incapsulata in assign_completion_points
                    newly_earned_badges = attempt.assign_completion_points() # Questo metodo imposta anche lo stato
                    # Log IMMEDIATAMENTE dopo la chiamata per vedere se l'attributo esiste sull'istanza
                    logger.info(f"[VIEW] After assign_completion_points: points_earned exists? {hasattr(attempt, 'points_earned')}, Value: {getattr(attempt, 'points_earned', 'N/A')}")

                    # Salva tutte le modifiche al tentativo
                    attempt.save()

                    # Aggiorna il progresso nel percorso, se applicabile
                    attempt.update_pathway_progress()

                    # Restituisci i dettagli completi, inclusi i nuovi badge
                    serializer = QuizAttemptDetailSerializer(attempt) # Usa il serializer dettagliato
                    response_data = serializer.data
                    # Assicurati che newly_earned_badges sia incluso se presente
                    if newly_earned_badges:
                         # Serializza i badge semplici
                         badge_serializer = SimpleBadgeSerializer(newly_earned_badges, many=True)
                         response_data['newly_earned_badges'] = badge_serializer.data
                    else:
                         response_data['newly_earned_badges'] = [] # Assicura che sia sempre presente

                    # Log spostato qui, dopo che tutti i calcoli, salvataggi e aggiornamenti sono avvenuti
                    # Si accede a attempt.points_earned che è un attributo dell'istanza, non del DB
                    logger.info(f"Tentativo {attempt.id} per Quiz {attempt.quiz.id} completato. Score: {attempt.score}, Stato: {attempt.status}, Punti: {getattr(attempt, 'points_earned', 'N/A')}") # Usiamo getattr per sicurezza

                    return Response(response_data, status=status.HTTP_200_OK)

            except Exception as e:
                 logger.error(f"Errore durante il completamento/calcolo punteggio del tentativo {attempt.id}: {e}", exc_info=True)
                 return Response({'detail': 'Errore interno durante il completamento del tentativo.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- ViewSet per Docenti (Grading) ---
class TeacherGradingViewSet(viewsets.GenericViewSet):
    """ Endpoint per Docenti per visualizzare e correggere risposte manuali. """
    queryset = StudentAnswer.objects.filter(
        question__question_type=QuestionType.OPEN_ANSWER_MANUAL
    ) # Queryset base per risposte manuali
    serializer_class = StudentAnswerSerializer # Serializer per visualizzare/aggiornare risposte
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser] # Solo docenti

    def get_queryset(self):
        """ Filtra le risposte manuali per i quiz appartenenti al docente loggato. """
        user = self.request.user
        # Assicurati che sia un docente
        if isinstance(user, User) and user.is_teacher:
            # Filtra le risposte dove il quiz del tentativo associato appartiene al docente
            return StudentAnswer.objects.filter(
                question__question_type=QuestionType.OPEN_ANSWER_MANUAL,
                quiz_attempt__quiz__teacher=user
            ).select_related('quiz_attempt', 'question', 'quiz_attempt__student', 'quiz_attempt__quiz')
        return StudentAnswer.objects.none()

    # Azione per listare le risposte PENDING (is_correct is NULL)
    @action(detail=False, methods=['get'], url_path='pending')
    def list_pending(self, request):
        """ Lista le risposte manuali in attesa di valutazione per il docente loggato. """
        # Applica il filtro del queryset base e aggiungi il filtro per is_correct=None
        pending_answers = self.get_queryset().filter(is_correct__isnull=True).order_by('answered_at')

        # Verifica permessi (get_queryset dovrebbe già filtrare per docente)
        # Controllo manuale ridondante ma sicuro
        # if not all(ans.quiz_attempt.quiz.teacher == request.user for ans in pending_answers):
        #      logger.error(f"Tentativo di accesso non autorizzato a risposte pendenti da utente {request.user.id}")
        #      # Non sollevare PermissionDenied qui, semplicemente non mostrare dati non autorizzati
        #      # Il filtro queryset è il modo corretto per gestire questo.

        serializer = self.get_serializer(pending_answers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='grade')
    def grade_answer(self, request, pk=None):
        """ Permette al docente di assegnare un punteggio a una risposta manuale. """
        student_answer = self.get_object() # Applica permessi (tramite get_queryset)

        # Verifica che la risposta sia effettivamente manuale e non ancora valutata
        if student_answer.question.question_type != QuestionType.OPEN_ANSWER_MANUAL:
            return Response({'detail': 'Questa non è una risposta a una domanda aperta.'}, status=status.HTTP_400_BAD_REQUEST)
        if student_answer.is_correct is not None:
            return Response({'detail': 'Questa risposta è già stata valutata.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validazione input docente
        score_str = request.data.get('score')
        is_correct_str = request.data.get('is_correct') # Accetta 'true'/'false' o booleano

        if score_str is None or is_correct_str is None:
             return Response({'detail': 'score e is_correct sono richiesti.'}, status=status.HTTP_400_BAD_REQUEST)

        # Converti e valida score
        try:
            score = float(score_str)
            max_score = float(student_answer.question.metadata.get('max_score', 1.0)) # Default a 1 se non specificato
            if score < 0 or score > max_score:
                 raise ValueError(f"Il punteggio deve essere tra 0 e {max_score}.")
        except (ValueError, TypeError):
             return Response({'detail': f'Punteggio non valido. Deve essere un numero tra 0 e {student_answer.question.metadata.get("max_score", "N/D")}.'}, status=status.HTTP_400_BAD_REQUEST)

        # Converti e valida is_correct
        if isinstance(is_correct_str, bool):
            is_correct = is_correct_str
        elif isinstance(is_correct_str, str):
            if is_correct_str.lower() == 'true':
                is_correct = True
            elif is_correct_str.lower() == 'false':
                is_correct = False
            else:
                 return Response({'detail': 'is_correct deve essere true o false.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
             return Response({'detail': 'is_correct deve essere un booleano o una stringa "true"/"false".'}, status=status.HTTP_400_BAD_REQUEST)


        # Aggiorna la risposta dello studente
        student_answer.score = score
        student_answer.is_correct = is_correct
        student_answer.save(update_fields=['score', 'is_correct'])
        logger.info(f"Docente {request.user.id} ha valutato risposta {student_answer.id} (Tentativo: {student_answer.quiz_attempt.id}) con score={score}, is_correct={is_correct}")

        # --- Logica post-valutazione ---
        # Verifica se TUTTE le domande manuali del tentativo sono state valutate
        attempt = student_answer.quiz_attempt
        all_manual_answers_graded = not attempt.student_answers.filter(
            question__question_type=QuestionType.OPEN_ANSWER_MANUAL,
            is_correct__isnull=True
        ).exists()

        if all_manual_answers_graded and attempt.status == QuizAttempt.AttemptStatus.PENDING_GRADING:
            logger.info(f"Tutte le risposte manuali per il tentativo {attempt.id} sono state valutate. Procedo al completamento finale.")
            try:
                with transaction.atomic():
                    # Ricalcola punteggio finale e assegna punti/badge
                    final_score = attempt.calculate_final_score()
                    attempt.score = final_score
                    # Riassegna punti e stato (COMPLETED/FAILED)
                    newly_earned_badges = attempt.assign_completion_points()
                    # Salva le modifiche finali al tentativo
                    attempt.save()
                    # Aggiorna progresso percorso
                    attempt.update_pathway_progress()
                    logger.info(f"Tentativo {attempt.id} completato finalizzato dopo valutazione manuale. Score: {attempt.score}, Stato: {attempt.status}")
                    # Qui potresti inviare una notifica allo studente
            except Exception as e:
                 logger.error(f"Errore durante il completamento finale del tentativo {attempt.id} dopo valutazione manuale: {e}", exc_info=True)
                 # Non bloccare la risposta del docente, ma logga l'errore

        # Restituisci la risposta aggiornata
        serializer = self.get_serializer(student_answer)
        return Response(serializer.data)


# --- View Generiche per Studenti (Lista Quiz/Percorsi Assegnati) ---

class StudentAssignedQuizzesView(generics.ListAPIView):
    """
    Restituisce l'elenco dei Quiz assegnati allo studente autenticato.
    Utilizza StudentQuizDashboardSerializer per includere info sull'ultimo tentativo.
    """
    serializer_class = StudentQuizDashboardSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudentAuthenticated]

    def get_queryset(self):
        student = self.request.user # Assicurato da IsStudentAuthenticated
        if not isinstance(student, Student):
             logger.error(f"Errore: request.user non è un'istanza Student nella StudentAssignedQuizzesView per user ID {request.user.id}")
             # Restituisci un queryset vuoto o solleva un errore?
             return Quiz.objects.none()

        # Recupera ID dei Quiz assegnati direttamente
        assigned_quiz_ids = QuizAssignment.objects.filter(
            student=student
        ).values_list('quiz_id', flat=True)

        # Recupera ID dei Quiz contenuti nei percorsi assegnati allo studente
        quiz_ids_in_assigned_pathways = PathwayQuiz.objects.filter(
            pathway__assignments__student=student # Filtra per percorsi assegnati allo studente
        ).values_list('quiz_id', flat=True)

        # Combina gli ID unici
        unique_quiz_ids = set(assigned_quiz_ids) | set(quiz_ids_in_assigned_pathways)

        # Filtra i Quiz per ID e precarica i tentativi dello studente
        student_attempts_prefetch = Prefetch(
            'attempts',
            queryset=QuizAttempt.objects.filter(student=student).order_by('-started_at'),
            to_attr='student_attempts_for_dashboard'
        )
        queryset = Quiz.objects.filter(id__in=unique_quiz_ids).select_related('teacher').prefetch_related(
            student_attempts_prefetch
        )
        return queryset

    def get_serializer_context(self):
        """ Aggiunge la request al contesto per accedere all'utente nel serializer. """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class StudentAssignedPathwaysView(generics.ListAPIView):
    """
    Restituisce l'elenco dei Percorsi assegnati allo studente autenticato.
    Utilizza StudentPathwayDashboardSerializer per includere info sul progresso.
    """
    serializer_class = StudentPathwayDashboardSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudentAuthenticated]

    def get_queryset(self):
        student = self.request.user
        if not isinstance(student, Student):
             logger.error(f"Errore: request.user non è un'istanza Student nella StudentAssignedPathwaysView per user ID {request.user.id}")
             return Pathway.objects.none()

        # Recupera ID dei Percorsi assegnati
        assigned_pathway_ids = PathwayAssignment.objects.filter(
            student=student
        ).values_list('pathway_id', flat=True)

        # Filtra i Percorsi per ID e precarica il progresso dello studente
        student_progress_prefetch = Prefetch(
            'progresses',
            queryset=PathwayProgress.objects.filter(student=student).order_by('-completed_at'), # Usa completed_at
            to_attr='student_progress_for_dashboard'
        )
        queryset = Pathway.objects.filter(id__in=assigned_pathway_ids).select_related('teacher').prefetch_related(
            student_progress_prefetch
        )
        return queryset

    def get_serializer_context(self):
        """ Aggiunge la request al contesto. """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# --- View Dettaglio Percorso per Studente ---

class PathwayAttemptDetailView(generics.RetrieveAPIView):
    """
    Restituisce i dettagli di un Percorso specifico per lo studente autenticato,
    includendo lo stato di avanzamento e il prossimo quiz da affrontare.
    """
    queryset = Pathway.objects.prefetch_related(
        'quizzes', 'progresses', 'assignments' # Precarica relazioni utili
    )
    serializer_class = PathwayAttemptDetailSerializer # Usa il serializer specifico
    permission_classes = [permissions.IsAuthenticated, IsStudentAuthenticated] # Solo studenti

    def get_object(self):
        """
        Recupera il percorso e verifica che sia assegnato allo studente.
        Passa lo studente al contesto del serializer.
        """
        pathway = super().get_object()
        student = self.request.user

        # Verifica assegnazione
        is_assigned = PathwayAssignment.objects.filter(
            pathway=pathway,
            student=student
        ).exists()

        if not is_assigned:
            logger.warning(f"Studente {student.id} ha tentato di accedere al percorso {pathway.id} non assegnato.")
            raise PermissionDenied("Non sei assegnato a questo percorso.")

        # Passa lo studente al contesto per usarlo nel serializer
        self.serializer_context = self.get_serializer_context()
        self.serializer_context['student'] = student

        return pathway

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Usa il contesto aggiornato con lo studente
        serializer = self.get_serializer(instance, context=self.serializer_context)
        return Response(serializer.data)
