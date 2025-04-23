from django.db import models
from django.conf import settings
# Assumendo che il modello Studente sia in apps.users.models
# Se Student è definito altrove, questo import dovrà essere aggiornato.
# Potrebbe essere necessario verificare la struttura effettiva di apps.users
try:
    from apps.users.models import Student
except ImportError:
    # Fallback o gestione alternativa se la struttura è diversa
    # Per ora, assumiamo che Student sia accessibile così o che
    # la relazione verrà definita usando stringhe se necessario.
    # Questo potrebbe richiedere aggiustamenti futuri.
    Student = settings.AUTH_USER_MODEL # Placeholder temporaneo se Student non trovato

class Subject(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    # Permette sia Admin che Docenti (verificare permessi nelle view)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_subjects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materie"

class Topic(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    # Permette sia Admin che Docenti (verificare permessi nelle view)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_topics')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'subject') # Un argomento deve essere unico all'interno di una materia
        verbose_name = "Argomento"
        verbose_name_plural = "Argomenti"

    def __str__(self):
        return f"{self.subject.name} - {self.name}"

class Lesson(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    # Protegge dalla cancellazione dell'argomento se ci sono lezioni collegate
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name='lessons')
    # Solo Docente può creare lezioni (verificare permessi nelle view)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_lessons')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False, help_text="Se la lezione è visibile agli studenti assegnati.")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Lezione"
        verbose_name_plural = "Lezioni"

def lesson_content_upload_path(instance, filename):
    # Salva i file in mediafiles/lezioni_contenuti/<lesson_id>/<filename>
    # Usiamo 'lezioni_contenuti' per evitare conflitti con il nome dell'app
    return f'lezioni_contenuti/{instance.lesson.id}/{filename}'

class LessonContent(models.Model):
    CONTENT_TYPES = [
        ('html', 'Contenuto HTML'),
        ('pdf', 'Documento PDF'),
        ('ppt', 'Presentazione PPT/PPTX'),
        ('url', 'Link Esterno'),
        # ('video', 'File Video'), # Esempio futuro
        # ('image', 'File Immagine'), # Esempio futuro
    ]
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='contents')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES, verbose_name="Tipo di Contenuto")
    # Usare un campo per l'editor avanzato, es. CKEditor (da configurare separatamente)
    html_content = models.TextField(blank=True, help_text="Usare per Contenuto HTML.", verbose_name="Contenuto HTML")
    # FileField per PDF, PPT, ecc.
    file = models.FileField(upload_to=lesson_content_upload_path, blank=True, null=True, help_text="Usare per PDF, PPT, ecc.", verbose_name="File Caricato")
    url = models.URLField(blank=True, help_text="Usare per Link Esterno.", verbose_name="URL Esterno")
    title = models.CharField(max_length=255, blank=True, help_text="Titolo opzionale per questo blocco di contenuto", verbose_name="Titolo Contenuto")
    order = models.PositiveIntegerField(default=0, help_text="Ordine di visualizzazione nella lezione.", verbose_name="Ordine")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Contenuto Lezione"
        verbose_name_plural = "Contenuti Lezione"

    def __str__(self):
         return f"Contenuto per '{self.lesson.title}' ({self.get_content_type_display()}) - Ordine: {self.order}"

class LessonAssignment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='assignments')
    # Assicurarsi che l'import di Student sia corretto
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='lesson_assignments')
    # Docente che ha assegnato
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='made_lesson_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(null=True, blank=True, help_text="Data e ora prima visualizzazione da parte dello studente")

    class Meta:
        unique_together = ('lesson', 'student') # Uno studente può essere assegnato a una lezione solo una volta
        ordering = ['-assigned_at']
        verbose_name = "Assegnazione Lezione"
        verbose_name_plural = "Assegnazioni Lezioni"

    def __str__(self):
        # Tentativo di ottenere un nome rappresentativo per lo studente
        student_name = getattr(self.student, 'unique_identifier', getattr(self.student, 'username', self.student.id))
        return f"'{self.lesson.title}' assegnata a {student_name}"
