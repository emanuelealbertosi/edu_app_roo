from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

# Import Student model safely using AUTH_USER_MODEL setting's app label
# This avoids circular imports if rewards models were needed in users app later.
# However, Student is not the AUTH_USER_MODEL, so we import it directly.
# Ensure 'apps.users' is loaded before 'apps.rewards' if there are complex dependencies.
from apps.users.models import Student


class Wallet(models.Model):
    """
    Portafoglio punti per ogni Studente.
    """
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE, # Se lo studente è eliminato, elimina anche il portafoglio
        related_name='wallet',
        primary_key=True, # Usiamo lo student_id come chiave primaria per semplicità
        verbose_name=_('Student')
    )
    current_points = models.PositiveIntegerField(
        _('Current Points'),
        default=0,
        help_text=_('Punti attualmente disponibili per lo studente.')
    )

    class Meta:
        verbose_name = _('Wallet')
        verbose_name_plural = _('Wallets')

    def __str__(self):
        return f"Wallet for {self.student.full_name} ({self.current_points} points)"

    def add_points(self, points_to_add, reason):
        """
        Adds points to the wallet and creates a transaction record.

        Args:
            points_to_add (int): The number of points to add (must be positive).
            reason (str): The reason for the point addition.
        """
        if points_to_add <= 0:
            # Consider raising ValueError for consistency? For now, just return.
            return
        # Use F() expression for atomic update
        self.current_points = models.F('current_points') + points_to_add
        self.save(update_fields=['current_points'])
        self.refresh_from_db() # Reload the value after atomic update

        # Create transaction *after* successful update
        PointTransaction.objects.create(
            wallet=self,
            points_change=points_to_add,
            reason=reason
        )

    def subtract_points(self, points_to_subtract, reason):
        """
        Subtracts points from the wallet and creates a transaction record.

        Args:
            points_to_subtract (int): The number of points to subtract (must be positive).
            reason (str): The reason for the point subtraction.

        Raises:
            ValueError: If points_to_subtract is not positive or if insufficient points.
        """
        if points_to_subtract <= 0:
            raise ValueError("Points to subtract must be positive.")
        if self.current_points < points_to_subtract:
            raise ValueError("Insufficient points.")
        # Use F() expression for atomic update
        self.current_points = models.F('current_points') - points_to_subtract
        self.save(update_fields=['current_points'])
        self.refresh_from_db() # Reload the value after atomic update

        # Create transaction *after* successful update
        PointTransaction.objects.create(
            wallet=self,
            points_change=-points_to_subtract, # Negativo per sottrazione
            reason=reason
        )


class PointTransaction(models.Model):
    """
    Registra ogni modifica ai punti nel Wallet di uno Studente.
    """
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE, # Se il wallet è eliminato, elimina le transazioni
        related_name='transactions',
        verbose_name=_('Wallet')
    )
    points_change = models.IntegerField(
        _('Points Change'),
        help_text=_('Numero di punti aggiunti (positivo) o rimossi (negativo).')
    )
    reason = models.CharField(
        _('Reason'),
        max_length=255,
        help_text=_('Motivo della transazione (es. Completamento Quiz X, Acquisto Ricompensa Y).')
    )
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)

    class Meta:
        verbose_name = _('Point Transaction')
        verbose_name_plural = _('Point Transactions')
        ordering = ['-timestamp'] # Mostra le più recenti prima

    def __str__(self):
        change_type = "Added" if self.points_change > 0 else "Subtracted"
        return f"{change_type} {abs(self.points_change)} points for {self.wallet.student.full_name} at {self.timestamp}"


