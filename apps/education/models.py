from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

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

class QuizTemplate(models.Model):
    """ Template per un Quiz, creato dall'Admin. """
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # O SET_NULL?
        related_name='created_quiz_templates',
        limit_choices_to={'role': 'ADMIN'}, # Assicura che sia un Admin
        verbose_name=_('Admin Creator')
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

        Returns:
            bool: True if points were successfully awarded (or attempted), False otherwise
                  (e.g., threshold not met, already completed, no points defined, error during transaction).
        """
        # logger.info(f"Attempt {self.id} - Entered assign_completion_points method.") # Rimosso print/log
        quiz = self.quiz
        student = self.student
        threshold = quiz.metadata.get('completion_threshold_percent', 80.0)
        points_to_award = quiz.metadata.get('points_on_completion', 0)
        # logger.info(f"Attempt {self.id} - Checking points: Threshold={threshold}, PointsToAward={points_to_award}, Score={self.score}") # Rimosso print/log

        if self.score is None:
             # print(f"Tentativo {self.id}: Punteggio non ancora calcolato. Nessuna azione sui punti.") # Rimosso print
             return False # Indica che i punti non sono stati assegnati
        if points_to_award <= 0:
            # logger.info(f"Attempt {self.id}: Points not awarded. points_on_completion is {points_to_award}.") # Rimosso print/log
            return False

        is_successful = self.score >= threshold

        if is_successful:
            # print(f"Tentativo {self.id} superato (Punteggio: {self.score} >= Soglia: {threshold}). Controllo assegnazione punti...") # Rimosso print
            # Verifica se è il *primo* tentativo completato con successo per questo quiz/studente
            previous_successful_attempts = QuizAttempt.objects.filter(
                student=student,
                quiz=quiz,
                status=QuizAttempt.AttemptStatus.COMPLETED,
                score__gte=threshold
            ).exclude(pk=self.pk).exists()
            # logger.info(f"Attempt {self.id} - Checking previous success: Exists={previous_successful_attempts}") # Rimosso print/log

            if not previous_successful_attempts:
                # print(f"Questo è il primo completamento con successo per {student.full_name} del quiz '{quiz.title}'. Assegnazione punti...") # Rimosso print
                try:
                    wallet, created = Wallet.objects.get_or_create(student=student)
                    wallet.current_points = F('current_points') + points_to_award
                    wallet.save(update_fields=['current_points'])
                    wallet.refresh_from_db()
                    # logger.info(f"Attempt {self.id}: Awarded {points_to_award} points to student {student.id}. New balance: {wallet.current_points}") # Rimosso print/log
                    PointTransaction.objects.create(wallet=wallet, points_change=points_to_award, reason=f"Completamento Quiz: {quiz.title}")
                    # Aggiorna il campo points_earned sull'attempt - Rimosso, non esiste
                    # self.points_earned = points_to_award
                    # self.save(update_fields=['points_earned']) # Rimosso
                    # Aggiorna il progresso del percorso dopo aver assegnato i punti
                    self.update_pathway_progress()
                    return True # Punti assegnati
                except Exception as e:
                    # logger.exception(f"Attempt {self.id}: Error awarding points to student {student.id}.") # Commentato logger
                    logger.exception(f"Attempt {self.id}: Error awarding points to student {student.id}.") # Ripristinato logger per errori
                    return False # Error during transaction
            else:
                # logger.info(f"Attempt {self.id}: Points not awarded. Previous successful attempt exists.") # Rimosso print/log
                # Still update pathway progress even if points aren't awarded again
                self.update_pathway_progress()
                return False # Not the first success
        else:
            # logger.info(f"Attempt {self.id}: Points not awarded. Score {self.score} did not meet threshold {threshold}.") # Rimosso print/log
            # Update pathway progress even on failure? Maybe not, depends on requirements.
            # Let's assume pathway only progresses on success.
            return False # Threshold not met
# Rimosso blocco duplicato/errato che causava IndentationError

    def update_pathway_progress(self):
        """
        Checks and updates the student's progress in any pathways containing this quiz.

        This method is called after a successful quiz attempt (`assign_completion_points`).
        It operates on the QuizAttempt instance (`self`).

        For each pathway containing this quiz where the student has active progress:
        1. It checks if the current quiz's order matches the *next expected* quiz order
           in the pathway (based on `last_completed_quiz_order`).
        2. If the order is correct, it updates `last_completed_quiz_order` in the
           student's `PathwayProgress` record for that pathway.
        3. If updating `last_completed_quiz_order` results in the last quiz of the
           pathway being completed, it marks the `PathwayProgress` as COMPLETED,
           sets `completed_at`, and checks for pathway completion points.
        4. Pathway points are awarded only on the *first* correct completion of the
           entire pathway, similar to quiz points logic.

        This ensures students progress through pathways sequentially.
        """
        quiz = self.quiz
        student = self.student
        threshold = quiz.metadata.get('completion_threshold_percent', 80.0)

        # Considera solo se il tentativo è stato completato con successo
        if self.status != self.AttemptStatus.COMPLETED or self.score is None or self.score < threshold:
            return

        # Trova i percorsi a cui questo quiz appartiene e per cui lo studente ha un progresso attivo
        pathway_quizzes = PathwayQuiz.objects.filter(quiz=quiz).select_related('pathway')
        active_progresses = PathwayProgress.objects.filter(
            student=student,
            pathway__in=[pq.pathway for pq in pathway_quizzes],
            status=PathwayProgress.ProgressStatus.IN_PROGRESS
        ).select_related('pathway').order_by('pathway_id') # Lock per pathway?

        # print(f"[Attempt {self.id}] Trovati {len(active_progresses)} progressi attivi per quiz {quiz.id} e studente {student.id}") # Rimosso print

        for progress in active_progresses:
            pathway = progress.pathway
            current_quiz_order_in_pathway = PathwayQuiz.objects.get(pathway=pathway, quiz=quiz).order

            # print(f"  - Controllo progresso per Pathway '{pathway.title}' (ID: {pathway.id}). Quiz attuale ordine: {current_quiz_order_in_pathway}. Ultimo completato: {progress.last_completed_quiz_order}") # Rimosso print

            # Aggiorna solo se questo quiz è il *successivo* a quello già completato (o il primo)
            next_expected_order = (progress.last_completed_quiz_order or 0) + 1
            if current_quiz_order_in_pathway == next_expected_order:
                progress.last_completed_quiz_order = current_quiz_order_in_pathway
                # print(f"    -> Aggiornato last_completed_quiz_order a {current_quiz_order_in_pathway}") # Rimosso print

                # Controlla se il percorso è stato completato
                total_quizzes_in_pathway = pathway.quizzes.count()
                if progress.last_completed_quiz_order == total_quizzes_in_pathway:
                    # print(f"    -> Percorso '{pathway.title}' completato!") # Rimosso print
                    progress.status = PathwayProgress.ProgressStatus.COMPLETED
                    progress.completed_at = timezone.now()

                    # Verifica se è il primo completamento corretto del percorso
                    previous_pathway_completions = PathwayProgress.objects.filter(
                        student=student,
                        pathway=pathway,
                        status=PathwayProgress.ProgressStatus.COMPLETED
                    ).exclude(pk=progress.pk).exists()

                    if not previous_pathway_completions:
                        progress.first_correct_completion = True
                        # print(f"    -> Primo completamento corretto del percorso '{pathway.title}'.") # Rimosso print
                        # Assegna punti percorso
                        pathway_points = pathway.metadata.get('points_on_completion', 0)
                        if pathway_points > 0:
                            try:
                                wallet, created = Wallet.objects.get_or_create(student=student)
                                wallet.current_points = F('current_points') + pathway_points
                                wallet.save(update_fields=['current_points'])
                                wallet.refresh_from_db()
                                PointTransaction.objects.create(wallet=wallet, points_change=pathway_points, reason=f"Completamento Percorso: {pathway.title}")
                                # print(f"      -> Assegnati {pathway_points} punti percorso. Nuovo saldo: {wallet.current_points}") # Rimosso print
                                # Aggiorna campo points_earned sul progresso (se esiste e vogliamo usarlo)
                                # progress.points_earned = pathway_points
                            except Exception as e:
                                logger.exception(f"ERRORE durante l'assegnazione dei punti PATHWAY per {pathway.id} a {student.full_name}")
                                # Considerare se propagare l'errore o solo loggarlo. Per ora logga e continua.
                                pass
                        else:
                            # Nessun punto previsto per il completamento di questo percorso.
                            pass
                    else:
                        progress.first_correct_completion = False # Non è il primo
                        # print("    -> Percorso già completato in precedenza. Nessun punto assegnato.") # Rimosso print

                # Salva le modifiche al progresso
                progress.save() # Salva tutti i campi aggiornati
            else:
                # print(f"    -> Quiz completato fuori ordine (atteso: {next_expected_order}). Nessun aggiornamento al progresso.") # Rimosso print
                pass


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
        on_delete=models.CASCADE, # O PROTECT?
        related_name='student_answers',
        verbose_name=_('Question')
    )
    # Memorizza la risposta in formato JSON per flessibilità
    # Es: {'selected_options': [12, 15]} per MC_MULTI
    # Es: {'selected_options': [20]} per MC_SINGLE o TF
    # Es: {'answers': ["cat", "red"]} per FILL_BLANK
    # Es: {'text': "My long answer..."} per OPEN_MANUAL
    selected_answers = models.JSONField(
        _('Selected Answers'),
        default=dict,
        blank=True
    )
    is_correct = models.BooleanField(
        _('Is Correct?'),
        null=True, # Null se in attesa di correzione manuale o non applicabile
        blank=True
    )
    score = models.FloatField( # Punteggio specifico per questa risposta (utile per manuale/ponderato)
        _('Score'),
        null=True,
        blank=True
    )
    answered_at = models.DateTimeField(_('Answered At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Student Answer')
        verbose_name_plural = _('Student Answers')
        ordering = ['quiz_attempt', 'question__order']
        unique_together = ('quiz_attempt', 'question') # Una sola risposta per domanda per tentativo

    def __str__(self):
        return f"Answer by {self.quiz_attempt.student.full_name} to Q{self.question.order} in {self.quiz_attempt}"


# --- INSERIMENTO MODELLO PathwayProgress ---
class PathwayProgress(models.Model):
    """ Traccia il progresso di uno Studente in un Percorso. """
    class ProgressStatus(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='pathway_progresses',
        verbose_name=_('Student')
    )
    pathway = models.ForeignKey(
        Pathway,
        on_delete=models.CASCADE, # O PROTECT?
        related_name='progresses',
        verbose_name=_('Pathway')
    )
    # Potremmo memorizzare l'ultimo quiz completato con successo nel percorso
    last_completed_quiz_order = models.PositiveIntegerField(
        _('Last Completed Quiz Order'),
        null=True,
        blank=True
    )
    started_at = models.DateTimeField(_('Started At'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)
    # points_earned: Non memorizzato qui, ma in PointTransaction
    first_correct_completion = models.BooleanField(
        _('First Correct Completion?'),
        default=False,
        help_text=_('Indicates if this is the first time the student successfully completed the pathway.')
    )
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
        unique_together = ('student', 'pathway') # Uno studente ha un solo progresso per percorso

    def __str__(self):
        return f"Progress of {self.student.full_name} in {self.pathway.title} ({self.status})"
# --- FINE INSERIMENTO MODELLO PathwayProgress ---


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
        settings.AUTH_USER_MODEL, # Il docente che ha assegnato
        on_delete=models.SET_NULL, # Mantiene l'assegnazione se il docente è eliminato
        null=True,
        related_name='assigned_quizzes',
        limit_choices_to={'role': 'TEACHER'},
        verbose_name=_('Assigned By')
    )
    assigned_at = models.DateTimeField(_('Assigned At'), auto_now_add=True)
    due_date = models.DateTimeField(_('Due Date'), null=True, blank=True)
    # Potremmo aggiungere uno stato specifico dell'assegnazione (es. 'not_started', 'completed')
    # se diverso dallo stato dell'ultimo QuizAttempt. Per ora lo omettiamo.

    class Meta:
        verbose_name = _('Quiz Assignment')
        verbose_name_plural = _('Quiz Assignments')
        unique_together = ('quiz', 'student') # Uno studente è assegnato a un quiz una sola volta
        ordering = ['-assigned_at']

    def __str__(self):
        return f"'{self.quiz.title}' assigned to {self.student.full_name}"

    def clean(self):
        # Validazione: Assicura che lo studente appartenga al docente che ha creato il quiz
        if self.quiz.teacher != self.student.teacher:
            raise ValidationError(_("Cannot assign quiz: Student does not belong to the quiz's teacher."))
        # Assicura che chi assegna (se specificato) sia il docente del quiz/studente
        if self.assigned_by and self.assigned_by != self.quiz.teacher:
             raise ValidationError(_("Cannot assign quiz: Assigner must be the quiz's teacher."))


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
        limit_choices_to={'role': 'TEACHER'},
        verbose_name=_('Assigned By')
    )
    assigned_at = models.DateTimeField(_('Assigned At'), auto_now_add=True)
    due_date = models.DateTimeField(_('Due Date'), null=True, blank=True)

    class Meta:
        verbose_name = _('Pathway Assignment')
        verbose_name_plural = _('Pathway Assignments')
        unique_together = ('pathway', 'student')
        ordering = ['-assigned_at']

    def __str__(self):
        return f"'{self.pathway.title}' assigned to {self.student.full_name}"

    def clean(self):
        if self.pathway.teacher != self.student.teacher:
            raise ValidationError(_("Cannot assign pathway: Student does not belong to the pathway's teacher."))
        if self.assigned_by and self.assigned_by != self.pathway.teacher:
             raise ValidationError(_("Cannot assign pathway: Assigner must be the pathway's teacher."))
