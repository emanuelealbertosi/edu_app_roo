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
from django.db.models import Q, F, OuterRef, Subquery, Count, Prefetch # Import per Q, Subquery, Count e Prefetch

from .models import (
    QuizTemplate, QuestionTemplate, AnswerOptionTemplate,
    Quiz, Question, AnswerOption, Pathway, PathwayQuiz,
    QuizAttempt, StudentAnswer, PathwayProgress, QuestionType,
    QuizAssignment, PathwayAssignment, PathwayTemplate, PathwayQuizTemplate, # Importa i modelli Assignment e Template Percorsi
    Notification, NotificationType # NUOVI IMPORT PER NOTIFICHE
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
    QuizAssignmentSerializer, PathwayAssignmentSerializer,
    # Nuovi serializer per azioni di assegnazione
    AssignQuizSerializer, AssignPathwaySerializer,
    NotificationSerializer, # NUOVO IMPORT PER NOTIFICHE
    # Serializers per TeacherGradingViewSet
    PendingQuizAttemptSerializer,
    GradingQuizAttemptDetailSerializer,
    GradeSubmissionSerializer
)
from .permissions import (
    IsAdminOrReadOnly, IsQuizTemplateOwnerOrAdmin, IsQuizOwnerOrAdmin, IsPathwayOwnerOrAdmin, # Updated IsPathwayOwner -> IsPathwayOwnerOrAdmin
    IsStudentOwnerForAttempt, IsTeacherOfStudentForAttempt, IsAnswerOptionOwner # Aggiunto IsAnswerOptionOwner
    # Rimosso IsTeacherOwner che non esiste
)
from apps.users.permissions import IsAdminUser, IsTeacherUser, IsStudent, IsStudentAuthenticated # Import IsStudentAuthenticated
from apps.users.models import UserRole, Student, User # Import modelli utente e User
from apps.rewards.models import Wallet, PointTransaction # Import Wallet e PointTransaction
# Riorganizzato import per chiarezza
from .models import (
    QuizTemplate, QuestionTemplate, AnswerOptionTemplate,
    Quiz, Question, AnswerOption, Pathway, PathwayQuiz,
    QuizAttempt, StudentAnswer, PathwayProgress, QuestionType,
    QuizAssignment, PathwayAssignment, PathwayTemplate, PathwayQuizTemplate,
    Notification, NotificationType, # Assicurati che Quiz e Notification siano importati
)
from apps.student_groups.models import StudentGroup, StudentGroupMembership, GroupAccessRequest # Importa modelli per permessi gruppi
# Importa PermissionDenied da Django Core Exceptions
from django.core.exceptions import PermissionDenied

# Get an instance of a logger
logger = logging.getLogger(__name__)


