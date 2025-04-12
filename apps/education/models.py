from django.conf import settings
from django.db import models, transaction # Import transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Max as AggregateMax # Rinomina Max per evitare conflitti

# Import Student model
from apps.users.models import Student, UserRole, User # Ripristinato import UserRole e User
from django.utils import timezone # Import timezone
from django.db.models import F # Import F for atomic updates
# Import Wallet and PointTransaction later to avoid circular dependency if needed,
# or ensure they are defined before QuizAttempt if in the same file.
# Let's import them here for clarity for now.
from apps.rewards.models import Wallet, PointTransaction, Badge, EarnedBadge # Import Badge and EarnedBadge
import logging # Import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Choices for Question Types (consistent with design doc)
class QuestionType(models.TextChoices):
    MULTIPLE_CHOICE_SINGLE = 'MC_SINGLE', _('Multiple Choice (Single Answer)')
    MULTIPLE_CHOICE_MULTIPLE = 'MC_MULTI', _('Multiple Choice (Multiple Answers)')
    TRUE_FALSE = 'TF', _('True/False')
    FILL_BLANK = 'FILL_BLANK', _('Fill in the Blank')
    OPEN_ANSWER_MANUAL = 'OPEN_MANUAL', _('Open Answer (Manual Grading)')


# --- Template Models (Created by Admin) ---

from django.db.models import Q, CheckConstraint # Import Q e CheckConstraint

class QuizTemplate(models.Model):
    """ Template per un Quiz, creato da Admin (globale) o Docente (locale). """
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Meglio SET_NULL se l'admin viene eliminato
        related_name='admin_created_quiz_templates', # Nome più specifico
        limit_choices_to={'role': 'ADMIN'},
        verbose_name=_('Admin Creator'),
        null=True, # Rendi opzionale
        blank=True
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Meglio SET_NULL se il docente viene eliminato
        related_name='teacher_created_quiz_templates', # Nome specifico
        limit_choices_to={'role': 'TEACHER'},
        verbose_name=_('Teacher Creator'),
        null=True, # Rendi opzionale
        blank=True
    )
    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField(_('Description'), blank=True)
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Extra data like difficulty ("easy", "medium", "hard"), subject ("Math", "History"), etc. Example: {"difficulty": "medium", "subject": "Physics"}')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Quiz Template')
        verbose_name_plural = _('Quiz Templates')
        ordering = ['title']
        constraints = [
            CheckConstraint(
                check=Q(admin__isnull=False) | Q(teacher__isnull=False),
                name='quiz_template_creator_check',
                violation_error_message=_('Un template di quiz deve avere un Admin o un Docente creatore.')
            ),
             CheckConstraint(
                check=~(Q(admin__isnull=False) & Q(teacher__isnull=False)),
                name='quiz_template_single_creator_check',
                violation_error_message=_('Un template di quiz non può avere sia un Admin che un Docente creatore.')
            )
        ]

    def __str__(self):
        return self.title


class QuestionTemplate(models.Model):
    """ Template per una Domanda all'interno di un QuizTemplate. """
    quiz_template = models.ForeignKey(
        QuizTemplate,
        on_delete=models.CASCADE,
        related_name='question_templates',
        verbose_name=_('Quiz Template')
    )
    text = models.TextField(_('Question Text'))
    question_type = models.CharField(
        _('Question Type'),
        max_length=20,
        choices=QuestionType.choices
    )
    order = models.PositiveIntegerField(
        _('Order'),
        default=0,
        help_text=_('Order of the question within the template.')
    )
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Specific config based on type. E.g., for FILL_BLANK: {"correct_answers": ["Paris", "paris"], "case_sensitive": false}. For MC/TF: {"points_per_correct_answer": 2}.')
    )

    class Meta:
        verbose_name = _('Question Template')
        verbose_name_plural = _('Question Templates')
        ordering = ['quiz_template', 'order']
        unique_together = ('quiz_template', 'order') # Ensure unique order within a template

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}... ({self.quiz_template.title})"


class AnswerOptionTemplate(models.Model):
    """ Template per un'Opzione di Risposta (per tipi MC, TF). """
    question_template = models.ForeignKey(
        QuestionTemplate,
        on_delete=models.CASCADE,
        related_name='answer_option_templates',
        verbose_name=_('Question Template')
    )
    text = models.CharField(_('Option Text'), max_length=500)
    is_correct = models.BooleanField(
        _('Is Correct?'),
        default=False,
        help_text=_('Is this the/a correct answer for the question?')
    )
    order = models.PositiveIntegerField(
        _('Order'),
        default=0,
        help_text=_('Display order of the option.')
    )

    class Meta:
        verbose_name = _('Answer Option Template')
        verbose_name_plural = _('Answer Option Templates')
        ordering = ['question_template', 'order']
        unique_together = ('question_template', 'order')

    def __str__(self):
        return f"Opt{self.order}: {self.text[:50]}... ({self.question_template})"

class PathwayTemplate(models.Model):
    """ Template per un Percorso Educativo, creato da Admin o Docente?
        Per ora assumiamo Docente, come per Quiz/Pathway concreti,
        ma potrebbe essere esteso ad Admin. """
    # Se si vuole permettere anche agli Admin di creare template globali:
    # creator = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.CASCADE,
    #     related_name='created_pathway_templates',
    #     # limit_choices_to={'role__in': ['ADMIN', 'TEACHER']}, # Se entrambi
    #     limit_choices_to={'role': 'TEACHER'}, # Per ora solo Docente
    #     verbose_name=_('Creator')
    # )
    teacher = models.ForeignKey( # Manteniamo 'teacher' per coerenza con Pathway
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_pathway_templates',
        limit_choices_to={'role': 'TEACHER'},
        verbose_name=_('Teacher')
    )
    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField(_('Description'), blank=True)
    quiz_templates = models.ManyToManyField(
        QuizTemplate,
        through='PathwayQuizTemplate', # Specifica il modello intermedio
        related_name='pathway_templates',
        verbose_name=_('Quiz Templates')
    )
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('E.g., points_on_completion. Example: {"points_on_completion": 50}')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Pathway Template')
        verbose_name_plural = _('Pathway Templates')
        ordering = ['title']

    def __str__(self):
        return f"[Template] {self.title}"


