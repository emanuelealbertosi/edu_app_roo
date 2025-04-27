from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password, check_password # Add imports
import uuid
from django.utils import timezone
from datetime import timedelta
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


class Student(models.Model):
    """
    Modello che rappresenta uno Studente.
    Collegato a un Docente (User con role=TEACHER).
    """
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE, # Se il docente viene eliminato, elimina anche gli studenti associati? O SET_NULL? O PROTECT? Decidiamo CASCADE per ora.
        related_name='students',
        limit_choices_to={'role': UserRole.TEACHER}, # Assicura che si possa collegare solo a Docenti
        verbose_name=_('Teacher')
    )
    student_code = models.CharField(
        _('Student Code'),
        max_length=50,
        unique=True,
        help_text=_('Codice univoco identificativo dello studente (es. matricola).')
    )
    pin_hash = models.CharField( # Memorizza l'hash del PIN
        _('PIN Hash'),
        max_length=128,
        help_text=_('Hash del PIN numerico per l\'accesso studente.')
        # Non impostare un default, deve essere impostato alla creazione
    )
    first_name = models.CharField(_('First Name'), max_length=150)
    last_name = models.CharField(_('Last Name'), max_length=150)
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
        # Aggiungere validazione per assicurarsi che sia numerico e di lunghezza adeguata?
        if not raw_pin or not raw_pin.isdigit():
             raise ValueError("Il PIN deve essere numerico.")
        # Esempio: lunghezza minima 4 cifre
        if len(raw_pin) < 4:
             raise ValueError("Il PIN deve essere di almeno 4 cifre.")
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


class RegistrationToken(models.Model):
    """
    Modello per memorizzare i token univoci di registrazione per gli studenti,
    generati dai docenti.
    """
    token = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('Token')
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE, # Se il docente viene eliminato, elimina anche i token associati
        related_name='registration_tokens',
        limit_choices_to={'role': UserRole.TEACHER},
        verbose_name=_('Teacher'),
        help_text=_('Il docente che ha generato questo token.')
    )
    created_at = models.DateTimeField(
        _('Created At'),
        auto_now_add=True,
        help_text=_('Data e ora di creazione del token.')
    )
    expires_at = models.DateTimeField(
        _('Expires At'),
        help_text=_('Data e ora di scadenza del token.')
        # Impostato nel metodo save
    )
    used_at = models.DateTimeField(
        _('Used At'),
        null=True,
        blank=True,
        help_text=_('Data e ora in cui il token è stato utilizzato per la registrazione.')
    )
    student = models.OneToOneField( # Un token può registrare un solo studente
        Student,
        on_delete=models.SET_NULL, # Se lo studente viene eliminato, non eliminare il token, ma scollega
        null=True,
        blank=True,
        related_name='registration_token_used',
        verbose_name=_('Student Registered'),
        help_text=_('Lo studente che si è registrato utilizzando questo token.')
    )
    # Aggiungi ForeignKey opzionale al gruppo
    source_group = models.ForeignKey(
        'student_groups.StudentGroup', # Riferimento stringa al modello nell'altra app
        on_delete=models.SET_NULL, # Se il gruppo viene eliminato, non eliminare il token
        null=True,
        blank=True,
        related_name='registration_tokens_generated', # Nome per accedere ai token dal gruppo
        verbose_name=_('Gruppo di Origine'),
        help_text=_('Il gruppo specifico per cui questo token è stato generato (se applicabile).')
    )

    class Meta:
        verbose_name = _('Registration Token')
        verbose_name_plural = _('Registration Tokens')
        ordering = ['-created_at']

    def __str__(self):
        # Formattazione sicura per evitare errori se expires_at è None (anche se save dovrebbe prevenirlo)
        expires_str = self.expires_at.strftime('%Y-%m-%d %H:%M') if self.expires_at else "N/A"
        return f"Token for {self.teacher.username} (Expires: {expires_str})"

    def save(self, *args, **kwargs):
        # Imposta la data di scadenza se non è già impostata (es. 7 giorni dalla creazione)
        if not self.expires_at:
            # Assicurati che timezone.now() sia chiamato qui per ottenere l'ora corrente al momento del salvataggio
            self.expires_at = timezone.now() + timedelta(days=7) # Scadenza di default a 7 giorni
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        """ Verifica se il token è ancora valido (non scaduto e non utilizzato). """
        # Assicurati che expires_at esista prima di confrontare
        if not self.expires_at:
            return False
        return self.used_at is None and timezone.now() < self.expires_at

    @property
    def registration_link(self):
        """ Genera l'URL di registrazione completo usando FRONTEND_STUDENT_BASE_URL dalle impostazioni. """
        from django.conf import settings
        from urllib.parse import urljoin # Per unire correttamente base URL e path

        # Assicurati che la base URL finisca con '/'
        base_url = settings.FRONTEND_STUDENT_BASE_URL
        if not base_url.endswith('/'):
             base_url += '/'

        # Il path relativo per la registrazione (senza slash iniziale se base_url finisce con slash)
        # Usa il path corretto definito nel router frontend
        registration_path = f"register/student?token={self.token}"

        # Unisci la base URL e il path relativo
        return urljoin(base_url, registration_path)