class RewardTemplate(models.Model):
    """
    Template per le ricompense, creato da Admin (global) o Docente (local).
    """
    class RewardScope(models.TextChoices):
        GLOBAL = 'GLOBAL', _('Global')
        LOCAL = 'LOCAL', _('Local')

    class RewardType(models.TextChoices):
        DIGITAL = 'DIGITAL', _('Digital')
        REAL_WORLD = 'REAL_WORLD', _('Real World Tracked')

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Usa l'impostazione per flessibilità
        on_delete=models.CASCADE, # O SET_NULL se vogliamo mantenere i template anche se l'utente è eliminato
        related_name='created_reward_templates',
        verbose_name=_('Creator')
    )
    scope = models.CharField(
        _('Scope'),
        max_length=10,
        choices=RewardScope.choices,
        help_text=_('Global (Admin) or Local (Teacher)')
    )
    name = models.CharField(_('Name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    type = models.CharField(
        _('Type'),
        max_length=20,
        choices=RewardType.choices,
        default=RewardType.DIGITAL
    )
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Extra data like image URL, link, etc. Example: {"image_url": "http://example.com/img.png", "external_link": "http://info.example.com"}')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Reward Template')
        verbose_name_plural = _('Reward Templates')
        ordering = ['name']

    def __str__(self):
        scope_display = self.get_scope_display()
        return f"{self.name} ({scope_display})"


class Reward(models.Model):
    """
    Ricompensa specifica creata da un Docente, potenzialmente basata su un Template.
    """
    class AvailabilityType(models.TextChoices):
        ALL_STUDENTS = 'ALL', _('All Students of Teacher')
        SPECIFIC_STUDENTS = 'SPECIFIC', _('Specific Students')

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_rewards',
        limit_choices_to={'role': 'TEACHER'}, # Assicura che sia un Docente
        verbose_name=_('Teacher')
    )
    template = models.ForeignKey(
        RewardTemplate,
        on_delete=models.SET_NULL, # Mantiene la ricompensa se il template è eliminato
        null=True,
        blank=True,
        related_name='rewards_from_template',
        verbose_name=_('Source Template')
    )
    name = models.CharField(_('Name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    type = models.CharField(
        _('Type'),
        max_length=20,
        choices=RewardTemplate.RewardType.choices, # Usa le stesse scelte del template
        default=RewardTemplate.RewardType.DIGITAL
    )
    cost_points = models.PositiveIntegerField(_('Cost (Points)'))
    availability_type = models.CharField(
        _('Availability'),
        max_length=10,
        choices=AvailabilityType.choices,
        default=AvailabilityType.ALL_STUDENTS
    )
    # Relazione M2M per disponibilità specifica, definita tramite through model implicito o esplicito
    available_to_specific_students = models.ManyToManyField(
        Student,
        through='RewardStudentSpecificAvailability', # Specifica il modello intermedio
        blank=True, # Permette di non avere studenti specifici se availability_type è ALL
        verbose_name=_('Specifically Available To')
    )
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
        help_text=_('Extra data like image URL, link, etc. Inherited/overridden from template. Example: {"image_url": "http://example.com/reward.jpg"}')
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Is this reward currently available for purchase?')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Reward')
        verbose_name_plural = _('Rewards')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.cost_points} points)"


class RewardStudentSpecificAvailability(models.Model):
    """
    Modello intermedio per la relazione M2M tra Reward e Student
    quando availability_type è 'SPECIFIC'.
    """
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True) # Opzionale: quando è stata resa disponibile

    class Meta:
        verbose_name = _('Reward Specific Availability')
        verbose_name_plural = _('Reward Specific Availabilities')
        unique_together = ('reward', 'student') # Assicura che una coppia sia unica
        ordering = ['assigned_at']


