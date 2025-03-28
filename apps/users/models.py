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
        return self.role == UserRole.ADMIN

    @property
    def is_teacher(self):
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
        return f"{self.first_name} {self.last_name}"

    @property
    def is_authenticated(self):
        """
        Property to satisfy Django REST Framework's IsAuthenticated permission check
        when the user object is an instance of Student.
        """
        return True

    def set_pin(self, raw_pin):
        """ Imposta l'hash del PIN dal PIN in chiaro. """
        # Aggiungere validazione per assicurarsi che sia numerico e di lunghezza adeguata?
        if not raw_pin or not raw_pin.isdigit():
             raise ValueError("Il PIN deve essere numerico.")
        # Esempio: lunghezza minima 4 cifre
        if len(raw_pin) < 4:
             raise ValueError("Il PIN deve essere di almeno 4 cifre.")
        self.pin_hash = make_password(raw_pin)

    def check_pin(self, raw_pin):
        """ Verifica se il PIN in chiaro corrisponde all'hash memorizzato. """
        return check_password(raw_pin, self.pin_hash)

