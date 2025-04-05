from django.conf import settings
from django.db import models, transaction # Import transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Max as AggregateMax # Rinomina Max per evitare conflitti

# Import Student model
from apps.users.models import Student
from django.utils import timezone # Import timezone
from django.db.models import F # Import F for atomic updates
# Import Wallet and PointTransaction later to avoid circular dependency if needed,
# or ensure they are defined before QuizAttempt if in the same file.
# Let's import them here for clarity for now.
from apps.rewards.models import Wallet, PointTransaction
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
    # points_earned: Calcolato al momento del completamento se le condizioni sono soddisfatte
    # first_correct_completion: Calcolato al momento del completamento
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

        correct_answers_count = 0
        manual_score_total = 0
        manual_questions_graded = 0
        correct_manual_answers_count = 0 # Aggiunto contatore

        # Itera sulle risposte dello studente recuperate dal DB
        for student_answer in student_answers:
            question = student_answer.question
            question_id = question.id
            question_type = question.question_type
            selected_data = student_answer.selected_answers

            if question_type == QuestionType.OPEN_ANSWER_MANUAL:
                if student_answer.score is not None: # Considera solo se gradata
                    manual_score_total += student_answer.score
                    manual_questions_graded += 1
                    if student_answer.is_correct: # Aggiunto controllo
                        correct_manual_answers_count += 1
                continue # Salta il controllo automatico

            # Logica correzione automatica
            is_correct = False
            try:
                if question_type in [QuestionType.MULTIPLE_CHOICE_SINGLE, QuestionType.TRUE_FALSE]:
                    selected_option_id_raw = selected_data.get('answer_option_id') if isinstance(selected_data, dict) else None
                    expected_correct_id = correct_options_map.get(question_id)

                    # Tentativo di conversione a intero e confronto
                    selected_option_id = None
                    try:
                        if selected_option_id_raw is not None:
                            selected_option_id = int(selected_option_id_raw)
                    except (ValueError, TypeError):
                        logger.warning(f"Attempt {self.id} - Q {question_id}: Could not convert selected_option_id '{selected_option_id_raw}' to int.") # Manteniamo questo warning

                    if expected_correct_id is not None and selected_option_id == expected_correct_id: # Rimosso log da qui
                        is_correct = True
                elif question_type == QuestionType.MULTIPLE_CHOICE_MULTIPLE:
                    # Corretto per usare answer_option_ids
                    selected_option_ids = set(selected_data.get('answer_option_ids', [])) if isinstance(selected_data, dict) else set()
                    expected_correct_set = correct_options_map.get(question_id, set()) # Get the set or an empty set
                    print(f"--- Attempt {self.id}: Evaluating Q {question_id} (MC_MULTI): Selected Set={selected_option_ids}, Expected Set={expected_correct_set} ---") # DEBUG PRINT
                    if question_id in correct_options_map and selected_option_ids == expected_correct_set:
                        is_correct = True
                elif question_type == QuestionType.FILL_BLANK:
                    user_answer = selected_data.get('answer_text', '').strip().lower() if isinstance(selected_data, dict) else ''
                    if question_id in fill_blank_answers_map and user_answer in fill_blank_answers_map[question_id]:
                        is_correct = True
            except Exception as e:
                logger.exception(f"Errore durante la valutazione della risposta per domanda {question_id} nel tentativo {self.id}")
                # Consideriamo la risposta come errata in caso di eccezione? Per ora sì.
                is_correct = False # Assicurati che is_correct sia False

            if is_correct:
                correct_answers_count += 1
            # Aggiorna is_correct sulla risposta se è cambiato
            if student_answer.is_correct != is_correct:
                 student_answer.is_correct = is_correct
                 student_answer.save(update_fields=['is_correct']) # Salva l'esito della singola risposta

        # Calcola punteggio finale
        # Calcolo del punteggio finale:
        # - Se ci sono domande a correzione automatica, il punteggio è la percentuale
        #   di risposte corrette *solo* tra quelle automatiche. Il punteggio manuale
        #   viene ignorato in questo calcolo percentuale finale.
        # - Se ci sono *solo* domande manuali e sono state tutte gradate,
        #   il punteggio è la percentuale di risposte manuali corrette.
        # - Altrimenti (es. solo domande manuali non ancora gradate), il punteggio è 0.
        final_score = 0
        if total_autograded_questions > 0:
            # Caso 1: Ci sono domande auto-gradate. Il punteggio si basa solo su queste.
            final_score = (correct_answers_count / total_autograded_questions) * 100
        elif manual_questions_graded > 0:
             # Caso 2: Ci sono SOLO domande manuali e sono state gradate.
             final_score = (correct_manual_answers_count / manual_questions_graded) * 100 # Calcola percentuale
        # else: final_score rimane 0

        final_score = round(final_score, 2)
        # print(f"Calcolato punteggio finale per tentativo {self.id}: {final_score}") # Rimosso print
        return final_score

    def assign_completion_points(self):
        """
        Checks if the attempt meets the completion threshold and assigns points if applicable.

        This method operates on the QuizAttempt instance (`self`).
        It reads 'completion_threshold_percent' and 'points_on_completion' from the Quiz metadata.
        Points are awarded only if:
        1. The attempt's score meets or exceeds the threshold.
        2. 'points_on_completion' is greater than 0.
        3. This is the *first* successful completion of this specific quiz by this student
           (checked by querying previous successful attempts).

        If points are awarded, it atomically updates the student's Wallet balance
        and creates a PointTransaction record.

        It also triggers `update_pathway_progress` regardless of whether points were awarded for the quiz itself,
        to ensure pathway progression is checked upon successful quiz completion.
        """
        # Ensure score is calculated and saved before checking threshold
        if self.score is None:
             self.score = self.calculate_final_score() # Calculate if not already done
             # self.save(update_fields=['score']) # Save score? calculate_final_score might not save. Let's assume it does for now or is saved before calling this.

        # Default threshold to 100% if not specified
        completion_threshold = float(self.quiz.metadata.get('completion_threshold_percent', 100.0))
        points_to_award = int(self.quiz.metadata.get('points_on_completion', 0))

        logger.debug(f"Attempt {self.id}: Score={self.score}, Threshold={completion_threshold}, Points={points_to_award}")

        passed = self.score is not None and self.score >= completion_threshold

        # Update attempt status based on pass/fail
        if passed:
            self.status = self.AttemptStatus.COMPLETED
        else:
            self.status = self.AttemptStatus.FAILED
        # Save the status change immediately
        self.save(update_fields=['status', 'score']) # Ensure score is saved too

        # Check if this is the first *successful* completion
        is_first_successful = False
        if passed:
            # Check if there are any *previous* attempts for this quiz by this student that were COMPLETED
            previous_successful_attempts_exist = QuizAttempt.objects.filter(
                quiz=self.quiz,
                student=self.student,
                status=self.AttemptStatus.COMPLETED
            ).exclude(pk=self.pk).exists() # Exclude the current attempt

            if not previous_successful_attempts_exist:
                is_first_successful = True
                logger.info(f"Attempt {self.id} is the first successful completion for quiz {self.quiz.id} by student {self.student.id}.")


        # Award points only on the first successful completion and if points > 0
        if is_first_successful and points_to_award > 0:
            try:
                wallet = Wallet.objects.get(student=self.student)
                # Use atomic transaction for updating wallet and creating transaction
                with transaction.atomic():
                    # Use F() expression for atomic update
                    wallet.current_points = F('current_points') + points_to_award
                    wallet.save(update_fields=['current_points'])
                    # Refresh wallet from DB to get the updated value if needed later in this request
                    # wallet.refresh_from_db()

                    PointTransaction.objects.create(
                        wallet=wallet,
                        points_change=points_to_award,
                        reason=f"Completamento Quiz: {self.quiz.title}"
                    )
                    logger.info(f"Awarded {points_to_award} points to student {self.student.id} for completing quiz {self.quiz.id}. New balance: {wallet.current_points}") # Note: wallet.current_points might be F() object here
            except Wallet.DoesNotExist:
                logger.error(f"Wallet not found for student {self.student.id} when trying to award points for quiz {self.quiz.id}.")
            except Exception as e:
                logger.exception(f"Error awarding points for quiz attempt {self.id}: {e}")

        # --- Trigger Pathway Progress Update ---
        # This should happen if the quiz was passed, regardless of points awarded
        if passed:
             self.update_pathway_progress() # Call the method to update pathway progress


    def update_pathway_progress(self):
        """
        Updates the PathwayProgress if this quiz is part of a pathway and was successfully completed.
        Uses the new `completed_orders` field.
        Checks if the pathway itself is now complete and assigns pathway points if applicable.
        """
        logger.debug(f"Attempt {self.id}: Checking pathway progress update for quiz {self.quiz.id}.")
        # Check if the attempt was successful (status is COMPLETED)
        if self.status != self.AttemptStatus.COMPLETED:
            logger.debug(f"Attempt {self.id}: Quiz not passed (status={self.status}), skipping pathway update.")
            return

        # Find if this quiz is part of any pathways assigned to the student
        assigned_pathways = Pathway.objects.filter(
            assignments__student=self.student, # Check assignments for this student
            pathwayquiz__quiz=self.quiz # Check if the pathway contains this quiz
        ).distinct().prefetch_related('pathwayquiz_set') # Prefetch related quizzes for efficiency

        if not assigned_pathways.exists():
            logger.debug(f"Attempt {self.id}: Quiz {self.quiz.id} is not part of any assigned pathway for student {self.student.id}.")
            return

        for pathway in assigned_pathways:
            logger.info(f"Attempt {self.id}: Updating progress for pathway {pathway.id} for student {self.student.id}.")
            try:
                # Get or create the progress record for this student and pathway
                progress, created = PathwayProgress.objects.get_or_create(
                    student=self.student,
                    pathway=pathway,
                    defaults={'status': PathwayProgress.ProgressStatus.IN_PROGRESS, 'completed_orders': []} # Ensure completed_orders is initialized
                )

                # Find the order of the completed quiz within this specific pathway
                try:
                    pathway_quiz_entry = pathway.pathwayquiz_set.get(quiz=self.quiz)
                    completed_quiz_order = pathway_quiz_entry.order
                except PathwayQuiz.DoesNotExist:
                    logger.error(f"Consistency error: Quiz {self.quiz.id} completed in attempt {self.id} but not found in PathwayQuiz for pathway {pathway.id}.")
                    continue # Skip this pathway if the quiz isn't actually part of it

                # Ensure completed_orders is a list (handle potential null/incorrect type from DB if default wasn't set properly)
                if not isinstance(progress.completed_orders, list):
                    progress.completed_orders = []

                # Add the completed order to the list if not already present
                if completed_quiz_order not in progress.completed_orders:
                    progress.completed_orders.append(completed_quiz_order)
                    progress.completed_orders.sort() # Keep the list sorted
                    logger.debug(f"Pathway {pathway.id} Progress for student {self.student.id}: Added order {completed_quiz_order} to completed_orders. New list: {progress.completed_orders}")
                else:
                    logger.debug(f"Pathway {pathway.id} Progress for student {self.student.id}: Order {completed_quiz_order} already in completed_orders.")

                # Update last_completed_quiz_order with the maximum completed order
                progress.last_completed_quiz_order = max(progress.completed_orders) if progress.completed_orders else None

                # Check if the entire pathway is now complete
                all_pathway_quiz_orders = set(pathway.pathwayquiz_set.values_list('order', flat=True))
                completed_orders_set = set(progress.completed_orders)

                is_pathway_complete = all_pathway_quiz_orders.issubset(completed_orders_set)

                if is_pathway_complete and progress.status != PathwayProgress.ProgressStatus.COMPLETED:
                    progress.status = PathwayProgress.ProgressStatus.COMPLETED
                    progress.completed_at = timezone.now()
                    logger.info(f"Pathway {pathway.id} completed by student {self.student.id}.")

                    # --- Assign Pathway Completion Points ---
                    pathway_points = int(pathway.metadata.get('points_on_completion', 0))
                    # Check if this is the first completion of the *pathway*
                    previous_pathway_completions_exist = PathwayProgress.objects.filter(
                        pathway=pathway,
                        student=self.student,
                        status=PathwayProgress.ProgressStatus.COMPLETED
                    ).exclude(pk=progress.pk).exists()

                    if not previous_pathway_completions_exist and pathway_points > 0:
                        progress.first_correct_completion = True # Mark first completion
                        try:
                            wallet = Wallet.objects.get(student=self.student)
                            with transaction.atomic():
                                wallet.current_points = F('current_points') + pathway_points
                                wallet.save(update_fields=['current_points'])
                                PointTransaction.objects.create(
                                    wallet=wallet,
                                    points_change=pathway_points,
                                    reason=f"Completamento Percorso: {pathway.title}"
                                )
                                progress.points_earned = pathway_points # Record points earned for the pathway
                                logger.info(f"Awarded {pathway_points} points to student {self.student.id} for completing pathway {pathway.id}.")
                        except Wallet.DoesNotExist:
                            logger.error(f"Wallet not found for student {self.student.id} when trying to award points for pathway {pathway.id}.")
                        except Exception as e:
                            logger.exception(f"Error awarding points for pathway completion {progress.id}: {e}")
                    else:
                         logger.info(f"Pathway {pathway.id} already completed previously or has 0 points. No points awarded.")
                         # Ensure points_earned is null if no points were awarded this time
                         progress.points_earned = None


                # Save the progress changes (status, completed_at, last_completed_quiz_order, completed_orders, points_earned, first_correct_completion)
                progress.save()

            except Exception as e:
                logger.exception(f"Error updating pathway progress for pathway {pathway.id}, student {self.student.id}, attempt {self.id}: {e}")


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


