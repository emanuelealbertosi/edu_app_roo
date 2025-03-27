from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

# Import Student model
from apps.users.models import Student

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
        help_text=_('Extra data like difficulty, subject, etc.')
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
        help_text=_('Specific config based on type, e.g., correct answers for fill_blank, points.')
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
    description = models.TextField(_('Description'), blank=True)
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('E.g., difficulty, subject, completion_threshold (0-1), points_on_completion')
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
        help_text=_('Specific config based on type, e.g., correct answers for fill_blank, points.')
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
        help_text=_('E.g., points_on_completion')
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
        COMPLETED = 'COMPLETED', _('Completed')

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
    # points_earned: Calcolato al completamento se le condizioni sono soddisfatte
    # first_correct_completion: Calcolato al completamento
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