class PathwayQuizTemplate(models.Model):
    """ Modello intermedio per la relazione M2M tra PathwayTemplate e QuizTemplate. """
    pathway_template = models.ForeignKey(PathwayTemplate, on_delete=models.CASCADE)
    quiz_template = models.ForeignKey(QuizTemplate, on_delete=models.CASCADE) # Collega a QuizTemplate
    order = models.PositiveIntegerField(
        _('Order'),
        help_text=_('Order of the quiz template within the pathway template.')
    )

    class Meta:
        verbose_name = _('Pathway Quiz Template')
        verbose_name_plural = _('Pathway Quiz Templates')
        ordering = ['pathway_template', 'order']
        unique_together = ('pathway_template', 'order') # Unico ordine per template percorso
        # unique_together = ('pathway_template', 'quiz_template') # Un template quiz può apparire una sola volta? Probabilmente sì.

    def __str__(self):
        return f"{self.pathway_template.title} - Step {self.order}: {self.quiz_template.title}"


# --- Concrete Models (Created/Managed by Teacher) ---

class Quiz(models.Model):
    """ Quiz specifico creato da un Docente, possibilmente da un template. """
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_quizzes',
        limit_choices_to={'role': 'TEACHER'},
        verbose_name=_('Teacher')
    )
    source_template = models.ForeignKey(
        QuizTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quizzes_from_template',
        verbose_name=_('Source Template')
    )
    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField(_('Description'), blank=True, null=True) # Aggiunto null=True
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('E.g., difficulty, subject, completion_threshold_percent (0-100), points_on_completion. Example: {"difficulty": "hard", "completion_threshold_percent": 75.0, "points_on_completion": 10}')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    available_from = models.DateTimeField(_('Available From'), null=True, blank=True)
    available_until = models.DateTimeField(_('Available Until'), null=True, blank=True)
    # Relazione M2M implicita per studenti assegnati (gestita esternamente o con modello dedicato se necessario)

    class Meta:
        verbose_name = _('Quiz')
        verbose_name_plural = _('Quizzes')
        ordering = ['title']

    def __str__(self):
        return self.title

    def get_max_possible_score(self) -> float:
        """
        Calcola il punteggio massimo possibile per questo quiz.
        Assume:
        - 1 punto per MC_SINGLE, MC_MULTI, TF, FILL_BLANK (a meno che specificato diversamente in metadata).
        - Punteggio definito in metadata['max_score'] per OPEN_MANUAL.
        Restituisce un float per gestire potenziali punteggi frazionari futuri.
        """
        total_max_score = 0.0
        for question in self.questions.all():
            if question.question_type == QuestionType.OPEN_ANSWER_MANUAL:
                # Per domande manuali, usa 'max_score' dai metadati, default a 1 se non presente
                max_score = float(question.metadata.get('max_score', 1.0))
                total_max_score += max_score
            elif question.question_type == QuestionType.FILL_BLANK:
                 # Per fill_blank, conta il numero di risposte corrette attese, default a 1
                 num_blanks = len(question.metadata.get('correct_answers', [1])) # Default a 1 blank se non specificato
                 points_per_blank = float(question.metadata.get('points_per_blank', 1.0)) # Default 1 punto per blank
                 total_max_score += num_blanks * points_per_blank
            else:
                # Per MC e TF, usa 'points_per_correct_answer', default a 1.0
                points = float(question.metadata.get('points_per_correct_answer', 1.0))
                total_max_score += points
        return total_max_score


class Question(models.Model):
    """ Domanda specifica all'interno di un Quiz. """
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('Quiz')
    )
    text = models.TextField(_('Question Text'))
    question_type = models.CharField(
        _('Question Type'),
        max_length=20,
        choices=QuestionType.choices
    )
    order = models.PositiveIntegerField(
        _('Order'),
        default=0,
        help_text=_('Order of the question within the quiz.')
    )
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Specific config based on type. E.g., for FILL_BLANK: {"correct_answers": ["Rome", "rome"], "case_sensitive": false}. For MC/TF: {"points_per_correct_answer": 1}. For OPEN_MANUAL: {"max_score": 5}.')
    )

    class Meta:
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')
        ordering = ['quiz', 'order']
        unique_together = ('quiz', 'order')

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}... ({self.quiz.title})"


class AnswerOption(models.Model):
    """ Opzione di Risposta specifica per una Domanda (per tipi MC, TF). """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answer_options',
        verbose_name=_('Question')
    )
    text = models.CharField(_('Option Text'), max_length=500)
    is_correct = models.BooleanField(
        _('Is Correct?'),
        default=False
    )
    order = models.PositiveIntegerField(
        _('Order'),
        default=0,
        help_text=_('Display order of the option.')
    )

    class Meta:
        verbose_name = _('Answer Option')
        verbose_name_plural = _('Answer Options')
        ordering = ['question', 'order']
        unique_together = ('question', 'order')

    def __str__(self):
        return f"Opt{self.order}: {self.text[:50]}... ({self.question})"


class Pathway(models.Model):
    """ Percorso Educativo composto da più Quiz, creato da un Docente. """
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_pathways',
        limit_choices_to={'role': 'TEACHER'},
        verbose_name=_('Teacher')
    )
    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField(_('Description'), blank=True)
    source_template = models.ForeignKey(
        PathwayTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pathways_from_template',
        verbose_name=_('Source Template')
    )
    quizzes = models.ManyToManyField(
        Quiz,
        through='PathwayQuiz', # Specifica il modello intermedio
        related_name='pathways',
        verbose_name=_('Quizzes')
    )
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('E.g., points_on_completion. Example: {"points_on_completion": 50}')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Pathway')
        verbose_name_plural = _('Pathways')
        ordering = ['title']

    def __str__(self):
        return self.title