class RewardPurchase(models.Model):
    """
    Registra l'acquisto di una Ricompensa da parte di uno Studente.
    """
    class PurchaseStatus(models.TextChoices):
        PURCHASED = 'PURCHASED', _('Purchased')
        DELIVERED = 'DELIVERED', _('Delivered')
        CANCELLED = 'CANCELLED', _('Cancelled') # Es. se la ricompensa non è più disponibile

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE, # O SET_NULL/PROTECT se vogliamo mantenere lo storico acquisti
        related_name='purchases',
        verbose_name=_('Student')
    )
    reward = models.ForeignKey(
        Reward,
        on_delete=models.PROTECT, # Impedisce l'eliminazione di una ricompensa se è stata acquistata
        related_name='purchases',
        verbose_name=_('Reward')
    )
    points_spent = models.PositiveIntegerField(_('Points Spent'))
    purchased_at = models.DateTimeField(_('Purchased At'), auto_now_add=True)
    status = models.CharField(
        _('Status'),
        max_length=10,
        choices=PurchaseStatus.choices,
        default=PurchaseStatus.PURCHASED
    )
    # Campi per tracciare la consegna (per tipo REAL_WORLD)
    delivered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivered_rewards',
        limit_choices_to={'role': 'TEACHER'}, # O anche Admin? Per ora solo Docente
        verbose_name=_('Delivered By')
    )
    delivered_at = models.DateTimeField(_('Delivered At'), null=True, blank=True)
    delivery_notes = models.TextField(_('Delivery Notes'), blank=True)

    class Meta:
        verbose_name = _('Reward Purchase')
        verbose_name_plural = _('Reward Purchases')
        ordering = ['-purchased_at']

    def __str__(self):
        return f"{self.student.full_name} purchased {self.reward.name} at {self.purchased_at}"


# --- Modelli per Gamification (Badge) ---

class Badge(models.Model):
    """
    Definizione di un badge/traguardo che gli studenti possono ottenere.
    """
    class TriggerType(models.TextChoices):
        QUIZ_COMPLETED = 'QUIZ_COMPLETED', _('Quiz Completed')
        PATHWAY_COMPLETED = 'PATHWAY_COMPLETED', _('Pathway Completed')
        CORRECT_STREAK = 'CORRECT_STREAK', _('Correct Answer Streak')
        POINTS_THRESHOLD = 'POINTS_THRESHOLD', _('Points Threshold Reached')
        # Aggiungere altri trigger se necessario

    name = models.CharField(_('Badge Name'), max_length=100, unique=True)
    description = models.TextField(_('Description'), help_text=_('Spiega come ottenere questo badge.'))
    # Cambiato da URLField a ImageField per permettere l'upload
    image = models.ImageField(
        _('Image'),
        upload_to='badges/', # Salva le immagini in MEDIA_ROOT/badges/
        blank=True,
        null=True,
        help_text=_('Immagine del badge (verrà caricata).')
    )
    trigger_type = models.CharField(
        _('Trigger Type'),
        max_length=30,
        choices=TriggerType.choices,
        help_text=_('L\'evento che può sbloccare questo badge.')
    )
    # Condizioni specifiche basate sul trigger_type (JSON per flessibilità)
    trigger_condition = models.JSONField(
        _('Trigger Condition'),
        default=dict,
        blank=True,
        help_text=_(
            'Condizioni specifiche in formato JSON. Esempi:\n'
            '- Per QUIZ_COMPLETED: {"quiz_id": 123, "min_score_percent": 80} (quiz_id opzionale, si applica a qualsiasi quiz se omesso)\n'
            '- Per PATHWAY_COMPLETED: {"pathway_id": 45} (pathway_id opzionale)\n'
            '- Per CORRECT_STREAK: {"streak_length": 10}\n'
            '- Per POINTS_THRESHOLD: {"points": 500}'
        )
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Se il badge può essere attualmente ottenuto.')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Badge')
        verbose_name_plural = _('Badges')
        ordering = ['name']

    def __str__(self):
        return self.name


class EarnedBadge(models.Model):
    """
    Registra quando uno Studente ha ottenuto un Badge specifico.
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='earned_badges',
        verbose_name=_('Student')
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE, # Se il badge viene eliminato, rimuovi anche le occorrenze guadagnate
        related_name='earned_by_students',
        verbose_name=_('Badge')
    )
    earned_at = models.DateTimeField(_('Earned At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Earned Badge')
        verbose_name_plural = _('Earned Badges')
        # Assicura che uno studente possa guadagnare lo stesso badge una sola volta
        unique_together = ('student', 'badge')
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.student.full_name} earned {self.badge.name} at {self.earned_at}"

