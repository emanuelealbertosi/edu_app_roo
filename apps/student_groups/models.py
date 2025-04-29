from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string
from urllib.parse import urljoin, urlencode
from apps.users.models import RegistrationToken, User, UserRole # Importa User e UserRole
from django.utils.translation import gettext_lazy as _ # Import per traduzioni

# Create your models here.

def generate_registration_token():
    """Generates a unique random string for registration token."""
    # TODO: Add logic to ensure uniqueness if high collision probability is expected
    return get_random_string(length=32)

class StudentGroup(models.Model):
    """Represents a group of students managed by a teacher."""
    owner = models.ForeignKey( # Rinominato da teacher
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # Considerare SET_NULL se si vuole mantenere il gruppo senza owner?
        related_name='owned_groups', # Aggiornato related_name
        verbose_name=_("Docente Proprietario"),
        limit_choices_to={'role': UserRole.TEACHER} # Usa UserRole importato
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Nome Gruppo"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descrizione (Opzionale)"
    )
    # Sostituiamo il CharField con una relazione al modello RegistrationToken
    registration_token = models.OneToOneField(
        'users.RegistrationToken',
        on_delete=models.SET_NULL, # Se il token viene eliminato, non eliminare il gruppo
        null=True,
        blank=True,
        related_name='group', # Permette di accedere al gruppo dal token (token.group)
        verbose_name="Token di Registrazione Associato",
        help_text="Token UUID associato a questo gruppo per la registrazione."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data Creazione"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Attivo")
    )
    is_public = models.BooleanField(
        _("Gruppo Pubblico"),
        default=False,
        help_text=_("Indica se il gruppo è visibile ad altri docenti per richieste di accesso.")
    )
    # ManyToManyField defined implicitly by StudentGroupMembership

    class Meta:
        verbose_name = _("Gruppo di Studenti")
        verbose_name_plural = _("Gruppi di Studenti")
        ordering = ['owner', 'name'] # Aggiornato a owner
        # Ensure an owner cannot have two groups with the same name
        unique_together = ('owner', 'name') # Aggiornato a owner

    def __str__(self):
        return f"{self.name} (Owner: {self.owner.username})" # Aggiornato a owner

    def generate_token(self):
        """
        Genera un nuovo RegistrationToken (UUID) per il gruppo,
        eliminando eventuali token precedenti associati.
        """
        # Elimina il token precedente, se esiste
        if self.registration_token:
            self.registration_token.delete()

        # Crea un nuovo token associato al docente E al gruppo corrente
        new_token = RegistrationToken.objects.create(
            teacher=self.owner, # Aggiornato a owner
            source_group=self # Associa questo gruppo al token
        )
        self.registration_token = new_token
        self.save(update_fields=['registration_token'])
        return new_token # Restituisce l'istanza del token UUID

    def delete_token(self):
        """Elimina il RegistrationToken associato a questo gruppo."""
        if self.registration_token:
            self.registration_token.delete()
            # self.registration_token viene impostato a None automaticamente da on_delete=models.SET_NULL
            # Non è necessario salvare nuovamente il gruppo qui, a meno che non ci siano altri campi da aggiornare.
            # self.save(update_fields=['registration_token']) # Rimosso perché SET_NULL lo gestisce

    @property
    def registration_link(self):
        """ Restituisce l'URL di registrazione completo dal token associato, se esiste. """
        if self.registration_token:
            # La logica per costruire il link è già nel modello RegistrationToken
            return self.registration_token.registration_link
        return None


class StudentGroupMembership(models.Model):
    """Intermediate model for the ManyToMany relationship between StudentGroup and Student."""
    group = models.ForeignKey(
        StudentGroup,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name="Gruppo"
    )
    student = models.ForeignKey(
        'users.Student', # Assumes Student model is in 'users' app
        on_delete=models.CASCADE,
        related_name='group_memberships',
        verbose_name="Studente"
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data Iscrizione al Gruppo"
    )

    class Meta:
        verbose_name = "Appartenenza a Gruppo"
        verbose_name_plural = "Appartenenze ai Gruppi"
        # Ensure a student can only be in a specific group once
        unique_together = ('group', 'student')
        ordering = ['group', 'student']

    def __str__(self):
        return f"Studente {self.student.unique_identifier} nel gruppo {self.group.name}"

# Add the ManyToMany field to StudentGroup using 'through'
# This needs to be done after StudentGroupMembership is defined if not using string references throughout
# However, Django handles string references well, so defining it directly in StudentGroup is fine.
# models.ManyToManyField(
#     'users.Student',
#     through=StudentGroupMembership,
#     related_name='student_groups',
#     verbose_name="Studenti Membri"
# )
class GroupAccessRequest(models.Model):
    """ Modello per gestire le richieste di accesso ai gruppi pubblici da parte di altri docenti. """
    class AccessStatus(models.TextChoices):
        PENDING = 'PENDING', _('In Attesa')
        APPROVED = 'APPROVED', _('Approvato')
        REJECTED = 'REJECTED', _('Rifiutato')

    group = models.ForeignKey(
        StudentGroup,
        on_delete=models.CASCADE,
        related_name='access_requests',
        verbose_name=_("Gruppo Richiesto")
    )
    requesting_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_access_requests',
        limit_choices_to={'role': UserRole.TEACHER},
        verbose_name=_("Docente Richiedente")
    )
    status = models.CharField(
        _("Stato Richiesta"),
        max_length=10,
        choices=AccessStatus.choices,
        default=AccessStatus.PENDING
    )
    requested_at = models.DateTimeField(
        _("Data Richiesta"),
        auto_now_add=True
    )
    responded_at = models.DateTimeField(
        _("Data Risposta"),
        null=True,
        blank=True
    )
    # Chi ha risposto? Dovrebbe essere l'owner del gruppo.
    responder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Mantiene la traccia anche se l'owner viene eliminato
        related_name='responded_group_requests',
        limit_choices_to={'role': UserRole.TEACHER},
        verbose_name=_("Docente che ha Risposto"),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("Richiesta Accesso Gruppo")
        verbose_name_plural = _("Richieste Accesso Gruppi")
        # Un docente può richiedere accesso a un gruppo una sola volta
        unique_together = ('group', 'requesting_teacher')
        ordering = ['group', '-requested_at']

    def __str__(self):
        return f"Richiesta di {self.requesting_teacher.username} per '{self.group.name}' ({self.get_status_display()})"