class PathwayQuiz(models.Model):
    """ Modello intermedio per la relazione M2M tra Pathway e Quiz, definisce l'ordine. """
    pathway = models.ForeignKey(Pathway, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE) # O PROTECT se un quiz non può essere eliminato se in un percorso?
    order = models.PositiveIntegerField(
        _('Order'),
        help_text=_('Order of the quiz within the pathway.')
    )

    class Meta:
        verbose_name = _('Pathway Quiz')
        verbose_name_plural = _('Pathway Quizzes')
        ordering = ['pathway', 'order']
        unique_together = ('pathway', 'order') # Unico ordine per percorso
        # unique_together = ('pathway', 'quiz') # Un quiz può apparire una sola volta in un percorso? Probabilmente sì.

    def __str__(self):
        return f"{self.pathway.title} - Step {self.order}: {self.quiz.title}"


# --- Student Progress/Attempt Models ---

class QuizAttempt(models.Model):
    """ Registra un tentativo di uno Studente di completare un Quiz. """
    class AttemptStatus(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        PENDING_GRADING = 'PENDING', _('Pending Manual Grading')
        COMPLETED = 'COMPLETED', _('Completed (Passed)') # Chiarito che COMPLETED implica superato
        FAILED = 'FAILED', _('Completed (Failed)') # Nuovo stato per tentativi non superati

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        verbose_name=_('Student')
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE, # O PROTECT?
        related_name='attempts',
        verbose_name=_('Quiz')
    )
    started_at = models.DateTimeField(_('Started At'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)
    score = models.FloatField( # Usiamo Float per punteggi percentuali o ponderati
        _('Score'),
        null=True,
        blank=True,
        help_text=_('Final score achieved (e.g., percentage or total points).')
    )
    # points_earned: Calcolato al momento del completamento se le condizioni sono soddisfatte (Non è un campo DB diretto)
    first_correct_completion = models.BooleanField(
        _('First Correct Completion?'),
        default=False,
        help_text=_('Indica se questo è stato il primo tentativo superato con successo per questo quiz da parte dello studente.')
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=AttemptStatus.choices,
        default=AttemptStatus.IN_PROGRESS
    )

    class Meta:
        verbose_name = _('Quiz Attempt')
        verbose_name_plural = _('Quiz Attempts')
        ordering = ['student', '-started_at']

    def __str__(self):
        return f"Attempt by {self.student.full_name} on {self.quiz.title} ({self.status})"

    # Methods moved from AttemptViewSet
    def calculate_final_score(self):
        """
        Calculates the final score for this attempt based on saved answers.

        This method operates on the QuizAttempt instance (`self`).
        It evaluates automatically gradable questions (MC_SINGLE, MC_MULTI, TF, FILL_BLANK)
        and calculates a score percentage based on those.

        If only manually graded questions (OPEN_MANUAL) exist and have been graded,
        it calculates the score based on the percentage of correctly marked manual answers.

        Note: The current logic prioritizes the score from auto-graded questions if present.
              Manually assigned scores on OPEN_MANUAL questions are used primarily for teacher feedback
              unless *only* manual questions exist in the quiz.

        Returns:
            float: The calculated final score (percentage, 0-100), rounded to 2 decimal places.
        """
        score = 0
        # Recupera le risposte dello studente per questo tentativo
        student_answers = self.student_answers.select_related('question').all()
        quiz = self.quiz

        # Pre-fetch questions and their correct options for efficiency
        questions = quiz.questions.prefetch_related('answer_options').all()
        correct_options_map = {}
        fill_blank_answers_map = {}
        total_questions = 0 # Conteggio totale domande (per punteggio manuale)
        total_autograded_questions = 0 # Conteggio domande auto-gradate

        for q in questions:
            total_questions += 1
            # Considera solo le domande a correzione automatica per il calcolo del punteggio %
            if q.question_type != QuestionType.OPEN_ANSWER_MANUAL:
                total_autograded_questions += 1
                if q.question_type in [QuestionType.MULTIPLE_CHOICE_SINGLE, QuestionType.TRUE_FALSE]:
                     correct_option = q.answer_options.filter(is_correct=True).first()
                     if correct_option:
                         correct_options_map[q.id] = correct_option.id
                elif q.question_type == QuestionType.MULTIPLE_CHOICE_MULTIPLE:
                     correct_options_map[q.id] = set(q.answer_options.filter(is_correct=True).values_list('id', flat=True))
                elif q.question_type == QuestionType.FILL_BLANK:
                    correct_answers = [ans.strip().lower() for ans in q.metadata.get('correct_answers', [])]
                    fill_blank_answers_map[q.id] = correct_answers

        # Se non ci sono domande auto-gradate, non possiamo calcolare un punteggio automatico
        if total_autograded_questions == 0:
            # Potremmo controllare se ci sono domande manuali e se sono state valutate,
            # ma per ora restituiamo None se non ci sono domande auto-gradate.
            # Oppure potremmo impostare lo stato su PENDING_GRADING se ci sono domande manuali.
            logger.info(f"Attempt {self.id}: No auto-gradable questions found. Score calculation skipped.")
            # Se ci sono domande totali ma nessuna auto-gradabile, probabilmente sono tutte manuali
            if total_questions > 0:
                 self.status = self.AttemptStatus.PENDING_GRADING
                 self.save(update_fields=['status'])
                 logger.info(f"Attempt {self.id}: Status set to PENDING_GRADING as only manual questions exist.")
            self.score = None # Assicura che lo score sia None
            self.save(update_fields=['score'])
            return None # O 0.0? None indica che non è stato calcolato automaticamente.

        correct_answers_count = 0
        total_score_points = 0.0 # Punteggio basato sui punti per domanda
        max_possible_points = 0.0 # Punteggio massimo possibile dalle domande auto-gradate

        for answer in student_answers:
            q = answer.question
            # Considera solo le risposte a domande auto-gradate per il punteggio
            if q.question_type != QuestionType.OPEN_ANSWER_MANUAL:
                points_per_correct = float(q.metadata.get('points_per_correct_answer', 1.0)) # Default a 1 punto
                max_possible_points += points_per_correct # Aggiungi al massimo possibile

                is_correct = False # Resetta per ogni risposta
                selected_data = answer.selected_answers

                if q.question_type == QuestionType.MULTIPLE_CHOICE_SINGLE:
                    correct_option_id = correct_options_map.get(q.id)
                    selected_option_id = selected_data.get('answer_option_id') if isinstance(selected_data, dict) else None
                    if correct_option_id is not None and selected_option_id == correct_option_id:
                        is_correct = True

                elif q.question_type == QuestionType.TRUE_FALSE:
                    correct_option_id = correct_options_map.get(q.id)
                    selected_bool = selected_data.get('is_true') if isinstance(selected_data, dict) else None
                    # Trova l'opzione corretta per determinare se la risposta attesa è True o False
                    correct_option_obj = q.answer_options.filter(id=correct_option_id).first() if correct_option_id else None
                    if correct_option_obj:
                         expected_bool = correct_option_obj.text.lower() == 'vero' # O un check più robusto
                         if selected_bool == expected_bool:
                             is_correct = True
                    # Se correct_option_obj non esiste o selected_bool è None, is_correct rimane False

                elif q.question_type == QuestionType.MULTIPLE_CHOICE_MULTIPLE:
                    correct_option_ids = correct_options_map.get(q.id, set())
                    selected_option_ids = set(selected_data.get('answer_option_ids', [])) if isinstance(selected_data, dict) else set()
                    if correct_option_ids == selected_option_ids:
                        is_correct = True

                elif q.question_type == QuestionType.FILL_BLANK:
                    correct_answers_list = fill_blank_answers_map.get(q.id, [])
                    submitted_answers = selected_data.get('answers', []) if isinstance(selected_data, dict) else []
                    case_sensitive = q.metadata.get('case_sensitive', False)

                    if len(correct_answers_list) == len(submitted_answers):
                        all_match = True
                        for i, correct_ans in enumerate(correct_answers_list):
                            submitted = submitted_answers[i]
                            correct_str = str(correct_ans)
                            submitted_str = str(submitted)
                            if not case_sensitive:
                                if correct_str.lower() != submitted_str.lower(): all_match = False; break
                            else:
                                if correct_str != submitted_str: all_match = False; break
                        if all_match:
                            is_correct = True

                # Aggiorna il conteggio e il punteggio se la risposta è corretta
                if is_correct:
                    correct_answers_count += 1
                    total_score_points += points_per_correct

                # Salva is_correct e score sulla singola risposta (se non già fatto in submit_answer)
                # Questo è ridondante se lo facciamo già in submit_answer, ma può servire come fallback
                # o se vogliamo ricalcolare tutto qui. Per ora lo commentiamo assumendo che submit_answer lo faccia.
                # answer.is_correct = is_correct
                # answer.score = points_per_correct if is_correct else 0.0
                # answer.save(update_fields=['is_correct', 'score'])


        # Calcola il punteggio percentuale finale
        final_score_percent = 0.0
        if max_possible_points > 0:
            final_score_percent = round((total_score_points / max_possible_points) * 100, 2)
        else:
            # Se non ci sono punti massimi possibili (es. solo domande con 0 punti?), il punteggio è 0 o indeterminato?
            # Per ora impostiamo a 0.
            final_score_percent = 0.0

        # Salva il punteggio finale sul tentativo
        self.score = final_score_percent
        self.save(update_fields=['score'])
        logger.info(f"Attempt {self.id}: Final score calculated: {final_score_percent}% ({total_score_points}/{max_possible_points} points)")

        return final_score_percent


    @transaction.atomic # Assicura atomicità per punti e badge
    def assign_completion_points(self) -> list[EarnedBadge]: # Aggiunto tipo di ritorno
        logger.info(f"Attempt {self.id}: Entering assign_completion_points. Current status: {self.status}, Score: {self.score}") # LOGGING
        """
        Assigns points and potentially the 'first-quiz-completed' badge
        if the quiz attempt is the first successful one for the student.
        Also updates the attempt status based on score and threshold.
        Returns a list of newly earned Badge instances.
        """
        newly_earned_badges = [] # Inizializza lista badge guadagnati
        logger.info(f"Attempt {self.id}: Entering assign_completion_points. Current status: {self.status}, Score: {self.score}") # LOGGING
        # Ensure score is calculated and available
        if self.score is None:
             logger.warning(f"Attempt {self.id}: Score is None, cannot assign points or determine status accurately.")
             # Decide how to handle this - maybe recalculate? For now, just return or set to FAILED.
             if self.status == self.AttemptStatus.IN_PROGRESS: # Avoid overwriting PENDING_GRADING
                 self.status = self.AttemptStatus.FAILED
                 self.save(update_fields=['status'])
             return

        # Determine pass/fail based on threshold
        threshold = self.quiz.metadata.get('completion_threshold_percent', 100.0) # Default to 100% if not set
        passed = self.score >= threshold

        # Update status based on pass/fail, only if currently IN_PROGRESS or PENDING (after grading)
        if self.status in [self.AttemptStatus.IN_PROGRESS, self.AttemptStatus.PENDING_GRADING]:
             self.status = self.AttemptStatus.COMPLETED if passed else self.AttemptStatus.FAILED
             self.save(update_fields=['status']) # Save status update

        # Award points logic (only if passed)
        points_to_award = 0
        if passed:
            points_to_award = self.quiz.metadata.get('points_on_completion', 0)

            # Check if this is the first *successful* completion for this specific quiz
            is_first_successful_for_this_quiz = not QuizAttempt.objects.filter(
                quiz=self.quiz,
                student=self.student,
                status=self.AttemptStatus.COMPLETED
            ).exclude(pk=self.pk).exists() # Exclude the current attempt

            if is_first_successful_for_this_quiz:
                self.first_correct_completion = True # Mark this attempt
                logger.info(f"Attempt {self.id} is the first successful completion for quiz {self.quiz.id} by student {self.student.id}.")
            else:
                 self.first_correct_completion = False # Ensure it's False otherwise
                 logger.info(f"Attempt {self.id} is NOT the first successful completion for quiz {self.quiz.id} by student {self.student.id}.")

            # Save first_correct_completion status
            self.save(update_fields=['first_correct_completion'])

            # Award points only on the first successful completion and if points > 0
            if is_first_successful_for_this_quiz and points_to_award > 0:
                try:
                    wallet = Wallet.objects.get(student=self.student)
                    # Use atomic transaction for updating wallet and creating transaction
                    with transaction.atomic():
                        # Use F() expression for atomic update
                        wallet.current_points = F('current_points') + points_to_award
                        wallet.save(update_fields=['current_points'])
                        PointTransaction.objects.create(
                            wallet=wallet,
                            points_change=points_to_award,
                            reason=f"Completamento Quiz: {self.quiz.title}"
                        )
                        logger.info(f"Awarded {points_to_award} points to student {self.student.id} for completing quiz {self.quiz.id}.")
                except Wallet.DoesNotExist:
                    logger.error(f"Wallet not found for student {self.student.id} when trying to award points for quiz {self.quiz.id}.")
                except Exception as e_points:
                    logger.exception(f"Error awarding points for quiz attempt {self.id}: {e_points}")

            # --- Logica Assegnazione Badge per Soglia Punti ---
            # Questo controllo va fatto se il quiz è stato superato, dopo l'eventuale assegnazione punti.
            try:
                # Recupera il wallet (potrebbe non essere stato caricato se points_to_award era 0 o non era la prima volta)
                # Usiamo select_for_update per bloccare la riga del wallet durante il controllo della soglia
                # per evitare race conditions se più tentativi finiscono contemporaneamente.
                # Nota: Questo richiede che il DB supporti SELECT FOR UPDATE (PostgreSQL lo fa).
                wallet = Wallet.objects.select_for_update().get(student=self.student)
                # Ricarica sempre dal DB per avere il saldo più aggiornato possibile dopo l'eventuale F() expression
                wallet.refresh_from_db()
                current_points = wallet.current_points
                logger.info(f"Attempt {self.id}: Student {self.student.id} current points: {current_points}. Checking threshold badges.")

                # Recupera tutti i badge di soglia attivi
                threshold_badges = Badge.objects.filter(
                    is_active=True,
                    trigger_type='POINTS_THRESHOLD' # Usa la stringa diretta
                )

                for badge in threshold_badges:
                    try:
                        # Estrai la soglia dalla condizione JSON
                        threshold = int(badge.trigger_condition.get("points", -1)) # CORRETTO: Usa la chiave "points" come da definizione modello
                        if threshold < 0:
                            logger.warning(f"Badge Soglia ID {badge.id} ('{badge.name}') ha una soglia non valida o mancante: {badge.trigger_condition}")
                            continue # Salta questo badge

                        # Controlla se la soglia è raggiunta
                        if current_points >= threshold:
                            logger.info(f"Attempt {self.id}: Student points ({current_points}) >= threshold ({threshold}) for badge '{badge.name}' (ID {badge.id}).")
                            # Tenta di assegnare il badge se non già posseduto
                            earned_badge, created = EarnedBadge.objects.get_or_create(
                                student=self.student,
                                badge=badge,
                                defaults={'earned_at': timezone.now()}
                            )
                            if created:
                                logger.info(f"Badge Soglia '{badge.name}' assegnato a {self.student.full_name}.")
                                newly_earned_badges.append(earned_badge) # Aggiungi alla lista se creato
                                logger.info(f"Attempt {self.id}: Threshold Badge ID {earned_badge.id} aggiunto alla lista newly_earned_badges.")
                            # else: # Log non necessario se già posseduto
                            #    logger.info(f"Studente {self.student.full_name} aveva già il badge '{badge.name}' (threshold).")

                    except (ValueError, TypeError, KeyError) as e_cond:
                        logger.error(f"Errore nel parsing trigger_condition per Badge Soglia {badge.id} ('{badge.name}'): {badge.trigger_condition}. Errore: {e_cond}", exc_info=True)
                    except Exception as e_thresh_badge:
                        logger.error(f"Errore durante l'assegnazione del Badge Soglia {badge.id} ('{badge.name}') a {self.student.id}: {e_thresh_badge}", exc_info=True)

            except Wallet.DoesNotExist:
                logger.error(f"Wallet not found for student {self.student.id} when checking threshold badges.")
            except Exception as e_check_thresh:
                logger.error(f"Errore imprevisto durante il controllo dei badge di soglia per lo studente {self.student.id}: {e_check_thresh}", exc_info=True)
            # --- Fine Logica Badge Soglia Punti ---

            # --- Logica Assegnazione Badge per Completamento Quiz Specifico ---
            try:
                logger.info(f"Attempt {self.id}: Checking specific quiz completion badges.")
                quiz_completion_badges = Badge.objects.filter(
                    is_active=True,
                    trigger_type='QUIZ_COMPLETED' # Usa la stringa diretta
                )

                for badge in quiz_completion_badges:
                    try:
                        condition = badge.trigger_condition
                        required_quiz_id = condition.get("quiz_id") # Può essere None
                        min_score_percent = float(condition.get("min_score_percent", 0)) # Default 0 se non specificato

                        # Controlla se è il quiz giusto (se specificato)
                        quiz_match = (required_quiz_id is None or required_quiz_id == self.quiz.id)

                        # Controlla se il punteggio è sufficiente (usa self.score che è già percentuale 0-100)
                        score_match = (self.score is not None and self.score >= min_score_percent)

                        logger.debug(f"Badge '{badge.name}': ReqQuizID={required_quiz_id}, MinScore={min_score_percent} | CurrentQuizID={self.quiz.id}, CurrentScore={self.score} | QuizMatch={quiz_match}, ScoreMatch={score_match}")

                        if quiz_match and score_match:
                            logger.info(f"Attempt {self.id}: Conditions met for QUIZ_COMPLETED badge '{badge.name}' (ID {badge.id}).")
                            # Tenta di assegnare il badge se non già posseduto
                            earned_badge, created = EarnedBadge.objects.get_or_create(
                                student=self.student,
                                badge=badge,
                                defaults={'earned_at': timezone.now()}
                            )
                            if created:
                                logger.info(f"Badge QUIZ_COMPLETED '{badge.name}' assegnato a {self.student.full_name}.")
                                newly_earned_badges.append(earned_badge) # Aggiungi alla lista se creato
                                logger.info(f"Attempt {self.id}: QUIZ_COMPLETED Badge ID {earned_badge.id} aggiunto alla lista newly_earned_badges.")
                            # else:
                            #    logger.info(f"Studente {self.student.full_name} aveva già il badge '{badge.name}' (QUIZ_COMPLETED).")

                    except (ValueError, TypeError, KeyError) as e_cond:
                         logger.error(f"Errore nel parsing trigger_condition per Badge QUIZ_COMPLETED {badge.id} ('{badge.name}'): {condition}. Errore: {e_cond}", exc_info=True)
                    except Exception as e_quiz_badge:
                        logger.error(f"Errore durante l'assegnazione del Badge QUIZ_COMPLETED {badge.id} ('{badge.name}') a {self.student.id}: {e_quiz_badge}", exc_info=True)

            except Exception as e_check_quiz_comp:
                 logger.error(f"Errore imprevisto durante il controllo dei badge QUIZ_COMPLETED per lo studente {self.student.id}: {e_check_quiz_comp}", exc_info=True)
            # --- Fine Logica Badge Quiz Specifico ---

            # --- Logica Assegnazione Badge "Primo Quiz Completato" (SPOSTATA FUORI DAL BLOCCO PUNTI) ---
            # Controlla se è il primo quiz IN ASSOLUTO completato correttamente dallo studente
            # Questo controllo ha senso farlo solo se il tentativo corrente è stato superato con successo
            # E se è la prima volta che questo specifico quiz viene superato con successo
            # La condizione corretta: controlla solo se il quiz è stato superato.
            # Il controllo se è il primo in assoluto avviene all'interno.
            if passed:
                 logger.info(f"Attempt {self.id}: Quiz passed and first successful for this quiz. Checking for first completion badge.")
                 is_first_ever_completion = not QuizAttempt.objects.filter(
                     student=self.student,
                     status=QuizAttempt.AttemptStatus.COMPLETED
                 ).exclude(pk=self.pk).exists() # Escludi il tentativo corrente

                 logger.info(f"Attempt {self.id}: Checking for first completion badge. is_first_ever_completion={is_first_ever_completion}")
                 if is_first_ever_completion:
                     logger.info(f"Questo è il primo quiz IN ASSOLUTO completato correttamente da {self.student.full_name}. Tentativo assegnazione badge 'Primo Quiz Completato!'.")
                     try:
                         first_quiz_badge = Badge.objects.get(name='Primo Quiz Completato!') # Usa nome corretto
                         earned_badge, created = EarnedBadge.objects.get_or_create(
                             student=self.student,
                             badge=first_quiz_badge,
                             defaults={'earned_at': timezone.now()}
                         )
                         if created:
                             logger.info(f"Badge '{first_quiz_badge.name}' assegnato a {self.student.full_name}.")
                             newly_earned_badges.append(earned_badge) # Aggiungi alla lista se creato
                         else:
                             logger.info(f"Studente {self.student.full_name} aveva già il badge '{first_quiz_badge.name}'.")
                     except Badge.DoesNotExist:
                         logger.warning("Badge con nome 'Primo Quiz Completato!' non trovato nel database. Impossibile assegnare.")
                     except Exception as e_badge:
                         logger.error(f"Errore durante l'assegnazione del badge 'Primo Quiz Completato!' a {self.student.id}: {e_badge}", exc_info=True)
            # --- Fine Logica Badge ---

        # --- Trigger Pathway Progress Update (TEMPORANEAMENTE COMMENTATO PER DEBUG) ---
        # This should happen if the quiz was passed, regardless of points awarded
        pathway_badges = []
        if passed:
             pathway_badges = self.update_pathway_progress() # Cattura i badge dal percorso

        return newly_earned_badges + pathway_badges # Restituisci tutti i badge guadagnati


    def update_pathway_progress(self) -> list[EarnedBadge]: # Aggiunto tipo di ritorno
        """
        Updates the PathwayProgress if this quiz is part of a pathway and was successfully completed.
        Uses the new `completed_orders` field.
        Checks if the pathway itself is now complete and assigns pathway points/badges if applicable.
        Returns a list of newly earned pathway-related Badge instances.
        """
        newly_earned_pathway_badges = [] # Inizializza lista badge guadagnati
        logger.debug(f"Attempt {self.id}: Checking pathway progress update for quiz {self.quiz.id}.")
        # Check if the attempt was successful (status is COMPLETED)
        if self.status != self.AttemptStatus.COMPLETED:
            logger.debug(f"Attempt {self.id}: Quiz not passed (status={self.status}), skipping pathway update.")
            return

        # Find pathways this quiz belongs to and the student is assigned to
        pathway_assignments = PathwayAssignment.objects.filter(
            student=self.student,
            pathway__quizzes=self.quiz # Filtra per percorsi che contengono questo quiz
        ).select_related('pathway')

        logger.debug(f"Attempt {self.id}: Found {pathway_assignments.count()} pathway assignments for student {self.student.id} containing quiz {self.quiz.id}.")

        for assignment in pathway_assignments:
            pathway = assignment.pathway
            # Get the order of the current quiz within this specific pathway
            try:
                pathway_quiz_entry = PathwayQuiz.objects.get(pathway=pathway, quiz=self.quiz)
                current_quiz_order = pathway_quiz_entry.order
            except PathwayQuiz.DoesNotExist:
                logger.warning(f"Attempt {self.id}: Quiz {self.quiz.id} is linked to pathway {pathway.id} but PathwayQuiz entry is missing.")
                continue # Skip this pathway if the link is broken

            # Get or create the progress record for this student and pathway
            progress, created = PathwayProgress.objects.get_or_create(
                student=self.student,
                pathway=pathway,
                defaults={'status': PathwayProgress.ProgressStatus.IN_PROGRESS}
            )

            # Add the current quiz order to the list of completed orders if not already present
            if current_quiz_order not in progress.completed_orders:
                progress.completed_orders.append(current_quiz_order)
                progress.completed_orders.sort() # Mantieni ordinato
                progress.last_completed_quiz_order = max(progress.completed_orders) # Aggiorna l'ultimo completato
                logger.info(f"Attempt {self.id}: Updated pathway {pathway.id} progress for student {self.student.id}. Completed orders: {progress.completed_orders}")
            else:
                 logger.debug(f"Attempt {self.id}: Quiz order {current_quiz_order} already marked as completed for pathway {pathway.id}, student {self.student.id}.")


            # Check if the pathway is now complete
            all_pathway_quiz_orders = set(PathwayQuiz.objects.filter(pathway=pathway).values_list('order', flat=True))
            completed_orders_set = set(progress.completed_orders)

            if all_pathway_quiz_orders == completed_orders_set:
                logger.info(f"Pathway {pathway.id} completed by student {self.student.id} with attempt {self.id}.")
                progress.status = PathwayProgress.ProgressStatus.COMPLETED
                progress.completed_at = timezone.now()

                # --- Logica Punti/Badge per Completamento Percorso ---
                if not progress.first_correct_completion: # Assegna solo la prima volta
                    progress.first_correct_completion = True
                    points_for_pathway = pathway.metadata.get('points_on_completion', 0)
                    if points_for_pathway > 0:
                        try:
                            wallet = Wallet.objects.get(student=self.student)
                            with transaction.atomic():
                                wallet.current_points = F('current_points') + points_for_pathway
                                wallet.save(update_fields=['current_points'])
                                PointTransaction.objects.create(
                                    wallet=wallet,
                                    points_change=points_for_pathway,
                                    reason=f"Completamento Percorso: {pathway.title}"
                                )
                                progress.points_earned = points_for_pathway
                                logger.info(f"Awarded {points_for_pathway} points to student {self.student.id} for completing pathway {pathway.id}.")
                        except Wallet.DoesNotExist:
                             logger.error(f"Wallet not found for student {self.student.id} when trying to award points for pathway {pathway.id}.")
                        except Exception as e_path_points:
                             logger.exception(f"Error awarding points for pathway {pathway.id} completion: {e_path_points}")

                    # --- Logica Badge per Completamento Percorso ---
                    try:
                        pathway_badges = Badge.objects.filter(
                            trigger_type='PATHWAY_COMPLETED', # Usa la stringa diretta
                            is_active=True
                        )
                        for badge in pathway_badges:
                            try:
                                condition = badge.trigger_condition
                                required_pathway_id = condition.get("pathway_id") # Può essere None

                                # Controlla se il badge è per questo percorso specifico (se richiesto)
                                pathway_match = (required_pathway_id is None or required_pathway_id == pathway.id)

                                logger.debug(f"Badge '{badge.name}': ReqPathwayID={required_pathway_id} | CurrentPathwayID={pathway.id} | Match={pathway_match}")

                                if pathway_match:
                                    # Controlla se lo studente ha già questo badge
                                    already_earned = EarnedBadge.objects.filter(student=self.student, badge=badge).exists()
                                    if not already_earned:
                                        logger.info(f"Conditions met for PATHWAY_COMPLETED badge '{badge.name}' (ID {badge.id}).")
                                        earned_badge = EarnedBadge.objects.create(student=self.student, badge=badge) # Cattura istanza creata
                                        newly_earned_pathway_badges.append(earned_badge) # Aggiungi alla lista
                                        logger.info(f"Awarded badge '{badge.name}' to student {self.student.id} for completing pathway {pathway.id}.")
                                    # else:
                                    #    logger.info(f"Studente {self.student.full_name} aveva già il badge '{badge.name}' (PATHWAY_COMPLETED).")

                            except (ValueError, TypeError, KeyError) as e_cond:
                                logger.error(f"Errore nel parsing trigger_condition per Badge PATHWAY_COMPLETED {badge.id} ('{badge.name}'): {condition}. Errore: {e_cond}", exc_info=True)
                            except Exception as e_inner_path_badge:
                                logger.error(f"Errore durante l'assegnazione del Badge PATHWAY_COMPLETED {badge.id} ('{badge.name}') a {self.student.id} per pathway {pathway.id}: {e_inner_path_badge}", exc_info=True)
                    except Exception as e_path_badge:
                        logger.exception(f"Error awarding badge for pathway {pathway.id} completion: {e_path_badge}")

            # Salva le modifiche al progresso (stato, completed_at, points_earned, first_correct_completion, completed_orders, last_completed_quiz_order)
            progress.save()

        return newly_earned_pathway_badges # Restituisci i badge guadagnati in questo aggiornamento


class StudentAnswer(models.Model):
    """ Registra la risposta data da uno Studente a una specifica Domanda in un Tentativo. """
    quiz_attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name='student_answers',
        verbose_name=_('Quiz Attempt')
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE, # Se la domanda viene eliminata, la risposta non ha più senso
        related_name='student_answers',
        verbose_name=_('Question')
    )
    selected_answers = models.JSONField(
        _('Selected Answers'),
        help_text=_('Format depends on question type. E.g., {"answer_option_id": 123} for MC_SINGLE/TF, {"answer_option_ids": [123, 456]} for MC_MULTI, {"answers": ["Paris"]} for FILL_BLANK, {"text": "..."} for OPEN_MANUAL.')
    )
    is_correct = models.BooleanField(
        _('Is Correct?'),
        null=True, # Null if not automatically graded or not graded yet
        blank=True,
        help_text=_('Null for manually graded questions until graded.')
    )
    score = models.FloatField( # Usiamo Float per punteggi parziali o manuali
        _('Score'),
        null=True,
        blank=True,
        help_text=_('Specific score for this answer, especially for manual grading.')
    )
    answered_at = models.DateTimeField(_('Answered At'), auto_now=True) # O auto_now_add=True? auto_now aggiorna ogni volta che si salva

    class Meta:
        verbose_name = _('Student Answer')
        verbose_name_plural = _('Student Answers')
        ordering = ['quiz_attempt', 'question__order']
        unique_together = ('quiz_attempt', 'question') # Solo una risposta per domanda per tentativo

    def __str__(self):
        return f"Answer by {self.quiz_attempt.student.full_name} to Q{self.question.order} in Attempt {self.quiz_attempt.id}"