# --- Assignment Models ---

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
        on_delete=models.SET_NULL, # Se l'assegnatore viene eliminato, manteniamo l'assegnazione
        null=True,
        related_name='assigned_quizzes',
        limit_choices_to={'role__in': ['TEACHER', 'ADMIN']}, # Docente o Admin
        verbose_name=_('Assigned By')
    )
    assigned_at = models.DateTimeField(_('Assigned At'), auto_now_add=True)
    due_date = models.DateTimeField(_('Due Date'), null=True, blank=True, help_text=_('Optional deadline for the quiz assignment.'))

    class Meta:
        verbose_name = _('Quiz Assignment')
        verbose_name_plural = _('Quiz Assignments')
        ordering = ['-assigned_at']
        unique_together = ('quiz', 'student') # Un quiz può essere assegnato una sola volta a uno studente

    def __str__(self):
        return f"Quiz '{self.quiz.title}' assigned to {self.student.full_name}"

    def clean(self):
        # Validazione: Assicura che lo studente appartenga al docente che ha creato il quiz
        # (o che l'assegnatore sia un admin)
        if self.assigned_by and self.assigned_by.role == 'TEACHER':
            if self.quiz.teacher != self.assigned_by:
                 raise ValidationError(_("A teacher can only assign their own quizzes."))
            if self.student.teacher != self.assigned_by:
                 raise ValidationError(_("A teacher can only assign quizzes to their own students."))
        # Se assigned_by è Admin, permettiamo l'assegnazione (assumendo che l'admin possa gestire tutto)
        # Se assigned_by è NULL (es. cancellato), non possiamo validare


class PathwayAssignment(models.Model):
    """ Modello che rappresenta l'assegnazione di un Percorso a uno Studente. """
    pathway = models.ForeignKey(
        Pathway,
        on_delete=models.CASCADE,
        null=True, # Permetti NULL a livello di DB
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
        limit_choices_to={'role__in': ['TEACHER', 'ADMIN']},
        verbose_name=_('Assigned By')
    )
    assigned_at = models.DateTimeField(_('Assigned At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Pathway Assignment')
        verbose_name_plural = _('Pathway Assignments')
        ordering = ['-assigned_at']
        unique_together = ('pathway', 'student')

    def __str__(self):
        return f"Pathway '{self.pathway.title}' assigned to {self.student.full_name}"

    def clean(self):
        # Validazione simile a QuizAssignment
        if self.assigned_by and self.assigned_by.role == 'TEACHER':
            if self.pathway.teacher != self.assigned_by:
                 raise ValidationError(_("A teacher can only assign their own pathways."))
            if self.student.teacher != self.assigned_by:
                 raise ValidationError(_("A teacher can only assign pathways to their own students."))
