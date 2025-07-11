from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field

class Announcement(models.Model):
    """
    Modello per gli avvisi mostrati agli utenti.
    """
    AUDIENCE_CHOICES = (
        ('ALL', _('All Users')),
        ('TEACHERS', _('Teachers Only')),
        ('STUDENTS', _('Students Only')),
    )

    title = models.CharField(_("Title"), max_length=255)
    content = CKEditor5Field(_("Content"), config_name='extends', help_text=_("Rich text content for the announcement modal."))
    is_active = models.BooleanField(_("Is Active"), default=True, help_text=_("Only active announcements will be shown."))
    is_important = models.BooleanField(_("Is Important"), default=False, help_text=_("Important announcements are shown first."))
    target_audience = models.CharField(
        _("Target Audience"),
        max_length=10,
        choices=AUDIENCE_CHOICES,
        default='ALL'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Announcement")
        verbose_name_plural = _("Announcements")
        ordering = ['-is_important', '-created_at']

    def __str__(self):
        return self.title

class UserAnnouncementView(models.Model):
    """
    Modello per tracciare quali utenti/studenti hanno visto un avviso
    e se hanno scelto di non mostrarlo più.
    """
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name="views")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_("The User (teacher/admin) who viewed the announcement.")
    )
    student = models.ForeignKey(
        'users.Student',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_("The Student who viewed the announcement.")
    )
    do_not_show_again = models.BooleanField(_("Do Not Show Again"), default=False)
    first_viewed_at = models.DateTimeField(auto_now_add=True)
    last_viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("User Announcement View")
        verbose_name_plural = _("User Announcement Views")
        # Un utente o uno studente può avere una sola entry per avviso
        unique_together = [['announcement', 'user'], ['announcement', 'student']]
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(student__isnull=False),
                name='user_or_student_is_not_null'
            )
        ]

    def __str__(self):
        viewer = self.user if self.user else self.student
        return f"'{self.announcement.title}' viewed by {viewer}"