class PathwayProgress(models.Model):
    """ Traccia il progresso di uno Studente in un Percorso. """
    class ProgressStatus(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='pathway_progresses', # Cambiato related_name in plurale
        verbose_name=_('Student')
    )
    pathway = models.ForeignKey(
        Pathway,
        on_delete=models.CASCADE,
        related_name='progresses', # Cambiato related_name in plurale
        verbose_name=_('Pathway')
    )
    last_completed_quiz_order = models.IntegerField( # Integer per permettere -1 o null
        _('Last Completed Quiz Order'),
        null=True,
        blank=True,
        help_text=_('The order number of the last successfully completed quiz in the pathway.')
    )
    # NUOVO CAMPO: Lista degli ordini dei quiz completati
    completed_orders = models.JSONField(
        _('Completed Quiz Orders'),
        default=list,
        blank=True,
        help_text=_('List of order numbers of successfully completed quizzes in this pathway.')
    )
    started_at = models.DateTimeField(_('Started At'), auto_now_add=True) # Aggiunto auto_now_add
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)
    points_earned = models.IntegerField(_('Points Earned'), null=True, blank=True) # Punti guadagnati per il completamento del percorso
    first_correct_completion = models.BooleanField(_('First Correct Completion'), default=False) # Era il primo completamento?
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=ProgressStatus.choices,
        default=ProgressStatus.IN_PROGRESS
    )

    class Meta:
        verbose_name = _('Pathway Progress')
        verbose_name_plural = _('Pathway Progresses')
        ordering = ['student', '-started_at']
        unique_together = ('student', 'pathway') # Un solo record di progresso per studente per percorso

    def __str__(self):
        return f"Progress of {self.student.full_name} in {self.pathway.title} ({self.status})"

    # Potremmo aggiungere una property per calcolare la percentuale di completamento
    @property
    def completion_percentage(self) -> float:
        total_quizzes = self.pathway.quizzes.count()
        if total_quizzes == 0:
            return 100.0 if self.status == self.ProgressStatus.COMPLETED else 0.0

        completed_count = len(self.completed_orders)
        return round((completed_count / total_quizzes) * 100, 1)