# --- Notification ViewSet (Student) ---
class NotificationViewSet(viewsets.ReadOnlyModelViewSet): # ReadOnly per ora, le azioni modificano lo stato
    """
    API endpoint per le notifiche dello studente.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudentAuthenticated] # Solo lo studente autenticato

    def get_queryset(self):
        """
        Restituisce solo le notifiche per lo studente autenticato.
        Permette di filtrare per 'is_read=false'.
        """
        user = self.request.user # Dovrebbe essere l'istanza Student grazie a IsStudentAuthenticated
        queryset = Notification.objects.filter(student=user)

        is_read_param = self.request.query_params.get('is_read')
        if is_read_param is not None:
            if is_read_param.lower() == 'false':
                queryset = queryset.filter(is_read=False)
            elif is_read_param.lower() == 'true':
                queryset = queryset.filter(is_read=True)
        return queryset.order_by('-created_at') # Le più recenti prima

    @action(detail=True, methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request, pk=None):
        """
        Segna una specifica notifica come letta.
        """
        notification = self.get_object() # get_object si basa su get_queryset, quindi è già filtrato per utente
        if notification.student != request.user:
            # Questo controllo è una doppia sicurezza, get_queryset dovrebbe già prevenire
            raise DRFPermissionDenied("Non puoi modificare questa notifica.")
        
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            logger.info(f"Notifica {notification.id} per studente {request.user.id} segnata come letta.")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='mark-all-as-read')
    def mark_all_as_read(self, request):
        """
        Segna tutte le notifiche non lette dello studente come lette.
        """
        user = request.user
        updated_count = Notification.objects.filter(student=user, is_read=False).update(is_read=True)
        logger.info(f"{updated_count} notifiche per studente {user.id} segnate come lette.")
        return Response(status=status.HTTP_204_NO_CONTENT)


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

    # --- Azione per Assegnare Template Percorso a Gruppo ---
    @action(detail=True, methods=['post'], url_path='assign-group', permission_classes=[permissions.IsAuthenticated, IsTeacherUser])
    @transaction.atomic # Assicura atomicità per creazione pathway, quiz, e assegnazione
    def assign_group(self, request, pk=None):
        """
        Assegna questo template percorso a un gruppo specificato.
        Crea un'istanza Pathway (con tutte le istanze Quiz) dal template e poi un PathwayAssignment.
        Richiede 'group' (ID del gruppo) e opzionalmente 'due_date' nel payload.
        """
        template = self.get_object() # Ottiene il PathwayTemplate dal pk nell'URL
        teacher = request.user

        # Verifica ownership del template
        if template.teacher != teacher:
            raise DRFPermissionDenied("Non puoi assegnare un template di percorso che non possiedi.")

        group_id = request.data.get('group')
        due_date_str = request.data.get('due_date')

        if not group_id:
            return Response({'group': 'ID del gruppo è richiesto.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            group_id = int(group_id)
            group = StudentGroup.objects.get(pk=group_id, teacher=teacher) # Verifica esistenza e ownership gruppo
        except (ValueError, TypeError):
            return Response({'group': 'ID gruppo non valido.'}, status=status.HTTP_400_BAD_REQUEST)
        except StudentGroup.DoesNotExist:
            return Response({'group': 'Gruppo non trovato o non appartenente a questo docente.'}, status=status.HTTP_404_NOT_FOUND)

        # Valida la data di scadenza se fornita
        due_date = None
        if due_date_str:
            try:
                due_date = timezone.datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                if timezone.is_naive(due_date):
                    due_date = timezone.make_aware(due_date, timezone.utc)
                if due_date < timezone.now():
                     raise ValidationError("La data di scadenza non può essere nel passato.")
            except (ValueError, ValidationError) as e:
                 error_detail = e.detail if isinstance(e, ValidationError) else "Formato data/ora non valido. Usare ISO 8601 (es. YYYY-MM-DDTHH:MM:SSZ)."
                 return Response({'due_date': error_detail}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # --- 1. Creazione Istanza Pathway ---
            instance_title = f"{template.title} (Gruppo: {group.name})"
            new_pathway = Pathway.objects.create(
                teacher=teacher,
                source_template=template,
                title=instance_title,
                description=template.description,
                metadata=template.metadata.copy() if template.metadata else {}
            )

            # --- 2. Creazione Istanze Quiz e Collegamenti PathwayQuiz ---
            pathway_quizzes_to_create = []
            # Itera sui template quiz associati al template percorso, ordinati
            # CORREZIONE: Usare il related_name predefinito 'pathwayquiztemplate_set'
            for pq_template in template.pathwayquiztemplate_set.select_related('quiz_template').order_by('order'):
                quiz_template = pq_template.quiz_template

                # --- Logica (replicata) per creare istanza Quiz da QuizTemplate ---
                quiz_instance_title = f"{quiz_template.title} (Percorso: {new_pathway.title})"
                new_quiz = Quiz.objects.create(
                    teacher=teacher,
                    source_template=quiz_template,
                    title=quiz_instance_title,
                    description=quiz_template.description,
                    metadata=quiz_template.metadata.copy() if quiz_template.metadata else {}
                )
                questions_to_create = []
                options_to_create_map = {}
                question_order_counter = 0
                for q_template in quiz_template.question_templates.prefetch_related('answer_option_templates').order_by('order'):
                    new_question = Question(
                        quiz=new_quiz, text=q_template.text, question_type=q_template.question_type,
                        order=question_order_counter, metadata=q_template.metadata.copy() if q_template.metadata else {}
                    )
                    questions_to_create.append(new_question)
                    options_to_create_map[q_template.id] = []
                    for opt_template in q_template.answer_option_templates.order_by('order'):
                         options_to_create_map[q_template.id].append(
                             AnswerOption(text=opt_template.text, is_correct=opt_template.is_correct, order=opt_template.order)
                         )
                    question_order_counter += 1 # Incrementa per la prossima domanda

                created_questions = Question.objects.bulk_create(questions_to_create)
                created_question_map = {q.text: q for q in created_questions} # Usa testo+quiz come chiave potenziale se ordine non basta

                options_final_list = []
                # Ricostruisci mappa ID template -> oggetto Question creato
                template_to_instance_map = {}
                q_templates_list = list(quiz_template.question_templates.all()) # Ottieni la lista per fare il mapping
                for i, q_instance in enumerate(created_questions):
                    if i < len(q_templates_list):
                        template_to_instance_map[q_templates_list[i].id] = q_instance

                for q_template_id, options_list in options_to_create_map.items():
                    newly_created_question = template_to_instance_map.get(q_template_id)
                    if newly_created_question:
                        for option in options_list:
                            option.question = newly_created_question
                            options_final_list.append(option)
                if options_final_list:
                    AnswerOption.objects.bulk_create(options_final_list)
                # --- Fine logica creazione istanza Quiz ---

                # Aggiungi alla lista per bulk create di PathwayQuiz
                pathway_quizzes_to_create.append(
                    PathwayQuiz(pathway=new_pathway, quiz=new_quiz, order=pq_template.order)
                )

            # Crea tutti i collegamenti PathwayQuiz in una sola query
            if pathway_quizzes_to_create:
                PathwayQuiz.objects.bulk_create(pathway_quizzes_to_create)

            # --- 3. Creazione Assegnazione Pathway ---
            assignment, created = PathwayAssignment.objects.get_or_create(
                pathway=new_pathway,
                group=group,
                defaults={'assigned_at': timezone.now(), 'due_date': due_date}
            )

            if not created:
                # Aggiorna data scadenza se necessario
                if due_date is not None and assignment.due_date != due_date:
                    assignment.due_date = due_date
                    assignment.save(update_fields=['due_date'])
                logger.info(f"Assegnazione Percorso {new_pathway.id} a Gruppo {group.id} già esistente. Data scadenza aggiornata se necessario.")

            logger.info(f"Template Percorso {template.id} assegnato a Gruppo {group.id} (creata Istanza Percorso {new_pathway.id}, Assegnazione ID {assignment.id})")

            # Serializza l'assegnazione per la risposta
            assignment_serializer = PathwayAssignmentSerializer(assignment) # Assicurati che esista e sia importato
            return Response(assignment_serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
             logger.error(f"Errore di integrità durante assegnazione template percorso {template.id} a gruppo {group.id}: {e}", exc_info=True)
             return Response({'detail': f'Errore di integrità durante l\'assegnazione: {e}'}, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            logger.error(f"Errore imprevisto durante assegnazione template percorso {template.id} a gruppo {group.id}: {e}", exc_info=True)
            # Potrebbe essere utile fare rollback manuale se non si usa @transaction.atomic, ma qui lo usiamo.
            return Response({'detail': f'Errore interno durante l\'assegnazione: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    # Per ora, questo ViewSet gestisce solo il CRUD del QuizTemplate stesso.

    # --- Azione per Assegnare Template a Gruppo ---
    @action(detail=True, methods=['post'], url_path='assign-group', permission_classes=[permissions.IsAuthenticated, IsTeacherUser])
    def assign_group(self, request, pk=None):
        """
        Assegna questo template quiz a un gruppo specificato.
        Crea un'istanza Quiz dal template e poi un QuizAssignment.
        Richiede 'group' (ID del gruppo) e opzionalmente 'due_date' nel payload.
        """
        template = self.get_object() # Ottiene il QuizTemplate dal pk nell'URL
        teacher = request.user

        # Verifica ownership del template (già fatto da get_object con permessi, ma doppia sicurezza)
        if template.teacher != teacher:
            raise DRFPermissionDenied("Non puoi assegnare un template che non possiedi.")

        group_id = request.data.get('group')
        due_date_str = request.data.get('due_date')

        if not group_id:
            return Response({'group': 'ID del gruppo è richiesto.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            group_id = int(group_id)
            group = get_object_or_404(StudentGroup, pk=group_id) # Recupera il gruppo
        except (ValueError, TypeError):
            return Response({'group': 'ID gruppo non valido.'}, status=status.HTTP_400_BAD_REQUEST)
        except StudentGroup.DoesNotExist:
             return Response({'group': 'Gruppo non trovato.'}, status=status.HTTP_404_NOT_FOUND) # Già gestito da get_object_or_404 ma per sicurezza

        # --- Controllo Permessi sul Gruppo ---
        is_owner = (group.owner == teacher)
        has_approved_access = GroupAccessRequest.objects.filter(
            group=group,
            requesting_teacher=teacher,
            status=GroupAccessRequest.AccessStatus.APPROVED
        ).exists()

        if not (is_owner or has_approved_access):
            logger.warning(f"Utente {teacher.id} ha tentato di assegnare template quiz {template.id} al gruppo {group.id} senza permesso.")
            raise DRFPermissionDenied("Non hai i permessi per assegnare contenuti a questo gruppo.")
        # --- Fine Controllo Permessi ---

        # Valida la data di scadenza se fornita
        due_date = None
        if due_date_str:
            try:
                # Prova a parsare la data/ora
                due_date = timezone.datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                # Rendi timezone-aware se non lo è (assumendo UTC se non specificato)
                if timezone.is_naive(due_date):
                    due_date = timezone.make_aware(due_date, timezone.utc)
                # Verifica che la data non sia nel passato
                if due_date < timezone.now():
                     raise ValidationError("La data di scadenza non può essere nel passato.")
            except (ValueError, ValidationError) as e:
                 error_detail = e.detail if isinstance(e, ValidationError) else "Formato data/ora non valido. Usare ISO 8601 (es. YYYY-MM-DDTHH:MM:SSZ)."
                 return Response({'due_date': error_detail}, status=status.HTTP_400_BAD_REQUEST)


        try:
            # Usa l'helper del QuizViewSet per creare l'istanza Quiz
            # Dobbiamo istanziare QuizViewSet temporaneamente o spostare l'helper?
            # Per ora, replichiamo la logica essenziale qui o chiamiamo l'helper se possibile.
            # Assumiamo di avere accesso a _create_quiz_instance_from_template (potrebbe richiedere refactoring)
            # Se non accessibile direttamente, potremmo dover chiamare l'endpoint 'create-from-template' internamente
            # o duplicare la logica. Duplichiamo per semplicità momentanea.

            with transaction.atomic():
                # 1. Crea l'istanza Quiz dal template
                # Titolo per la nuova istanza (potrebbe essere personalizzabile in futuro)
                instance_title = f"{template.title} (Gruppo: {group.name})"

                # --- Logica duplicata da _create_quiz_instance_from_template ---
                new_quiz = Quiz.objects.create(
                    teacher=teacher,
                    source_template=template,
                    title=instance_title,
                    description=template.description,
                    metadata=template.metadata.copy() if template.metadata else {}
                )
                questions_to_create = []
                options_to_create_map = {}
                question_order_counter = 0
                for q_template in template.question_templates.prefetch_related('answer_option_templates').order_by('order'):
                    new_question = Question(
                        quiz=new_quiz, text=q_template.text, question_type=q_template.question_type,
                        order=question_order_counter, metadata=q_template.metadata.copy() if q_template.metadata else {}
                    )
                    questions_to_create.append(new_question)
                    question_order_counter += 1
                    options_to_create_map[q_template.id] = []
                    for opt_template in q_template.answer_option_templates.order_by('order'):
                         options_to_create_map[q_template.id].append(
                             AnswerOption(text=opt_template.text, is_correct=opt_template.is_correct, order=opt_template.order)
                         )
                created_questions = Question.objects.bulk_create(questions_to_create)
                created_question_map = {q.order: q for q in created_questions}
                options_final_list = []
                for q_template_id, options_list in options_to_create_map.items():
                    q_template_order = QuestionTemplate.objects.get(id=q_template_id).order
                    newly_created_question = created_question_map.get(q_template_order)
                    if newly_created_question:
                        for option in options_list:
                            option.question = newly_created_question
                            options_final_list.append(option)
                if options_final_list:
                    AnswerOption.objects.bulk_create(options_final_list)
                # --- Fine logica duplicata ---

                # 2. Crea l'assegnazione per il gruppo e il nuovo quiz, impostando assigned_by
                assignment, created = QuizAssignment.objects.get_or_create(
                    quiz=new_quiz,
                    group=group,
                    student=None, # Assicurati che sia None per assegnazioni a gruppo
                    defaults={
                        'assigned_by': teacher, # Imposta chi ha assegnato
                        'assigned_at': timezone.now(),
                        'due_date': due_date
                    }
                )

                if not created:
                    # Se esisteva già, aggiorna la data di scadenza e assigned_by se necessario
                    update_fields = []
                    if due_date is not None and assignment.due_date != due_date:
                        assignment.due_date = due_date
                        update_fields.append('due_date')
                    # Potremmo voler aggiornare assigned_by se l'assegnazione esisteva ma era stata fatta da un altro utente?
                    # Per ora, assumiamo che chi la "riassegna" ne diventi il "responsabile" (assigned_by)
                    if assignment.assigned_by != teacher:
                         assignment.assigned_by = teacher
                         update_fields.append('assigned_by')

                    if update_fields:
                        assignment.save(update_fields=update_fields)
                        logger.info(f"Assegnazione Quiz {new_quiz.id} a Gruppo {group.id} già esistente. Campi aggiornati: {update_fields}.")
                    else:
                         logger.info(f"Assegnazione Quiz {new_quiz.id} a Gruppo {group.id} già esistente. Nessun campo da aggiornare.")

                else:
                     logger.info(f"Template Quiz {template.id} assegnato a Gruppo {group.id} (creata Istanza Quiz {new_quiz.id}, Nuova Assegnazione ID {assignment.id} da utente {teacher.id})")

                # Serializza l'assegnazione creata/trovata per la risposta
                assignment_serializer = QuizAssignmentSerializer(assignment) # Assicurati che esista e sia importato
                return Response(assignment_serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
             logger.error(f"Errore di integrità durante assegnazione template {template.id} a gruppo {group.id}: {e}", exc_info=True)
             return Response({'detail': f'Errore di integrità durante l\'assegnazione: {e}'}, status=status.HTTP_409_CONFLICT) # Conflict
        except Exception as e:
            logger.error(f"Errore imprevisto durante assegnazione template {template.id} a gruppo {group.id}: {e}", exc_info=True)
            return Response({'detail': f'Errore interno durante l\'assegnazione: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # --- Azione per Assegnare Template a Studente Singolo ---
    @action(detail=True, methods=['post'], url_path='assign-student', permission_classes=[permissions.IsAuthenticated, IsTeacherUser])
    def assign_student(self, request, pk=None):
        """
        Assegna questo template quiz a uno studente specificato.
        Crea un'istanza Quiz dal template e poi un QuizAssignment.
        Richiede 'student' (ID dello studente) e opzionalmente 'due_date' nel payload.
        """
        template = self.get_object() # Ottiene il QuizTemplate dal pk nell'URL
        teacher = request.user

        # Verifica ownership del template
        if template.teacher != teacher:
            raise DRFPermissionDenied("Non puoi assegnare un template che non possiedi.")

        student_id = request.data.get('student')
        due_date_str = request.data.get('due_date')

        if not student_id:
            return Response({'student': 'ID dello studente è richiesto.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student_id = int(student_id)
            # Verifica che lo studente esista (non necessariamente che sia "del docente",
            # un docente potrebbe assegnare a qualsiasi studente nel sistema? Da chiarire requisiti.
            # Per ora, verifichiamo solo l'esistenza.
            student = Student.objects.get(id=student_id) # CORRETTO: Usa l'ID primario dello studente
        except (ValueError, TypeError):
            return Response({'student': 'ID studente non valido.'}, status=status.HTTP_400_BAD_REQUEST)
        except Student.DoesNotExist:
            return Response({'student': 'Studente non trovato.'}, status=status.HTTP_404_NOT_FOUND)

        # Valida la data di scadenza se fornita (logica identica a assign_group)
        due_date = None
        if due_date_str:
            try:
                due_date = timezone.datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                if timezone.is_naive(due_date):
                    due_date = timezone.make_aware(due_date, timezone.utc)
                if due_date < timezone.now():
                     raise ValidationError("La data di scadenza non può essere nel passato.")
            except (ValueError, ValidationError) as e:
                 error_detail = e.detail if isinstance(e, ValidationError) else "Formato data/ora non valido. Usare ISO 8601 (es. YYYY-MM-DDTHH:MM:SSZ)."
                 return Response({'due_date': error_detail}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # 1. Crea l'istanza Quiz dal template (logica identica a assign_group)
                instance_title = f"{template.title} (Studente: {student.full_name})" # Titolo specifico per studente (CORRETTO)

                # --- Logica duplicata da _create_quiz_instance_from_template ---
                # TODO: Refactor questa logica in un metodo helper riutilizzabile
                new_quiz = Quiz.objects.create(
                    teacher=teacher,
                    source_template=template,
                    title=instance_title,
                    description=template.description,
                    metadata=template.metadata.copy() if template.metadata else {}
                )
                questions_to_create = []
                options_to_create_map = {}
                question_order_counter = 0
                for q_template in template.question_templates.prefetch_related('answer_option_templates').order_by('order'):
                    new_question = Question(
                        quiz=new_quiz, text=q_template.text, question_type=q_template.question_type,
                        order=question_order_counter, metadata=q_template.metadata.copy() if q_template.metadata else {}
                    )
                    questions_to_create.append(new_question)
                    question_order_counter += 1
                    options_to_create_map[q_template.id] = []
                    for opt_template in q_template.answer_option_templates.order_by('order'):
                         options_to_create_map[q_template.id].append(
                             AnswerOption(text=opt_template.text, is_correct=opt_template.is_correct, order=opt_template.order)
                         )
                created_questions = Question.objects.bulk_create(questions_to_create)
                # Mappa ID template -> istanza domanda creata (più robusto dell'ordine)
                template_to_instance_map = {}
                q_templates_list = list(template.question_templates.all()) # Ottieni la lista per fare il mapping
                for i, q_instance in enumerate(created_questions):
                    if i < len(q_templates_list):
                        template_to_instance_map[q_templates_list[i].id] = q_instance

                options_final_list = []
                for q_template_id, options_list in options_to_create_map.items():
                    newly_created_question = template_to_instance_map.get(q_template_id)
                    if newly_created_question:
                        for option in options_list:
                            option.question = newly_created_question
                            options_final_list.append(option)
                if options_final_list:
                    AnswerOption.objects.bulk_create(options_final_list)
                # --- Fine logica duplicata ---

                # 2. Crea l'assegnazione per lo studente e il nuovo quiz
                assignment, created = QuizAssignment.objects.get_or_create(
                    quiz=new_quiz,
                    student=student, # Usa l'oggetto Student trovato
                    defaults={'assigned_at': timezone.now(), 'due_date': due_date}
                )

                if not created:
                    # Se esisteva già, aggiorna la data di scadenza se fornita una nuova
                    if due_date is not None and assignment.due_date != due_date:
                        assignment.due_date = due_date
                        assignment.save(update_fields=['due_date'])
                    logger.info(f"Assegnazione Quiz {new_quiz.id} a Studente {student.full_name} (ID: {student_id}) già esistente. Data scadenza aggiornata se necessario.") # CORRETTO

                logger.info(f"Template Quiz {template.id} assegnato a Studente {student.full_name} (ID: {student_id}) (creata Istanza Quiz {new_quiz.id}, Assegnazione ID {assignment.id})") # CORRETTO

                # Serializza l'assegnazione creata/trovata per la risposta
                assignment_serializer = QuizAssignmentSerializer(assignment)
                return Response(assignment_serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError as e:
             logger.error(f"Errore di integrità durante assegnazione template {template.id} a studente {student_id}: {e}", exc_info=True)
             return Response({'detail': f'Errore di integrità durante l\'assegnazione: {e}'}, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            logger.error(f"Errore imprevisto durante assegnazione template {template.id} a studente {student_id}: {e}", exc_info=True)
            return Response({'detail': f'Errore interno durante l\'assegnazione: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            return Quiz.objects.filter(teacher=user).select_related('teacher')
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

from django.db.models import F # Assicurati che F sia importato all'inizio del file

class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    # Permetti a Docenti o Admin
    permission_classes = [(IsTeacherUser | IsAdminUser)]

    def get_queryset(self):
        quiz = get_object_or_404(Quiz, pk=self.kwargs['quiz_pk'])
        # Verifica ownership o ruolo admin
        if not isinstance(self.request.user, User) or (not self.request.user.is_admin and quiz.teacher != self.request.user):
             raise DRFPermissionDenied("Non hai accesso a questo quiz.") # Usa DRFPermissionDenied
        # Ordina per 'order' per coerenza
        return Question.objects.filter(quiz=quiz).order_by('order')

    def perform_create(self, serializer):
        quiz = get_object_or_404(Quiz, pk=self.kwargs['quiz_pk'])
        if not isinstance(self.request.user, User) or quiz.teacher != self.request.user:
             raise DRFPermissionDenied("Non puoi aggiungere domande a questo quiz.") # Usa DRFPermissionDenied
        # Calcola il prossimo ordine disponibile
        last_order = Question.objects.filter(quiz=quiz).aggregate(Max('order'))['order__max']
        # L'ordine parte da 1, non da 0
        next_order = 0 if last_order is None else last_order + 1 # Ordine 0-based
        # Salva la domanda con il quiz e l'ordine calcolato
        serializer.save(quiz=quiz, order=next_order)

    @transaction.atomic # Assicura che l'eliminazione e il riordino avvengano insieme
    def perform_destroy(self, instance):
        """
        Elimina la domanda e riordina le domande successive nello stesso quiz.
        """
        quiz = instance.quiz
        deleted_order = instance.order
        instance.delete()

        # Riordina le domande successive
        questions_to_reorder = Question.objects.filter(
            quiz=quiz,
            order__gt=deleted_order
        ).order_by('order')

        # Aggiorna l'ordine in modo efficiente se possibile
        # Nota: bulk_update potrebbe non funzionare direttamente con F() in tutte le versioni/DB
        # Un approccio più sicuro è iterare, ma meno performante per molti aggiornamenti.
        # Tentativo con update() e F():
        updated_count = questions_to_reorder.update(order=F('order') - 1)
        logger.info(f"Riordinate {updated_count} domande nel quiz {quiz.id} dopo l'eliminazione della domanda con ordine {deleted_order}.")

        # Fallback se update() non funziona come previsto o per maggiore robustezza:
        # questions_list = list(questions_to_reorder) # Esegui la query
        # for i, question in enumerate(questions_list):
        #     question.order = deleted_order + i # Assegna il nuovo ordine sequenziale
        # Question.objects.bulk_update(questions_list, ['order'])
        # logger.info(f"Riordinate {len(questions_list)} domande nel quiz {quiz.id} dopo l'eliminazione.")

class AnswerOptionViewSet(viewsets.ModelViewSet):
     serializer_class = AnswerOptionSerializer
     # Usa il nuovo permesso IsAnswerOptionOwner
     permission_classes = [IsAnswerOptionOwner]

     def get_queryset(self):
         question = get_object_or_404(Question, pk=self.kwargs['question_pk'])
         # Verifica ownership o ruolo admin
         if not isinstance(self.request.user, User) or (not self.request.user.is_admin and question.quiz.teacher != self.request.user):
              raise DRFPermissionDenied("Non hai accesso a questa domanda.") # Usa DRFPermissionDenied
         return AnswerOption.objects.filter(question=question)

     def perform_create(self, serializer):
         question = get_object_or_404(Question, pk=self.kwargs['question_pk'])
         if not isinstance(self.request.user, User) or question.quiz.teacher != self.request.user:
              raise DRFPermissionDenied("Non puoi aggiungere opzioni a questa domanda.") # Usa DRFPermissionDenied
         # Calcola il prossimo ordine disponibile per questa domanda
         last_order = AnswerOption.objects.filter(question=question).aggregate(Max('order'))['order__max']
         # L'ordine parte da 1 (o dal successivo se esistono già opzioni)
         next_order = 1 if last_order is None else last_order + 1
         # Salva l'opzione con la domanda e l'ordine calcolato
         serializer.save(question=question, order=next_order)

class PathwayViewSet(viewsets.ModelViewSet):
    """ API endpoint per i Percorsi (Docente). """
    serializer_class = PathwaySerializer
    permission_classes = [permissions.IsAuthenticated, IsPathwayOwnerOrAdmin] # Updated permission

    def get_queryset(self):
        user = self.request.user

        # Allow DRF to find the object for detail actions. Permissions handle access.
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'add_quiz', 'assign_student_pathway']: # Added detail/custom actions
            return Pathway.objects.all().select_related('teacher').prefetch_related('pathwayquiz_set__quiz')

        # Standard filtering for list action.
        if isinstance(user, User) and user.is_admin:
            return Pathway.objects.all().select_related('teacher').prefetch_related('pathwayquiz_set__quiz')
        elif isinstance(user, User) and user.is_teacher:
            return Pathway.objects.filter(teacher=user).select_related('teacher').prefetch_related('pathwayquiz_set__quiz')
        # Empty list for students or others.
        return Pathway.objects.none()

    def perform_create(self, serializer):
        if not isinstance(self.request.user, User) or not self.request.user.is_teacher:
             raise serializers.ValidationError("Solo i Docenti possono creare percorsi.")
        serializer.save(teacher=self.request.user)

    # --- Funzione Helper per Creazione Pathway da Template ---
    def _create_pathway_instance_from_template(self, template: PathwayTemplate, teacher: User, quiz_creator_func, title_override: str = None) -> Pathway:
        """
        Crea una nuova istanza di Pathway (con Quiz interni) a partire da un PathwayTemplate.
        Richiede una funzione (`quiz_creator_func`) per creare le istanze Quiz dai QuizTemplate.
        """
        try:
            with transaction.atomic():
                new_pathway = Pathway.objects.create(
                    teacher=teacher,
                    source_template=template,
                    title=title_override or template.title,
                    description=template.description,
                    metadata=template.metadata.copy() if template.metadata else {}
                )

                pathway_quiz_links = []
                # Itera sui template di quiz associati al template di percorso, ordinati
                for pq_template in template.pathwayquiztemplate_set.select_related('quiz_template').order_by('order'):
                    quiz_template = pq_template.quiz_template
                    # Crea l'istanza Quiz usando la funzione helper passata
                    # Passiamo il teacher corretto (quello che sta creando il percorso)
                    try:
                         new_quiz_instance = quiz_creator_func(quiz_template, teacher) # Non passiamo title_override qui
                         if not new_quiz_instance:
                              raise Exception(f"La funzione di creazione quiz non ha restituito un'istanza per il template {quiz_template.id}")
                    except Exception as quiz_creation_error:
                         logger.error(f"Errore durante la creazione dell'istanza Quiz (template ID {quiz_template.id}) per il Pathway (template ID {template.id}): {quiz_creation_error}", exc_info=True)
                         # Rilancia l'errore per interrompere la transazione atomica
                         raise Exception(f"Impossibile creare il quiz '{quiz_template.title}' dal template.") from quiz_creation_error

                    # Crea l'oggetto per il modello through M2M
                    pathway_quiz_links.append(
                        PathwayQuiz(
                            pathway=new_pathway,
                            quiz=new_quiz_instance,
                            order=pq_template.order
                        )
                    )

                # Crea i collegamenti Pathway-Quiz in blocco
                if pathway_quiz_links:
                    PathwayQuiz.objects.bulk_create(pathway_quiz_links)

                logger.info(f"Creata istanza Pathway ID {new_pathway.id} da Template ID {template.id} per Docente {teacher.id}")
                return new_pathway
        except Exception as e:
            logger.error(f"Errore atomico durante creazione Pathway da template {template.id}: {e}", exc_info=True)
            raise # Rilancia per fallimento API


    @action(detail=True, methods=['post'], url_path='add-quiz', permission_classes=[permissions.IsAuthenticated, IsPathwayOwnerOrAdmin])
    def add_quiz(self, request, pk=None):
        # ... (codice esistente per aggiungere un Quiz *esistente* a un Pathway *esistente*) ...
        # Questa logica rimane invariata per ora, gestisce solo istanze concrete.
        # Potremmo voler aggiungere una logica simile per aggiungere QuizTemplate a PathwayTemplate,
        # ma questo dovrebbe essere gestito da PathwayQuizTemplateViewSet.
        pathway = self.get_object()
        quiz_id = request.data.get('quiz_id')
        order = request.data.get('order')

        if not quiz_id or order is None:
            return Response({'detail': 'quiz_id e order sono richiesti.'}, status=status.HTTP_400_BAD_REQUEST)

        # Assicurati che il quiz esista e appartenga al docente (o sia admin)
        quiz = get_object_or_404(Quiz, pk=quiz_id)
        if quiz.teacher != request.user and not request.user.is_admin:
             raise DRFPermissionDenied("Non puoi usare questo quiz.")

        try:
            order = int(order)
            if order < 0: raise ValueError()
        except (ValueError, TypeError):
            return Response({'order': 'L\'ordine deve essere un intero non negativo.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica ordine esistente
        existing_entry_with_order = PathwayQuiz.objects.filter(
            pathway=pathway,
            order=order
        ).exclude(quiz=quiz).first()

        if existing_entry_with_order:
            return Response(
                {'order': f'L\'ordine {order} è già utilizzato dal quiz "{existing_entry_with_order.quiz.title}" in questo percorso.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pathway_quiz, created = PathwayQuiz.objects.update_or_create(
                pathway=pathway,
                quiz=quiz,
                defaults={'order': order}
            )
            return Response(PathwayQuizSerializer(pathway_quiz).data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
        except IntegrityError as e:
             logger.error(f"Errore di integrità aggiungendo quiz {quiz_id} a percorso {pathway.id}: {e}", exc_info=True)
             return Response({'detail': 'Errore di integrità durante l\'aggiunta del quiz al percorso.'}, status=status.HTTP_400_BAD_REQUEST)

    # --- NUOVE Azioni per Assegnazione/Revoca a Studenti/Gruppi ---

    @action(detail=True, methods=['post'], url_path='assign', permission_classes=[permissions.IsAuthenticated, IsPathwayOwnerOrAdmin])
    def assign(self, request, pk=None):
        """
        Assegna questo Percorso (pk) a uno Studente o a un Gruppo.
        Richiede 'student_id' o 'group_id' nel corpo della richiesta.
        """
        pathway = self.get_object() # Verifica ownership e recupera il percorso
        # Usa il serializer importato all'inizio del file
        serializer = AssignPathwaySerializer(data=request.data, context={'request': request, 'pathway': pathway})

        if serializer.is_valid():
            try:
                assignment = serializer.save()
                # Usa PathwayAssignmentSerializer per la risposta (fatto da to_representation)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                logger.warning(f"Errore validazione assegnazione percorso {pk} da utente {request.user.id}: {e.detail}")
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            except IntegrityError as e:
                 logger.error(f"Errore integrità assegnazione percorso {pk} da utente {request.user.id}: {e}", exc_info=True)
                 return Response({'detail': 'Errore durante il salvataggio dell\'assegnazione.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                 logger.error(f"Errore imprevisto assegnazione percorso {pk} da utente {request.user.id}: {e}", exc_info=True)
                 return Response({'detail': 'Errore interno durante l\'assegnazione.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Errore dati richiesta assegnazione percorso {pk} da utente {request.user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Usa lo stesso RevokeAssignmentSerializer definito in QuizViewSet
    @action(detail=True, methods=['post'], url_path='revoke', permission_classes=[permissions.IsAuthenticated, IsPathwayOwnerOrAdmin])
    def revoke(self, request, pk=None):
        """
        Revoca un'assegnazione specifica (identificata da 'assignment_id') per questo Percorso (pk).
        """
        pathway = self.get_object() # Verifica ownership percorso
        # Assumiamo che RevokeAssignmentSerializer sia definito sopra o importato
        serializer = QuizViewSet.RevokeAssignmentSerializer(data=request.data) # Riusa il serializer

        if serializer.is_valid():
            assignment_id = serializer.validated_data['assignment_id']
            try:
                assignment = get_object_or_404(PathwayAssignment, id=assignment_id, pathway=pathway)
                assignment.delete()
                logger.info(f"Assegnazione Percorso ID {assignment_id} (Percorso ID {pk}) revocata da utente {request.user.id}")
                return Response(status=status.HTTP_204_NO_CONTENT)
            except PathwayAssignment.DoesNotExist:
                 logger.warning(f"Tentativo revoca assegnazione percorso non trovata ID {assignment_id} per percorso {pk} da utente {request.user.id}")
                 return Response({'detail': 'Assegnazione non trovata per questo percorso.'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                 logger.error(f"Errore imprevisto revoca assegnazione percorso {assignment_id} (Percorso {pk}) da utente {request.user.id}: {e}", exc_info=True)
                 return Response({'detail': 'Errore interno durante la revoca.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Errore dati richiesta revoca assegnazione percorso {pk} da utente {request.user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['delete'], url_path='remove-quiz/(?P<pathway_quiz_pk>[^/.]+)', permission_classes=[permissions.IsAuthenticated, IsPathwayOwnerOrAdmin])
    def remove_quiz(self, request, pk=None, pathway_quiz_pk=None):
        """
        Rimuove una specifica relazione PathwayQuiz (un quiz da un percorso).
        """
        pathway = self.get_object() # Assicura che l'utente abbia accesso al percorso

        try:
            # Trova la specifica relazione PathwayQuiz da eliminare
            pathway_quiz_entry = get_object_or_404(
                PathwayQuiz,
                pk=pathway_quiz_pk,
                pathway=pathway # Assicura che appartenga al percorso corretto
            )
            deleted_order = pathway_quiz_entry.order
            quiz_title = pathway_quiz_entry.quiz.title # Per logging
            pathway_quiz_entry.delete()

            # Opzionale ma consigliato: Riordina i quiz successivi nel percorso
            # Simile a QuestionViewSet.perform_destroy
            quizzes_to_reorder = PathwayQuiz.objects.filter(
                pathway=pathway,
                order__gt=deleted_order
            ).order_by('order')
            updated_count = quizzes_to_reorder.update(order=F('order') - 1)
            logger.info(f"Rimosso quiz '{quiz_title}' (relazione {pathway_quiz_pk}) e riordinate {updated_count} voci nel percorso {pathway.id}.")

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404: # Importa Http404 da django.http se non già fatto
             return Response({'detail': 'Relazione Quiz-Percorso non trovata.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Errore durante la rimozione del quiz (relazione {pathway_quiz_pk}) dal percorso {pk}: {e}", exc_info=True)
            return Response({'detail': 'Errore interno durante la rimozione del quiz dal percorso.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- ViewSets per Studenti (Svolgimento) ---

class StudentDashboardViewSet(viewsets.ViewSet):
     """ Endpoint per lo studente per vedere cosa gli è stato assegnato. """
     permission_classes = [IsStudentAuthenticated] # Solo Studenti autenticati

     def list(self, request):
         student = request.user # Ora request.user è lo studente
         # Rimosso controllo 'if not student:' perché IsStudentAuthenticated garantisce che ci sia

         assigned_quiz_ids = QuizAssignment.objects.filter(student=student).values_list('quiz_id', flat=True)
         assigned_pathway_ids = PathwayAssignment.objects.filter(student=student).values_list('pathway_id', flat=True)

         assigned_quizzes = Quiz.objects.filter(id__in=assigned_quiz_ids)
         assigned_pathways = Pathway.objects.filter(id__in=assigned_pathway_ids)

         quiz_serializer = QuizSerializer(assigned_quizzes, many=True, context={'request': request})
         pathway_serializer = PathwaySerializer(assigned_pathways, many=True, context={'request': request})

         return Response({
             "assigned_quizzes": quiz_serializer.data,
             "assigned_pathways": pathway_serializer.data
         })


class StudentQuizAttemptViewSet(viewsets.GenericViewSet):
    """ Gestisce l'inizio di un Quiz da parte dello Studente (spostato da QuizViewSet). """
    permission_classes = [IsStudentAuthenticated] # Solo Studenti autenticati
    serializer_class = QuizAttemptSerializer # Per output base

    # POST /api/education/quizzes/{quiz_pk}/start-attempt/
    @action(detail=False, methods=['post'], url_path='start-attempt')
    def start_attempt(self, request, quiz_pk=None):
         quiz = get_object_or_404(Quiz, pk=quiz_pk)
         student = request.user # Ora request.user è lo studente
         # Rimosso controllo 'if not student:'

         # Verifica se il quiz è assegnato direttamente
         is_directly_assigned = QuizAssignment.objects.filter(student=student, quiz=quiz).exists()

         # Verifica se il quiz fa parte di un percorso assegnato
         is_in_assigned_pathway = Pathway.objects.filter(
             assignments__student=student,
             pathwayquiz__quiz=quiz
         ).exists()

         # Verifica se il quiz è assegnato a un gruppo a cui lo studente appartiene
         student_group_ids = StudentGroupMembership.objects.filter(student=student).values_list('group_id', flat=True)
         is_assigned_via_group = QuizAssignment.objects.filter(
             quiz=quiz,
             group_id__in=student_group_ids
         ).exists()

         # Se non è assegnato in nessuno dei modi consentiti, nega l'accesso
         if not is_directly_assigned and not is_in_assigned_pathway and not is_assigned_via_group:
             logger.warning(f"Tentativo accesso non autorizzato a quiz {quiz.id} da studente {student.id}. Assegnato direttamente: {is_directly_assigned}, In percorso assegnato: {is_in_assigned_pathway}, Via gruppo: {is_assigned_via_group}")
             return Response({'detail': 'Questo quiz non ti è stato assegnato direttamente, tramite un percorso o tramite un gruppo.'}, status=status.HTTP_403_FORBIDDEN)

         # Seleziona solo i campi necessari per QuizAttemptDetailSerializer se l'attempt esiste
         existing_attempt = QuizAttempt.objects.filter(
             student=student,
             quiz=quiz,
             status=QuizAttempt.AttemptStatus.IN_PROGRESS
         ).only(
             'id', 'student_id', 'quiz_id', 'started_at', 'completed_at', 'score', 'status'
             # Non includere 'first_correct_completion' qui
         ).first()
         if existing_attempt:
             serializer = QuizAttemptDetailSerializer(existing_attempt, context={'request': request})
             return Response(serializer.data, status=status.HTTP_200_OK)

         attempt = QuizAttempt.objects.create(student=student, quiz=quiz)
         serializer = QuizAttemptDetailSerializer(attempt, context={'request': request})
         return Response(serializer.data, status=status.HTTP_201_CREATED)


