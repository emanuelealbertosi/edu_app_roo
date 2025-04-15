import uuid
from datetime import timedelta
from django.utils import timezone
from django.conf import settings # Per accedere a eventuali settings custom
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password, check_password # Add imports

class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', _('Admin')
    TEACHER = 'TEACHER', _('Teacher')
    # Nota: Studente è un modello separato

class User(AbstractUser):
    """
    Modello Utente personalizzato che rappresenta Admin e Docenti.
    Gli Studenti sono rappresentati da un modello separato (Student).
    """
    # Campi come username, first_name, last_name, email, is_staff, is_active, date_joined
    # sono ereditati da AbstractUser.

    role = models.CharField(
        _('Role'),
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.TEACHER, # Default a Docente, Admin richiede impostazione esplicita
        help_text=_('Ruolo utente nel sistema (Admin o Docente).')
    )

    # Aggiungiamo related_name per evitare conflitti con i campi groups e user_permissions
    # del modello User predefinito quando si usa AUTH_USER_MODEL.
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'I gruppi a cui appartiene questo utente. Un utente otterrà tutti i permessi '
            'concessi a ciascuno dei suoi gruppi.'
        ),
        related_name="custom_user_set", # related_name personalizzato
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Permessi specifici per questo utente.'),
        related_name="custom_user_set", # related_name personalizzato
        related_query_name="user",
    )

    def __str__(self):
        return self.username

    # Proprietà per un controllo più semplice del ruolo
    @property
    def is_admin(self):
        """ Returns True if the user has the ADMIN role. """
        return self.role == UserRole.ADMIN

    @property
    def is_teacher(self):
        """ Returns True if the user has the TEACHER role. """
        return self.role == UserRole.TEACHER


class StudentGroup(models.Model):
    """
    Modello che rappresenta un gruppo di studenti gestito da un docente.
    Gli studenti appartengono a un gruppo tramite il campo ForeignKey 'group' nel modello Student.
    """
    name = models.CharField(_('Group Name'), max_length=100)
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE, # Se il docente viene eliminato, elimina anche i gruppi associati
        related_name='student_groups',
        limit_choices_to={'role': UserRole.TEACHER}, # Assicura che si possa collegare solo a Docenti
        verbose_name=_('Teacher')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Student Group')
        verbose_name_plural = _('Student Groups')
        unique_together = ('name', 'teacher') # Un docente non può avere due gruppi con lo stesso nome
        ordering = ['teacher', 'name']

    def __str__(self):
        return f"{self.name} ({self.teacher.username})"


class Student(models.Model):
    """
    Modello che rappresenta uno Studente.
    Collegato a un Docente (User con role=TEACHER) e opzionalmente a un Gruppo.
    """
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='students',
        limit_choices_to={'role': UserRole.TEACHER},
        verbose_name=_('Teacher')
    )
    student_code = models.CharField(
        _('Student Code'),
        max_length=50,
        unique=True,
        help_text=_('Codice univoco identificativo dello studente (es. matricola).')
    )
    pin_hash = models.CharField(
        _('PIN Hash'),
        max_length=128,
        help_text=_('Hash del PIN numerico per l\'accesso studente.')
    )
    first_name = models.CharField(_('First Name'), max_length=150)
    last_name = models.CharField(_('Last Name'), max_length=150)
    group = models.ForeignKey(
        StudentGroup,
        on_delete=models.SET_NULL, # Se il gruppo viene eliminato, lo studente perde l'associazione
        related_name='members', # Nome relazione inversa da Gruppo a Studente (membri)
        null=True,
        blank=True,
        verbose_name=_('Group')
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Designates whether this student should be treated as active. Unselect this instead of deleting accounts.')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)

    class Meta:
        verbose_name = _('Student')
        verbose_name_plural = _('Students')
        ordering = ['last_name', 'first_name'] # Ordine predefinito

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        """ Returns the student's full name. """
        return f"{self.first_name} {self.last_name}"

    @property
    def is_authenticated(self):
        """
        Property to satisfy Django REST Framework's IsAuthenticated permission check
        when the user object is an instance of Student.
        """
        return True

    def set_pin(self, raw_pin):
        """
        Sets the student's PIN hash from a raw PIN string.

        Args:
            raw_pin (str): The raw PIN string to hash.

        Raises:
            ValueError: If the PIN is not numeric or doesn't meet length requirements.
        """
        if not raw_pin or not raw_pin.isdigit():
             raise ValueError("Il PIN deve essere numerico.")
        # Usa la lunghezza definita nelle settings o un default
        min_pin_length = getattr(settings, 'STUDENT_PIN_MIN_LENGTH', 4)
        if len(raw_pin) < min_pin_length:
             raise ValueError(f"Il PIN deve essere di almeno {min_pin_length} cifre.")
        self.pin_hash = make_password(raw_pin)

    def check_pin(self, raw_pin):
        """
        Checks if the provided raw PIN matches the stored hash.

        Args:
            raw_pin (str): The raw PIN string to check.

        Returns:
            bool: True if the PIN matches, False otherwise.
        """
        return check_password(raw_pin, self.pin_hash)


class StudentRegistrationToken(models.Model):
    """
    Token temporaneo per permettere l'auto-registrazione degli studenti.
    """
    token = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='registration_tokens',
        limit_choices_to={'role': UserRole.TEACHER},
        verbose_name=_('Teacher')
    )
    group = models.ForeignKey(
        StudentGroup,
        on_delete=models.CASCADE, # Se il gruppo viene eliminato, il token non è più valido per quel gruppo
        related_name='registration_tokens',
        null=True,
        blank=True, # Permette token non legati a un gruppo specifico (assegnati solo al docente)
        verbose_name=_('Group (Optional)')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    expires_at = models.DateTimeField(_('Expires At'))
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Indica se il token può essere ancora utilizzato.')
    )

    class Meta:
        verbose_name = _('Student Registration Token')
        verbose_name_plural = _('Student Registration Tokens')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Imposta scadenza default (es. 24 ore) se non specificata
            validity_duration = getattr(settings, 'STUDENT_REGISTRATION_TOKEN_VALIDITY', timedelta(hours=24))
            self.expires_at = timezone.now() + validity_duration
        super().save(*args, **kwargs)

    def is_valid(self):
        """ Controlla se il token è attivo e non scaduto. """
        return self.is_active and self.expires_at > timezone.now()

    def __str__(self):
        group_name = f" ({self.group.name})" if self.group else ""
        return f"Token for {self.teacher.username}{group_name} - Expires: {self.expires_at.strftime('%Y-%m-%d %H:%M')}"