class QuizAssignment(models.Model):
    """ Modello che rappresenta l'assegnazione di un Quiz a uno Studente. """
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name=_('Quiz')
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='quiz_assignments',
        verbose_name=_('Student')
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Mantiene l'assegnazione se chi l'ha assegnato viene eliminato
        null=True,
        related_name='assigned_quizzes',
        limit_choices_to=Q(role=UserRole.TEACHER) | Q(role=UserRole.ADMIN), # Docente o Admin
        verbose_name=_('Assigned By')
    )
    assigned_at = models.DateTimeField(_('Assigned At'), auto_now_add=True)
    due_date = models.DateTimeField(_('Due Date'), null=True, blank=True)
    # Potremmo aggiungere uno stato (es. 'pending', 'completed', 'overdue') se necessario

    class Meta:
        verbose_name = _('Quiz Assignment')
        verbose_name_plural = _('Quiz Assignments')
        ordering = ['student', 'assigned_at']
        unique_together = ('quiz', 'student') # Uno studente può essere assegnato allo stesso quiz una sola volta

    def __str__(self):
        return f"Quiz '{self.quiz.title}' assigned to {self.student.full_name}"

    def clean(self):
        # Validazione opzionale: assicurarsi che assigned_by sia un docente o admin
        if self.assigned_by and self.assigned_by.role not in [UserRole.TEACHER, UserRole.ADMIN]:
            raise ValidationError(_('Only Teachers or Admins can assign quizzes.'))
        # Validazione opzionale: assicurarsi che lo studente appartenga allo stesso docente (se applicabile)
        # if self.assigned_by and self.assigned_by.is_teacher and self.student.teacher != self.assigned_by:
        #     raise ValidationError(_('Teacher can only assign quizzes to their own students.'))