# NUOVO ViewSet per gestire un tentativo specifico
class AttemptViewSet(viewsets.GenericViewSet):
    """ Gestisce le azioni su un tentativo di quiz specifico (submit, complete). """
    queryset = QuizAttempt.objects.all()
    # Usa IsStudentAuthenticated
    # permission_classes = [IsStudentAuthenticated, IsStudentOwnerForAttempt] # TEMPORANEAMENTE COMMENTATO per debug
    permission_classes = [IsStudentAuthenticated] # Usiamo solo IsStudentAuthenticated per ora

    # GET /api/education/attempts/{pk}/details/
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        attempt = self.get_object() # get_object usa queryset e pk dall'URL
        serializer = QuizAttemptDetailSerializer(attempt, context={'request': request})
        return Response(serializer.data)

    # GET /api/education/attempts/{pk}/current-question/
    @action(detail=True, methods=['get'], url_path='current-question')
    def current_question(self, request, pk=None):
        """ Restituisce la prossima domanda non risposta nel tentativo. """
        attempt = self.get_object()
        if attempt.status != QuizAttempt.AttemptStatus.IN_PROGRESS:
            return Response({'detail': 'Questo tentativo non è più in corso.'}, status=status.HTTP_400_BAD_REQUEST)

        # Ottieni tutte le domande del quiz ordinate
        all_questions = attempt.quiz.questions.prefetch_related('answer_options').order_by('order') # Aggiunto prefetch_related
        # Ottieni gli ID delle domande già risposte in questo tentativo
        answered_question_ids = set(attempt.student_answers.values_list('question_id', flat=True))

        next_question = None
        for question in all_questions:
            if question.id not in answered_question_ids:
                next_question = question
                break # Trovata la prima domanda non risposta

        if next_question:
            # Serializza e restituisci la domanda corrente
            serializer = QuestionSerializer(next_question, context={'request': request})
            return Response(serializer.data)
        else:
            # Se non ci sono più domande non risposte, ma il tentativo è ancora in corso
            # (l'utente potrebbe non aver ancora chiamato 'complete'),
            # restituisci 204 No Content per indicare che non c'è una *prossima* domanda.
            return Response(status=status.HTTP_204_NO_CONTENT)

    # POST /api/education/attempts/{pk}/submit-answer/
    @action(detail=True, methods=['post'], url_path='submit-answer')
    def submit_answer(self, request, pk=None):
        attempt = self.get_object()
        if attempt.status != QuizAttempt.AttemptStatus.IN_PROGRESS:
            return Response({'detail': 'Questo tentativo non è più in corso.'}, status=status.HTTP_400_BAD_REQUEST)

        question_id = request.data.get('question_id')
        selected_answers_data = request.data.get('selected_answers') # Formato dipende dal tipo di domanda

        if question_id is None or selected_answers_data is None:
             return Response({'detail': 'question_id e selected_answers sono richiesti.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            question = Question.objects.get(pk=question_id, quiz=attempt.quiz)
        except Question.DoesNotExist:
             return Response({'detail': 'Domanda non trovata in questo quiz.'}, status=status.HTTP_404_NOT_FOUND)

        # Validazione di selected_answers_data in base a question.question_type
        logger.info(f"Attempt {pk} - Submit Answer - Raw request.data: {request.data}") # LOGGING
        logger.info(f"Attempt {pk} - Submit Answer - Extracted selected_answers_data: {selected_answers_data}") # LOGGING
        logger.info(f"Attempt {pk} - Submit Answer - Type of selected_answers_data: {type(selected_answers_data)}") # LOGGING
        validation_error = None
        valid_data_for_storage = {} # Dati validati da salvare

        q_type = question.question_type
        if q_type in [QuestionType.MULTIPLE_CHOICE_SINGLE, QuestionType.TRUE_FALSE]:
            # Modificato per aspettarsi 'answer_option_id'
            if not isinstance(selected_answers_data, dict) or 'answer_option_id' not in selected_answers_data:
                validation_error = "Per questo tipo di domanda, 'selected_answers' deve essere un dizionario con chiave 'answer_option_id'."
            else:
                selected_id = selected_answers_data['answer_option_id'] # Modificato per usare la chiave corretta
                # Permetti None per deselezionare? Se sì, aggiungere 'or selected_id is None'
                # Modificato messaggio di errore
                if not isinstance(selected_id, int):
                    validation_error = "'answer_option_id' deve essere un intero."
                else:
                    # Verifica che l'opzione esista per questa domanda
                    # Modificato messaggio di errore
                    if not question.answer_options.filter(pk=selected_id).exists():
                        validation_error = f"L'opzione con ID {selected_id} ('answer_option_id') non è valida per questa domanda."
                    else:
                        # Dati validi per il salvataggio
                        valid_data_for_storage = {'answer_option_id': selected_id} # Modificato per salvare la chiave corretta

        elif q_type == QuestionType.MULTIPLE_CHOICE_MULTIPLE:
            # Modificato per aspettarsi 'answer_option_ids'
            if not isinstance(selected_answers_data, dict) or 'answer_option_ids' not in selected_answers_data:
                validation_error = "Per questo tipo di domanda, 'selected_answers' deve essere un dizionario con chiave 'answer_option_ids'."
            else:
                selected_ids = selected_answers_data['answer_option_ids'] # Modificato per usare la chiave corretta
                # Modificato messaggio di errore
                if not isinstance(selected_ids, list) or not all(isinstance(i, int) for i in selected_ids):
                    validation_error = "'answer_option_ids' deve essere una lista di interi."
                else:
                    # Verifica che tutte le opzioni esistano per questa domanda
                    valid_option_ids = set(question.answer_options.values_list('id', flat=True))
                    submitted_ids_set = set(selected_ids)
                    if not submitted_ids_set.issubset(valid_option_ids):
                        invalid_ids = submitted_ids_set - valid_option_ids
                        # Modificato messaggio di errore
                        validation_error = f"Le seguenti opzioni ('answer_option_ids') non sono valide per questa domanda: {list(invalid_ids)}."
                    else:
                        # Dati validi per il salvataggio
                        valid_data_for_storage = {'answer_option_ids': sorted(list(submitted_ids_set))} # Salva come lista ordinata

        elif q_type == QuestionType.FILL_BLANK:
            # Modificato per aspettarsi 'answers' come lista di stringhe
            if not isinstance(selected_answers_data, dict) or 'answers' not in selected_answers_data:
                 validation_error = "Per questo tipo di domanda, 'selected_answers' deve essere un dizionario con chiave 'answers'."
            else:
                answers = selected_answers_data['answers']
                # Modificato messaggio di errore
                if not isinstance(answers, list) or not all(isinstance(a, str) for a in answers):
                    validation_error = "'answers' deve essere una lista di stringhe."
                else:
                    # Verifica che il numero di risposte corrisponda agli spazi vuoti attesi (se definito in metadata)
                    expected_blanks = question.metadata.get('blanks_count')
                    if expected_blanks is not None and len(answers) != expected_blanks:
                        validation_error = f"Numero di risposte ('answers') non corretto. Attesi {expected_blanks}, ricevuti {len(answers)}."
                    else:
                        # Dati validi per il salvataggio
                        valid_data_for_storage = {'answers': answers} # Modificato per salvare la chiave corretta

        elif q_type == QuestionType.OPEN_ANSWER_MANUAL:
            # Modificato per aspettarsi 'text'
            if not isinstance(selected_answers_data, dict) or 'text' not in selected_answers_data:
                 validation_error = "Per questo tipo di domanda, 'selected_answers' deve essere un dizionario con chiave 'text'."
            else:
                answer_text = selected_answers_data['text'] # Modificato per usare la chiave corretta
                # Modificato messaggio di errore
                if not isinstance(answer_text, str):
                    validation_error = "'text' deve essere una stringa."
                else:
                    # Dati validi per il salvataggio
                    valid_data_for_storage = {'text': answer_text} # Modificato per salvare la chiave corretta

        else:
            validation_error = f"Tipo di domanda non supportato: {q_type}"

        if validation_error:
            logger.warning(f"Attempt {pk} - Submit Answer - Validation Error: {validation_error}") # LOGGING
            return Response({'selected_answers': validation_error}, status=status.HTTP_400_BAD_REQUEST)

        # Crea o aggiorna la risposta dello studente
        student_answer, created = StudentAnswer.objects.update_or_create(
            quiz_attempt=attempt,
            question=question,
            defaults={
                'selected_answers': valid_data_for_storage, # Salva i dati validati
                'answered_at': timezone.now()
                # Rimosso 'is_correct' e 'score' da qui, verranno calcolati/impostati dopo
            }
        )

        # Rimosso: La valutazione avviene in calculate_final_score o manualmente
        # if question.question_type != QuestionType.OPEN_ANSWER_MANUAL:
        #     student_answer.evaluate() # Il metodo evaluate() salva la risposta
        serializer = StudentAnswerSerializer(student_answer)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


    # POST /api/education/attempts/{pk}/complete/
    @action(detail=True, methods=['post'], url_path='complete')
    def complete_attempt(self, request, pk=None):
        """ Completa un tentativo di quiz. """
        attempt = self.get_object()
        if attempt.status != QuizAttempt.AttemptStatus.IN_PROGRESS:
            return Response({'detail': 'Questo tentativo non è più in corso.'}, status=status.HTTP_400_BAD_REQUEST)

        newly_earned_badges = [] # Inizializza a lista vuota

        # --- Inizio Valutazione IMMEDIATA Risposte Automatiche ---
        # Itera su tutte le risposte date per questo tentativo e valuta quelle automatiche
        logger.debug(f"Inizio valutazione immediata risposte per tentativo {attempt.id}")
        for student_answer in attempt.student_answers.prefetch_related('question', 'question__answer_options').all():
            question = student_answer.question
            valid_data_for_storage = student_answer.selected_answers # Recupera i dati salvati
            
            # Usa nomi di variabili locali diversi per evitare confusione con i campi del modello
            is_correct_val = None
            score_val = None
            
            # Esegui la logica di valutazione solo per domande a correzione automatica
            if question.question_type != QuestionType.OPEN_ANSWER_MANUAL:
                logger.debug(f"Valutazione Q{question.order} (Tipo: {question.question_type})")
                try:
                    if question.question_type == QuestionType.MULTIPLE_CHOICE_SINGLE:
                        correct_option = question.answer_options.filter(is_correct=True).first()
                        selected_option_id = valid_data_for_storage.get('answer_option_id')
                        is_correct_val = bool(correct_option and selected_option_id == correct_option.id)
                        score_val = float(question.metadata.get('points_per_correct_answer', 1.0)) if is_correct_val else 0.0
                        logger.debug(f"  MC_SINGLE: Sel={selected_option_id}, Corr={correct_option.id if correct_option else None}, Result={is_correct_val}, Score={score_val}")

                    elif question.question_type == QuestionType.TRUE_FALSE:
                        correct_option = question.answer_options.filter(is_correct=True).first()
                        selected_option_id = valid_data_for_storage.get('answer_option_id')
                        if correct_option:
                            is_correct_val = bool(selected_option_id == correct_option.id)
                            score_val = float(question.metadata.get('points_per_correct_answer', 1.0)) if is_correct_val else 0.0
                            logger.debug(f"  TF: SelOptID={selected_option_id}, CorrOptID={correct_option.id}, Result={is_correct_val}, Score={score_val}")
                        else:
                            is_correct_val = False; score_val = 0.0
                            logger.warning(f"  TF: Nessuna opzione corretta definita per Q ID {question.id}")

                    elif question.question_type == QuestionType.MULTIPLE_CHOICE_MULTIPLE:
                        correct_option_ids = set(question.answer_options.filter(is_correct=True).values_list('id', flat=True))
                        selected_option_ids = set(valid_data_for_storage.get('answer_option_ids', []))
                        is_correct_val = (correct_option_ids == selected_option_ids)
                        score_val = float(question.metadata.get('points_per_correct_answer', 1.0)) if is_correct_val else 0.0
                        logger.debug(f"  MC_MULTI: Sel={selected_option_ids}, Corr={correct_option_ids}, Result={is_correct_val}, Score={score_val}")

                    elif question.question_type == QuestionType.FILL_BLANK:
                        # Nuova logica di valutazione per FILL_BLANK come da FILL_BLANK_PLAN.md
                        question_metadata = question.metadata
                        blanks_config = question_metadata.get('blanks', []) # Lista di oggetti blank
                        case_sensitive = question_metadata.get('case_sensitive', False)
                        student_selected_answers = valid_data_for_storage.get('answers', []) # Lista di oggetti {blank_id, student_response}

                        if not blanks_config: # Se non ci sono blank configurati, la domanda non può essere corretta
                            is_correct_val = False
                            logger.warning(f"  FILL_BLANK: Nessuna configurazione 'blanks' trovata nei metadati per Q ID {question.id}")
                        else:
                            # Trasforma le risposte dello studente in un dizionario per un facile accesso by blank_id
                            student_responses_map = {}
                            # student_selected_answers è valid_data_for_storage.get('answers', [])
                            # blanks_config è question_metadata.get('blanks', [])

                            if student_selected_answers and isinstance(student_selected_answers[0], str):
                                # Caso: student_selected_answers è una lista di stringhe (es. ["risposta1", "risposta2"])
                                # Assumiamo che l'ordine delle risposte corrisponda all'ordine dei blank in blanks_config.
                                # Questo è coerente con il commento in riga 1443 e il formato del bug report.
                                if len(student_selected_answers) == len(blanks_config):
                                    for i, blank_conf in enumerate(blanks_config):
                                        blank_id = blank_conf.get('id')
                                        if blank_id: # Assicura che blank_id esista
                                            student_responses_map[blank_id] = student_selected_answers[i].strip()
                                else:
                                    # Numero di risposte stringa non corrisponde al numero di blanks.
                                    # La logica successiva (controllo len(student_responses_map) != len(blanks_config))
                                    # dovrebbe gestire questa discrepanza se la mappa risulta incompleta o di lunghezza errata.
                                    logger.debug(
                                        f"  FILL_BLANK: Numero di risposte stringa ({len(student_selected_answers)}) "
                                        f"non corrisponde al numero di blanks ({len(blanks_config)}) per Q ID {question.id}. "
                                        f"La mappa potrebbe essere popolata in modo incompleto o la validazione successiva fallirà."
                                    )
                            
                            elif student_selected_answers and isinstance(student_selected_answers[0], dict):
                                # Caso: student_selected_answers è una lista di dizionari (formato del piano originale)
                                # Esempio: [{"blank_id": "b0", "student_response": "r0"}, ...]
                                for ans_obj in student_selected_answers:
                                    blank_id = ans_obj.get('blank_id')
                                    student_response = ans_obj.get('student_response', '')
                                    if blank_id:
                                        student_responses_map[blank_id] = str(student_response).strip()
                            else:
                                # Formato inatteso o lista vuota di risposte.
                                # student_responses_map rimane vuota.
                                if student_selected_answers: # Solo se non è vuota ma ha un formato strano
                                    logger.warning(
                                        f"  FILL_BLANK: Formato inatteso o vuoto per student_selected_answers: "
                                        f"{student_selected_answers} per Q ID {question.id}"
                                    )
                            
                            all_blanks_match = True
                            if len(student_responses_map) != len(blanks_config):
                                # Se il numero di risposte fornite non corrisponde al numero di blank attesi
                                all_blanks_match = False
                                logger.debug(f"  FILL_BLANK: Numero di risposte fornite ({len(student_responses_map)}) non corrisponde al numero di blanks attesi ({len(blanks_config)}) per Q ID {question.id}")

                            if all_blanks_match: # Prosegui solo se il numero di risposte corrisponde
                                for blank_conf in blanks_config:
                                    blank_id = blank_conf.get('id')
                                    correct_variants_for_blank = blank_conf.get('correct_answers', [])
                                    student_response_for_blank = student_responses_map.get(blank_id)

                                    if student_response_for_blank is None: # Risposta mancante per questo blank_id
                                        all_blanks_match = False
                                        logger.debug(f"  FILL_BLANK: Risposta mancante per blank_id '{blank_id}' in Q ID {question.id}")
                                        break

                                    match_found_for_this_blank = False
                                    for correct_variant in correct_variants_for_blank:
                                        # Assicura che entrambe le stringhe siano effettivamente stringhe prima del confronto
                                        correct_variant_str = str(correct_variant).strip()
                                        # student_response_for_blank è già strippata quando inserita nella mappa
                                        student_response_str = str(student_response_for_blank)

                                        if not case_sensitive:
                                            if correct_variant_str.lower() == student_response_str.lower():
                                                match_found_for_this_blank = True
                                                break
                                        else:
                                            if correct_variant_str == student_response_str:
                                                match_found_for_this_blank = True
                                                break
                                    
                                    if not match_found_for_this_blank:
                                        all_blanks_match = False
                                        logger.debug(f"  FILL_BLANK: Nessun match per blank_id '{blank_id}' (risposta: '{student_response_for_blank}') in Q ID {question.id}")
                                        break # Esci dal ciclo dei blank, la domanda è sbagliata
                            
                            is_correct_val = all_blanks_match
                        
                        # Il punteggio è per l'intera domanda, non per singolo blank
                        score_val = float(question_metadata.get('points', 1.0)) if is_correct_val else 0.0
                        logger.debug(f"  FILL_BLANK (Nuova Logica): Result={is_correct_val}, Score={score_val} per Q ID {question.id}")

                    # Salva i risultati della valutazione sulla singola risposta
                    if is_correct_val is not None: # Salva solo se è stata valutata
                        student_answer.is_correct = is_correct_val
                        student_answer.score = score_val
                        student_answer.save(update_fields=['is_correct', 'score'])
                        logger.debug(f"  Risposta salvata: is_correct={student_answer.is_correct}, score={student_answer.score}")
                    else:
                         logger.debug(f"  Nessuna valutazione automatica applicabile (is_correct_val is None).")

                except Exception as eval_error:
                     logger.error(f"Errore durante valutazione automatica immediata per Q ID {question.id} in tentativo {attempt.id}: {eval_error}", exc_info=True)
                     student_answer.is_correct = None # Assicura che rimanga non valutato in caso di errore
                     student_answer.score = None
                     student_answer.save(update_fields=['is_correct', 'score'])
        logger.debug(f"Fine valutazione immediata risposte per tentativo {attempt.id}")
        # --- Fine Valutazione IMMEDIATA Risposte Automatiche ---

        # Ora determina se è necessaria la correzione manuale
        has_manual_questions = attempt.quiz.questions.filter(question_type=QuestionType.OPEN_ANSWER_MANUAL).exists()
        needs_manual_grading = False
        if has_manual_questions:
            manual_question_ids = attempt.quiz.questions.filter(question_type=QuestionType.OPEN_ANSWER_MANUAL).values_list('id', flat=True)
            answered_manual_ids = attempt.student_answers.filter(question_id__in=manual_question_ids).values_list('question_id', flat=True)
            if set(manual_question_ids) == set(answered_manual_ids):
                 needs_manual_grading = True
            else:
                 return Response({'detail': 'Devi rispondere a tutte le domande prima di completare il tentativo.'}, status=status.HTTP_400_BAD_REQUEST)

        attempt.completed_at = timezone.now() # Imposta il tempo di completamento per tutti i casi

        if needs_manual_grading:
            attempt.status = QuizAttempt.AttemptStatus.PENDING_GRADING
            logger.info(f"Tentativo Quiz {attempt.id} completato, ora PENDING_GRADING.")
        else:
            # Quiz completamente automatico o uno le cui domande manuali sono già state valutate
            # (questo secondo caso di solito seguirebbe un flusso di 'finalize_grading' separato,
            # ma qui gestiamo il caso in cui non ci sono domande manuali o sono state tutte risposte
            # e per qualche motivo non è PENDING_GRADING - anche se la logica sopra lo imposterebbe).
            # La logica principale qui è per quiz interamente automatici.
            final_score = attempt.calculate_final_score() # Calcola e salva lo score sull'attempt
            newly_earned_badges = attempt.assign_completion_points() # Assegna punti/badge e aggiorna lo stato dell'attempt
            logger.info(f"Tentativo Quiz {attempt.id} completato e valutato automaticamente. Score: {final_score}, Status: {attempt.status}")
        
        attempt.save() # Salva lo stato finale (PENDING_GRADING o COMPLETED/FAILED) e completed_at

        # Passa i nuovi badge al contesto del serializer
        context = {'request': request, 'newly_earned_badges': newly_earned_badges}
        # Usiamo QuizAttemptSerializer per coerenza, ma potrebbe essere utile QuizAttemptDetailSerializer se il FE lo aspetta
        serializer = QuizAttemptSerializer(attempt, context=context)
        return Response(serializer.data)


# --- ViewSet per Docenti (Correzione Manuale) ---



# --- Viste Generiche per Dashboard Studente (usano generics.ListAPIView) ---

class StudentAssignedQuizzesView(generics.ListAPIView):
    """
    Restituisce l'elenco dei TENTATIVI di quiz assegnati allo studente loggato per la dashboard.
    Restituisce un elenco di QuizAttempt con dettagli del Quiz associato.
    """
    # Importa il nuovo serializer all'inizio del file se non già fatto
    from .serializers import StudentQuizAttemptDashboardSerializer
    serializer_class = StudentQuizAttemptDashboardSerializer # Usa il NUOVO serializer basato su QuizAttempt
    permission_classes = [IsStudentAuthenticated] # Solo studenti autenticati

    def get_queryset(self):
        """
        Restituisce un elenco dei TENTATIVI più recenti per ogni quiz assegnato allo studente.
        """
        student = self.request.user # Assicurato da IsStudentAuthenticated

        # 1. Trova tutti i Quiz ID assegnati allo studente (direttamente o via gruppo)
        assigned_quiz_ids_direct = QuizAssignment.objects.filter(
            student=student
        ).values_list('quiz_id', flat=True)

        # Recupera gli ID dei gruppi a cui appartiene lo studente
        student_group_ids = list(StudentGroupMembership.objects.filter(
            student=student
        ).values_list('group_id', flat=True))
        
        # Recupera gli ID dei quiz dalle assegnazioni a quei gruppi
        if student_group_ids:
            assigned_quiz_ids_group = QuizAssignment.objects.filter(
                group_id__in=student_group_ids # Usa group_id__in
            ).values_list('quiz_id', flat=True)
        else:
            assigned_quiz_ids_group = QuizAssignment.objects.none()

        all_assigned_quiz_ids = set(assigned_quiz_ids_direct) | set(assigned_quiz_ids_group)

        if not all_assigned_quiz_ids:
            return QuizAttempt.objects.none() # Nessun quiz assegnato

        # 2. Trova l'ID del tentativo più recente per ogni quiz assegnato a questo studente
        latest_attempt_subquery = QuizAttempt.objects.filter(
            quiz_id=OuterRef('quiz_id'), # Filtra per quiz_id (corretto)
            student=student
        ).order_by('-started_at').values('id')[:1]

        # 3. Recupera i tentativi più recenti (se esistono) usando la subquery
        # Filtra solo per i quiz che sono effettivamente assegnati
        latest_attempts = QuizAttempt.objects.filter(
            quiz_id__in=all_assigned_quiz_ids, # Assicura che il tentativo sia per un quiz assegnato
            student=student, # Assicura che il tentativo sia dello studente corrente
            id__in=Subquery(latest_attempt_subquery) # Seleziona solo l'ID più recente per ogni quiz
        ).select_related('quiz', 'quiz__teacher', 'quiz__source_template') # Aggiunto quiz__source_template

        return latest_attempts.order_by('-started_at') # Ordina i tentativi più recenti

    def get_serializer_context(self):
        """
        Aggiunge al contesto la lista di tutti i Quiz assegnati e lo studente.
        Il serializer userà queste informazioni per costruire la risposta completa.
        """
        context = super().get_serializer_context()
        student = self.request.user

        # Recupera nuovamente tutti gli ID dei quiz assegnati (come in get_queryset)
        assigned_quiz_ids_direct = QuizAssignment.objects.filter(
            student=student
        ).values_list('quiz_id', flat=True)
        # Recupera gli ID dei gruppi a cui appartiene lo studente
        student_group_ids = StudentGroupMembership.objects.filter(
            student=student
        ).values_list('group_id', flat=True)
        # Filtra le assegnazioni per quegli ID di gruppo
        # Recupera gli oggetti StudentGroup a cui appartiene lo studente
        student_groups = StudentGroup.objects.filter(
            id__in=student_group_ids
        )
        # Recupera gli ID dei quiz dalle assegnazioni a quei gruppi
        assigned_quiz_ids_group = QuizAssignment.objects.filter(
            group__in=student_groups
        ).values_list('quiz_id', flat=True)
        all_assigned_quiz_ids = set(assigned_quiz_ids_direct) | set(assigned_quiz_ids_group)

        # Recupera gli oggetti Quiz assegnati
        assigned_quizzes = Quiz.objects.filter(
            id__in=all_assigned_quiz_ids
        ).select_related('teacher')

        context['student'] = student
        context['assigned_quizzes'] = assigned_quizzes # Passa i quiz assegnati al serializer
        return context

    def list(self, request, *args, **kwargs):
        """
        Costruisce l'elenco dei quiz per la dashboard basandosi sulle assegnazioni attive.
        Mostra lo stato del tentativo più recente per ogni istanza quiz assegnata,
        o "PENDING" se quell'istanza non è mai stata tentata.
        """
        student = request.user
        now = timezone.now()
        logger.debug(f"Inizio recupero dashboard quiz per studente: {student.id}")

        # 1. Ottieni ID dei gruppi dello studente
        try:
            student_group_ids = list(StudentGroupMembership.objects.filter(
                student=student
            ).values_list('group_id', flat=True))
            logger.debug(f"ID Gruppi studente {student.id}: {student_group_ids}")
        except Exception as e:
            logger.error(f"Errore nel recuperare i gruppi per studente {student.id}: {e}", exc_info=True)
            student_group_ids = []

        # 2. Ottieni tutte le QuizAssignment attive (dirette e di gruppo)
        try:
            assignments_queryset = QuizAssignment.objects.filter(
                Q(student=student) | Q(group_id__in=student_group_ids)
            ).filter(
                # Opzionale: Filtro per non mostrare assegnazioni scadute?
                # Q(due_date__isnull=True) | Q(due_date__gte=now)
                # Opzionale: Filtro per non mostrare assegnazioni future?
                # Q(assigned_at__lte=now) # O basarsi su quiz.available_from?
            ).select_related(
                'quiz', 'quiz__teacher', 'quiz__source_template' # Precarica dati correlati per efficienza
            ).order_by('-assigned_at') # Ordina per le più recenti prima (o altro criterio?)

            # Estrai gli ID delle istanze Quiz da tutte le assegnazioni attive
            # Usiamo un set per evitare duplicati se un quiz è in più gruppi
            assigned_quiz_ids = set(assignments_queryset.values_list('quiz_id', flat=True))
            logger.debug(f"ID Quiz assegnati (istanze) per studente {student.id}: {assigned_quiz_ids}")

        except Exception as e:
            logger.error(f"Errore nel recuperare le assegnazioni quiz per studente {student.id}: {e}", exc_info=True)
            return Response({"detail": "Errore nel recupero delle assegnazioni."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 3. Ottieni i QuizAttempt più recenti per ciascuno di questi quiz_id specifici
        latest_attempts_map = {}
        if assigned_quiz_ids: # Procedi solo se ci sono quiz assegnati
            try:
                # Subquery per trovare l'ID del tentativo più recente per ogni (quiz_id, student)
                latest_attempts_subquery = QuizAttempt.objects.filter(
                    quiz_id=OuterRef('quiz_id'),
                    student=student
                ).order_by('-started_at') # Il più recente per data di inizio

                # Annotiamo ogni (quiz_id, student) con l'ID del suo tentativo più recente
                latest_attempt_ids_qs = QuizAttempt.objects.filter(
                    quiz_id__in=assigned_quiz_ids,
                    student=student
                ).values(
                    'quiz_id' # Raggruppa per quiz
                ).annotate(
                    latest_attempt_id=Subquery(latest_attempts_subquery.values('id')[:1]) # Ottieni l'ID del più recente
                ).values('quiz_id', 'latest_attempt_id') # Estrai coppie quiz_id -> latest_attempt_id

                # Estrai solo gli ID dei tentativi più recenti validi
                valid_latest_attempt_ids = [item['latest_attempt_id'] for item in latest_attempt_ids_qs if item['latest_attempt_id'] is not None]

                # Recupera gli oggetti QuizAttempt completi per questi ID
                latest_attempts_queryset = QuizAttempt.objects.filter(
                    id__in=valid_latest_attempt_ids
                ).select_related('quiz', 'quiz__teacher', 'quiz__source_template') # Prendi i dati necessari

                # Crea la mappa quiz_id -> ultimo tentativo per un accesso rapido
                latest_attempts_map = {attempt.quiz_id: attempt for attempt in latest_attempts_queryset}
                logger.debug(f"Mappa ultimi tentativi per studente {student.id}: {latest_attempts_map.keys()}")

            except Exception as e:
                logger.error(f"Errore nel recuperare gli ultimi tentativi per studente {student.id}: {e}", exc_info=True)
                # Continua senza tentativi, verranno mostrati come PENDING

        # 4. Costruisci l'elenco finale basato sulle assegnazioni
        final_data_list = []
        # Usiamo un set per tenere traccia degli ID delle *istanze quiz* già processate
        # se vogliamo mostrare solo l'assegnazione più recente per ogni istanza quiz.
        # Se invece vogliamo mostrare *ogni* assegnazione, rimuoviamo questo set.
        # Assumiamo di voler mostrare ogni assegnazione attiva.
        # processed_quiz_instance_ids = set()

        for assignment in assignments_queryset:
            quiz = assignment.quiz
            # if quiz.id in processed_quiz_instance_ids: # Salta se già processato (se mostriamo solo l'ultima assegnazione)
            #     continue
            # processed_quiz_instance_ids.add(quiz.id)

            attempt = latest_attempts_map.get(quiz.id) # Trova l'ultimo tentativo per questa istanza quiz

            # Determina il tipo di assegnazione
            assignment_type = 'unknown'
            if assignment.student_id == student.id:
                assignment_type = 'student'
            elif assignment.group_id is not None and assignment.group_id in student_group_ids:
                assignment_type = 'group'

            # Determina le date di disponibilità (dal Quiz)
            available_from = quiz.available_from
            available_until = quiz.available_until

            # Costruisci l'oggetto dati per questa assegnazione
            item_data = {}
            if attempt:
                # Se esiste un tentativo per questa istanza quiz, usa i suoi dati
                item_data = {
                    "attempt_id": attempt.id,
                    "quiz_id": quiz.id,
                    "title": quiz.title, # Potremmo voler aggiungere info sull'assegnazione? Es. f"{quiz.title} (Assegnato il {assignment.assigned_at})"
                    "description": quiz.description,
                    "status": attempt.status,
                    "score": attempt.score,
                    "available_from": available_from,
                    "available_until": available_until,
                    "metadata": quiz.metadata,
                    "teacher_username": quiz.teacher.username if quiz.teacher else None, # CORRETTO: Username
                    "teacher_first_name": quiz.teacher.first_name if quiz.teacher else None, # NUOVO/CORRETTO
                    "teacher_last_name": quiz.teacher.last_name if quiz.teacher else None,   # NUOVO/CORRETTO
                    "started_at": attempt.started_at,
                    "completed_at": attempt.completed_at,
                    "assignment_type": assignment_type,
                    # Campi aggiuntivi richiesti dal serializer
                    "status_display": attempt.get_status_display(), # Usa il metodo del modello
                    "quiz_title": quiz.title,
                    "quiz_description": quiz.description,
"subject_name": quiz.source_template.subject if quiz.source_template else quiz.subject,
                    "topic_name": quiz.source_template.topic if quiz.source_template else quiz.topic,
                    # "subject_color_placeholder": quiz.source_template.subject_color_placeholder if quiz.source_template else (getattr(quiz, 'subject_color_placeholder', None)),
                    "card_background_color": quiz.source_template.card_background_color if quiz.source_template else None,
                }
            else:
                # Se non esiste NESSUN tentativo per questa istanza quiz, è "PENDING"
                item_data = {
                    "attempt_id": None,
                    "quiz_id": quiz.id,
                    "title": quiz.title,
                    "description": quiz.description,
                    "status": "PENDING", # Stato implicito se non tentato
                    "score": None,
                    "available_from": available_from,
                    "available_until": available_until,
                    "metadata": quiz.metadata,
                    "teacher_username": quiz.teacher.username if quiz.teacher else None, # CORRETTO: Username
                    "teacher_first_name": quiz.teacher.first_name if quiz.teacher else None, # NUOVO/CORRETTO
                    "teacher_last_name": quiz.teacher.last_name if quiz.teacher else None,   # NUOVO/CORRETTO
                    "started_at": None,
                    "completed_at": None,
                    "assignment_type": assignment_type,
                    # Campi aggiuntivi richiesti dal serializer
                    "status_display": "Da Iniziare",
                    "quiz_title": quiz.title,
                    "quiz_description": quiz.description,
"subject_name": quiz.source_template.subject if quiz.source_template else quiz.subject,
"topic_name": quiz.source_template.topic if quiz.source_template else quiz.topic,
                    # "subject_color_placeholder": quiz.source_template.subject_color_placeholder if quiz.source_template else (getattr(quiz, 'subject_color_placeholder', None)),
                    "card_background_color": quiz.source_template.card_background_color if quiz.source_template else None,
                }
            final_data_list.append(item_data)

        # 5. Serializza l'elenco costruito
        try:
            # Passiamo la lista di dizionari direttamente al serializer
            serializer = self.get_serializer(final_data_list, many=True)
            logger.debug(f"Dati finali serializzati per studente {student.id}: {len(serializer.data)} elementi.")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Errore durante la serializzazione della dashboard quiz per studente {student.id}: {e}", exc_info=True)
            return Response({"detail": "Errore durante la preparazione dei dati della dashboard."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StudentAssignedPathwaysView(generics.ListAPIView):
    """
    Restituisce l'elenco dei percorsi assegnati allo studente loggato,
    arricchiti con informazioni sull'ultimo progresso.
    """
    serializer_class = StudentPathwayDashboardSerializer
    permission_classes = [IsStudentAuthenticated]

    def get_queryset(self):
        """
        Restituisce i Percorsi assegnati allo studente autenticato (direttamente o tramite gruppo).
        """
        student = self.request.user

        # Trova ID percorsi assegnati direttamente
        direct_pathway_ids = PathwayAssignment.objects.filter(student=student).values_list('pathway_id', flat=True)

        # Trova ID gruppi dello studente
        # Usa il related_name corretto definito nel modello StudentGroupMembership
        group_ids = student.group_memberships.values_list('group_id', flat=True)

        # Trova ID percorsi assegnati ai gruppi dello studente
        group_pathway_ids = PathwayAssignment.objects.filter(group_id__in=group_ids).values_list('pathway_id', flat=True)

        # Unisci gli ID e filtra i Percorsi
        all_pathway_ids = set(direct_pathway_ids) | set(group_pathway_ids)

        queryset = Pathway.objects.filter(id__in=all_pathway_ids).select_related('teacher').prefetch_related(
             Prefetch(
                 'progresses', # Usa il related_name corretto
                 queryset=PathwayProgress.objects.filter(student=student).order_by('-started_at'),
                 to_attr='student_progresses_for_pathway'
             ),
             'pathwayquiz_set__quiz'
        ).order_by('-created_at')
        return queryset

    def get_serializer_context(self):
        """ Aggiunge lo studente al contesto del serializer. """
        context = super().get_serializer_context()
        context['student'] = self.request.user
        return context

# --- Vista Studente: Dettaglio Quiz Assegnato ---

class StudentQuizDetailView(generics.RetrieveAPIView):
    """
    API endpoint per uno studente per visualizzare i dettagli di un singolo quiz
    che gli è stato assegnato (direttamente o tramite gruppo).
    """
    queryset = Quiz.objects.all().select_related('teacher', 'source_template') # Queryset base
    serializer_class = QuizSerializer # Usa il serializer esistente per i dettagli del quiz
    permission_classes = [permissions.IsAuthenticated, IsStudentAuthenticated] # Solo studenti autenticati

    def get_object(self):
        """
        Recupera il quiz e verifica che sia assegnato allo studente corrente.
        """
        quiz_id = self.kwargs.get('pk')
        logger.debug(f"StudentQuizDetailView: Tentativo di accesso al quiz ID {quiz_id} da utente {self.request.user}")

        # Recupera l'oggetto quiz usando il lookup field standard (pk)
        quiz = super().get_object()

        # Assicurati che l'utente sia uno studente (CORREZIONE: usare isinstance)
        if not isinstance(self.request.user, Student):
             logger.error(f"StudentQuizDetailView: Tentativo di accesso da utente non studente: {getattr(self.request.user, 'id', 'ID non disponibile')} per quiz {quiz_id}")
             raise PermissionDenied("Utente non è uno studente.")
        # Se il controllo passa, request.user è l'oggetto Student
        student = self.request.user
        logger.debug(f"StudentQuizDetailView: Studente ID {student.id} richiede quiz ID {quiz.id}")

        # Verifica se il quiz è assegnato direttamente allo studente
        is_assigned_directly = QuizAssignment.objects.filter(quiz=quiz, student=student).exists()
        logger.debug(f"StudentQuizDetailView: Quiz {quiz.id} assegnato direttamente a studente {student.id}? {is_assigned_directly}")

        # Verifica se il quiz è assegnato a un gruppo a cui lo studente appartiene
        student_group_ids = list(StudentGroupMembership.objects.filter(student=student).values_list('group_id', flat=True))
        logger.debug(f"StudentQuizDetailView: Studente {student.id} appartiene ai gruppi ID: {student_group_ids}")
        is_assigned_via_group = False
        if student_group_ids:
            is_assigned_via_group = QuizAssignment.objects.filter(quiz=quiz, group_id__in=student_group_ids).exists()
            logger.debug(f"StudentQuizDetailView: Quiz {quiz.id} assegnato ai gruppi {student_group_ids}? {is_assigned_via_group}")
        else:
             logger.debug(f"StudentQuizDetailView: Studente {student.id} non appartiene a nessun gruppo.")

        # Se non è assegnato né direttamente né tramite gruppo, nega l'accesso
        if not is_assigned_directly and not is_assigned_via_group:
            logger.warning(f"Accesso NEGATO: Studente {student.id} non ha accesso al quiz {quiz.id}. Assegnato diretto: {is_assigned_directly}, Assegnato via gruppo: {is_assigned_via_group}")
            # Usa PermissionDenied da django.core.exceptions che DRF mappa a 403
            raise PermissionDenied("Questo quiz non ti è stato assegnato.")

        # Se i controlli passano, restituisci l'oggetto quiz
        logger.info(f"Accesso CONSENTITO: Studente {student.id} ha accesso al quiz {quiz.id}. Assegnato diretto: {is_assigned_directly}, Assegnato via gruppo: {is_assigned_via_group}")
        return quiz

# --- Vista per Dettagli Tentativo Percorso Studente ---

class PathwayAttemptDetailView(generics.RetrieveAPIView):
    """
    Restituisce i dettagli di un percorso per lo studente che lo sta svolgendo,
    includendo il progresso e il prossimo quiz da affrontare.
    """
    queryset = Pathway.objects.all().prefetch_related('pathwayquiz_set__quiz') # Queryset base
    serializer_class = PathwayAttemptDetailSerializer
    permission_classes = [IsStudentAuthenticated] # Solo studenti autenticati

    def get_object(self):
        """ Recupera il percorso e verifica l'assegnazione allo studente. """
        pathway = super().get_object() # Recupera il percorso usando il pk dall'URL
        student = self.request.user

        # Verifica se il percorso è assegnato allo studente
        is_assigned = PathwayAssignment.objects.filter(pathway=pathway, student=student).exists()
        if not is_assigned:
            # Solleva PermissionDenied se non assegnato
            raise DRFPermissionDenied("Questo percorso non ti è stato assegnato.")

        return pathway

    def retrieve(self, request, *args, **kwargs):
        """
        Recupera i dati del percorso, calcola il prossimo quiz e aggiunge
        le informazioni al serializer.
        """
        pathway = self.get_object() # Ottiene il percorso e verifica l'assegnazione
        student = request.user

        # Recupera o crea il progresso dello studente per questo percorso
        progress, created = PathwayProgress.objects.get_or_create(
            student=student,
            pathway=pathway,
            defaults={'status': PathwayProgress.ProgressStatus.IN_PROGRESS}
        )

        next_quiz = None
        if progress.status == PathwayProgress.ProgressStatus.IN_PROGRESS:
            last_completed_order = progress.last_completed_quiz_order
            # Trova il quiz nel percorso con l'ordine successivo
            next_pathway_quiz = pathway.pathwayquiz_set.filter(
                order__gt=last_completed_order if last_completed_order is not None else -1
            ).order_by('order').first()

            if next_pathway_quiz:
                next_quiz = next_pathway_quiz.quiz

        # Serializza il percorso
        serializer = self.get_serializer(pathway)
        data = serializer.data

        # Aggiungi manualmente i dati del progresso e del prossimo quiz
        # (Il serializer li ha definiti come read_only, quindi li popoliamo qui)
        data['progress'] = PathwayProgressSerializer(progress).data if progress else None
        data['next_quiz'] = NextPathwayQuizSerializer(next_quiz).data if next_quiz else None # Corretto: Usa il serializer importato

        return Response(data)

# --- Teacher Grading ViewSet ---

class TeacherGradingViewSet(viewsets.GenericViewSet):
    """
    ViewSet per i docenti per gestire la correzione manuale dei QuizAttempt.
    """
    permission_classes = [permissions.IsAuthenticated, IsTeacherUser]

    # Serializer di base per il ViewSet (potrebbe non essere usato direttamente se tutte le azioni ne specificano uno)
    # serializer_class = QuizAttemptSerializer # O un serializer più specifico se necessario

    def get_queryset(self):
        """
        Restituisce i QuizAttempt che il docente autenticato è autorizzato a vedere/correggere.
        Il filtro di base qui è sui quiz creati dal docente.
        Le azioni specifiche possono aggiungere ulteriori filtri o logiche di permesso.
        """
        user = self.request.user
        # Filtra i tentativi relativi ai quiz creati dal docente autenticato.
        # Questo serve come base per le azioni che poi selezioneranno un tentativo specifico
        # o elencheranno quelli in attesa di correzione.
        return QuizAttempt.objects.filter(quiz__teacher=user).distinct()


    @action(detail=False, methods=['get'], url_path='pending-attempts', serializer_class=PendingQuizAttemptSerializer)
    def list_pending_attempts(self, request):
        """
        Elenca tutti i QuizAttempt in stato 'PENDING_GRADING' che richiedono
        l'attenzione del docente autenticato.
        """
        user = request.user
        # Filtra i tentativi in attesa di correzione per i quiz creati dal docente
        # o per quiz assegnati a studenti/gruppi del docente.
        # La logica esatta di "competenza" del docente potrebbe variare.
        # Per ora, un docente vede i tentativi PENDING_GRADING dei quiz che ha creato.
        # O tentativi di quiz assegnati ai suoi studenti (se QuizAssignment traccia il docente)
        # O tentativi di quiz assegnati ai suoi gruppi.

        # Un approccio potrebbe essere: il docente vede i tentativi PENDING_GRADING dei quiz che LUI ha creato.
        pending_attempts = QuizAttempt.objects.filter(
            quiz__teacher=user, # Il docente è il creatore del quiz originale
            status=QuizAttempt.AttemptStatus.PENDING_GRADING
        ).select_related('student', 'quiz').order_by('-completed_at') # Ordina per data di sottomissione

        # TODO: Considerare anche i quiz che il docente non ha creato ma a cui ha accesso per correzione
        # (es. se un admin assegna un quiz e delega la correzione, o per co-docenti)
        # Questo richiederebbe una logica di permessi più granulare.

        page = self.paginate_queryset(pending_attempts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(pending_attempts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path=r'attempts/(?P<pk>[^/.]+)/details-for-grading', serializer_class=GradingQuizAttemptDetailSerializer)
    def get_attempt_details_for_grading(self, request, pk=None):
        """
        Restituisce i dettagli completi di un QuizAttempt specifico per la correzione,
        incluse tutte le domande e le relative risposte dello studente.
        Il pk è l'ID del QuizAttempt.
        """
        # Utilizza il queryset del ViewSet che già filtra per quiz__teacher=request.user
        # e aggiunge select_related specifici per questa azione.
        queryset = self.get_queryset().select_related('student', 'quiz', 'quiz__teacher')
        attempt = get_object_or_404(queryset, pk=pk)

        # Verifica permessi: il docente può correggere questo tentativo?
        # Ad esempio, se è il docente del quiz o se il tentativo è per un suo studente.
        if attempt.quiz.teacher != request.user:
            # Potremmo aggiungere un controllo più granulare se lo studente appartiene al docente
            # if not Student.objects.filter(user=request.user, students__quiz_attempts=attempt).exists():
            # Per ora, semplice controllo sul creatore del quiz.
            raise DRFPermissionDenied("Non sei autorizzato a correggere questo tentativo.")

        if attempt.status != QuizAttempt.AttemptStatus.PENDING_GRADING:
            return Response(
                {'detail': 'Questo tentativo non è in attesa di correzione manuale.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(attempt, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path=r'attempts/(?P<pk>[^/.]+)/finalize-grading', serializer_class=GradeSubmissionSerializer)
    @transaction.atomic
    def finalize_grading(self, request, pk=None):
        """
        Permette al docente di inviare le valutazioni per le risposte aperte
        di un QuizAttempt e finalizzare la correzione.
        Il pk è l'ID del QuizAttempt.
        """
        # Utilizza il queryset del ViewSet che già filtra per quiz__teacher=request.user
        # e aggiunge select_related specifici per questa azione.
        queryset = self.get_queryset().select_related('quiz', 'student', 'quiz__teacher')
        attempt = get_object_or_404(queryset, pk=pk)

        # Verifica permessi
        if attempt.quiz.teacher != request.user:
            raise DRFPermissionDenied("Non sei autorizzato a finalizzare la correzione per questo tentativo.")

        if attempt.status != QuizAttempt.AttemptStatus.PENDING_GRADING:
            return Response(
                {'detail': 'Questo tentativo non è (o non è più) in attesa di correzione manuale.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        graded_answers_data = serializer.validated_data['answers']
        student_answer_ids_from_payload = {item['student_answer_id'] for item in graded_answers_data}

        # Verifica che tutte le risposte aperte del tentativo siano state inviate per la correzione
        open_manual_answer_ids_for_attempt = set(
            StudentAnswer.objects.filter(
                quiz_attempt=attempt,
                question__question_type=QuestionType.OPEN_ANSWER_MANUAL
            ).values_list('id', flat=True)
        )

        if student_answer_ids_from_payload != open_manual_answer_ids_for_attempt:
            missing_ids = open_manual_answer_ids_for_attempt - student_answer_ids_from_payload
            extra_ids = student_answer_ids_from_payload - open_manual_answer_ids_for_attempt
            error_detail = "Payload di correzione incompleto o errato. "
            if missing_ids:
                error_detail += f"Mancano le correzioni per le risposte ID: {missing_ids}. "
            if extra_ids:
                error_detail += f"Sono state inviate correzioni per ID non pertinenti o non aperti: {extra_ids}."
            return Response({'detail': error_detail}, status=status.HTTP_400_BAD_REQUEST)


        total_score_from_manual = 0
        for item_data in graded_answers_data:
            try:
                student_answer = StudentAnswer.objects.get(
                    pk=item_data['student_answer_id'],
                    quiz_attempt=attempt, # Assicura che la risposta appartenga a questo tentativo
                    question__question_type=QuestionType.OPEN_ANSWER_MANUAL # Doppia verifica
                )
                student_answer.is_correct = item_data['is_correct']
                student_answer.score = 1.0 if item_data['is_correct'] else 0.0 # Punteggio 0 o 1
                student_answer.teacher_comment = item_data.get('teacher_comment')
                student_answer.save(update_fields=['is_correct', 'score', 'teacher_comment'])
                total_score_from_manual += student_answer.score
            except StudentAnswer.DoesNotExist:
                # Questo non dovrebbe accadere se la validazione degli ID è corretta
                logger.error(f"StudentAnswer ID {item_data['student_answer_id']} non trovata durante la finalizzazione della correzione per l'attempt {attempt.id}.")
                # Potremmo voler sollevare un errore qui o semplicemente loggare e continuare
                return Response({'detail': f"Errore interno: Risposta studente con ID {item_data['student_answer_id']} non trovata."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                 logger.error(f"Errore durante l'aggiornamento di StudentAnswer ID {item_data['student_answer_id']}: {e}", exc_info=True)
                 return Response({'detail': f"Errore durante l'aggiornamento della risposta: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        # Ricalcola il punteggio totale del QuizAttempt e aggiorna lo stato
        # Questo metodo dovrebbe considerare sia le risposte auto-corrette sia quelle manuali
        final_score_value = attempt.calculate_final_score() # Questo metodo ora dovrebbe usare i .score delle StudentAnswer
        
        # Assegna punti e badge (questo metodo aggiorna anche lo stato dell'attempt a COMPLETED/FAILED)
        newly_earned_badges = attempt.assign_completion_points()
        
        # completed_at è stato impostato quando lo studente ha sottomesso.
        # Lo stato è aggiornato da assign_completion_points.
        # Lo score è aggiornato da calculate_final_score.
        attempt.save() # Salva le modifiche allo score e allo stato.

        # --- CREAZIONE NOTIFICA PER LO STUDENTE ---
        if attempt.status in [QuizAttempt.AttemptStatus.COMPLETED, QuizAttempt.AttemptStatus.FAILED]:
            try:
                notification_message = f"Il tuo quiz '{attempt.quiz.title}' è stato corretto!"
                notification_link = f"/quiz/attempt/{attempt.id}/result" # Assumendo questa struttura URL per il frontend
                
                Notification.objects.create(
                    student=attempt.student,
                    message=notification_message,
                    link=notification_link,
                    notification_type=NotificationType.QUIZ_GRADED
                )
                logger.info(f"Notifica creata per studente {attempt.student.id} per correzione attempt {attempt.id}.")
            except Exception as e_notif:
                logger.error(f"Errore durante la creazione della notifica per attempt {attempt.id} (studente {attempt.student.id}): {e_notif}", exc_info=True)
        # --- FINE CREAZIONE NOTIFICA ---

        logger.info(f"Correzione manuale per QuizAttempt {attempt.id} finalizzata dal docente {request.user.username}. Score finale: {attempt.score}, Stato: {attempt.status}")

        # Serializza il tentativo aggiornato per la risposta
        # Potremmo voler un serializer specifico per la risposta post-correzione
        response_serializer = QuizAttemptDetailSerializer(attempt, context={'request': request, 'newly_earned_badges': newly_earned_badges})
        return Response(response_serializer.data, status=status.HTTP_200_OK)