class PathwayAssignment(models.Model):
    """ Modello che rappresenta l'assegnazione di un Percorso a uno Studente. """
    pathway = models.ForeignKey(
        Pathway,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name=_('Pathway')
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='pathway_assignments',
        verbose_name=_('Student')
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_pathways',
        limit_choices_to=Q(role=UserRole.TEACHER) | Q(role=UserRole.ADMIN),
        verbose_name=_('Assigned By')
    )
    assigned_at = models.DateTimeField(_('Assigned At'), auto_now_add=True)
    due_date = models.DateTimeField(_('Due Date'), null=True, blank=True)

    class Meta:
        verbose_name = _('Pathway Assignment')
        verbose_name_plural = _('Pathway Assignments')
        ordering = ['student', 'assigned_at']
        unique_together = ('pathway', 'student')

    def __str__(self):
        return f"Pathway '{self.pathway.title}' assigned to {self.student.full_name}"

    def clean(self):
        if self.assigned_by and self.assigned_by.role not in [UserRole.TEACHER, UserRole.ADMIN]:
            raise ValidationError(_('Only Teachers or Admins can assign pathways.'))
        # if self.assigned_by and self.assigned_by.is_teacher and self.student.teacher != self.assigned_by:
        #     raise ValidationError(_('Teacher can only assign pathways to their own students.'))
