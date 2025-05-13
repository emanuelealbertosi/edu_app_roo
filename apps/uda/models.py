from django.db import models
from django.conf import settings # Per AUTH_USER_MODEL
# Assumiamo che i modelli Subject, Topic, Lesson, Quiz siano definiti altrove
# e importabili. Ad esempio:
# from apps.education.models import Subject, Topic, Lesson, Quiz
# Per ora, useremo stringhe per le relazioni ForeignKey e ManyToManyField
# se i modelli non sono ancora definiti o per evitare import circolari.
# Sarà necessario sostituirli con i riferimenti corretti ai modelli.

class Course(models.Model):
   teacher = models.ForeignKey(
       settings.AUTH_USER_MODEL,
       on_delete=models.CASCADE,
       related_name='courses'
   )
   name = models.CharField(max_length=255)
   description = models.TextField(blank=True, null=True)
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   class Meta:
       app_label = 'uda'
       unique_together = ('teacher', 'name')
       verbose_name = "Course"
       verbose_name_plural = "Courses"

   def __str__(self):
       return f"{self.name} (by {self.teacher.username})"

class UDATemplate(models.Model):
   teacher = models.ForeignKey(
       settings.AUTH_USER_MODEL,
       on_delete=models.CASCADE,
       related_name='uda_templates'
   )
   name = models.CharField(max_length=255)
   description = models.TextField(blank=True, null=True)
   subject = models.ForeignKey(
       'lezioni.Subject', # Modificato da education.Subject
       on_delete=models.SET_NULL,
       blank=True,
       null=True,
       related_name='uda_templates'
   )
   topics = models.ManyToManyField(
       'lezioni.Topic', # Modificato da education.Topic
       through='UDATemplateTopic',
       related_name='uda_templates'
   )
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   class Meta:
       unique_together = ('teacher', 'name')
       verbose_name = "UDA Template"
       verbose_name_plural = "UDA Templates"

   def __str__(self):
       return f"{self.name} (by {self.teacher.username})"

class UDATemplateTopic(models.Model):
    udatemplate = models.ForeignKey(UDATemplate, on_delete=models.CASCADE)
    topic = models.ForeignKey('lezioni.Topic', on_delete=models.CASCADE) # Modificato da education.Topic

    class Meta:
        unique_together = ('udatemplate', 'topic')
        verbose_name = "UDA Template Topic"
        verbose_name_plural = "UDA Template Topics"

    def __str__(self):
        return f"{self.udatemplate.name} - {self.topic.name}"

class UDATemplateContent(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('LESSON', 'Lesson'),
        ('QUIZ_TEMPLATE', 'Quiz Template'), # Modificato
        ('NOTE_TEMPLATE', 'Note Template'),
        ('ACTIVITY_TEMPLATE', 'Activity Template'),
    ]
    uda_template = models.ForeignKey(
        UDATemplate,
        on_delete=models.CASCADE,
        related_name='contents'
    )
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES
    )
    lesson = models.ForeignKey(
        'lezioni.Lesson', # Modificato da education.Lesson
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    quiz_template = models.ForeignKey( # Rinominato da quiz a quiz_template
        'education.QuizTemplate', # Modificato per puntare a QuizTemplate
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Riferimento al template del quiz"
    )
    note_template_title = models.CharField(max_length=255, blank=True, null=True)
    note_template_content = models.TextField(blank=True, null=True)
    activity_template_title = models.CharField(max_length=255, blank=True, null=True)
    activity_template_description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField()
    estimated_hours = models.DecimalField( # Aggiunto campo estimated_hours
        max_digits=4, decimal_places=1, null=True, blank=True,
        help_text="Tempo stimato in ore (es. 1.5 per 1 ora e mezza)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = "UDA Template Content"
        verbose_name_plural = "UDA Template Contents"

    def __str__(self):
        return f"{self.get_content_type_display()} in {self.uda_template.name} (Order: {self.order})"

class UDA(models.Model):
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='udas'
    )
    source_template = models.ForeignKey(
        UDATemplate,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='generated_udas'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    subjects = models.ManyToManyField(
        'lezioni.Subject',
        through='UDASubject',
        related_name='udas_multiple', # Usiamo un related_name diverso per evitare conflitti temporanei
        blank=True # Permette a una UDA di non avere materie associate
    )
    topics = models.ManyToManyField(
        'lezioni.Topic', # Modificato da education.Topic
        through='UDATopic',
        related_name='udas'
    )
    course = models.ForeignKey(
       Course,
       on_delete=models.SET_NULL,
       blank=True,
       null=True,
       related_name='udas'
    )
    order_in_course = models.PositiveIntegerField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='TODO'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "UDA"
        verbose_name_plural = "UDAs"

    def __str__(self):
        return f"{self.title} (by {self.teacher.username})"

class UDATopic(models.Model):
    uda = models.ForeignKey(UDA, on_delete=models.CASCADE)
    topic = models.ForeignKey('lezioni.Topic', on_delete=models.CASCADE) # Modificato da education.Topic

    class Meta:
        unique_together = ('uda', 'topic')
        verbose_name = "UDA Topic"
        verbose_name_plural = "UDA Topics"

    def __str__(self):
        return f"{self.uda.title} - {self.topic.name}"

class UDASubject(models.Model):
    uda = models.ForeignKey(UDA, on_delete=models.CASCADE)
    subject = models.ForeignKey('lezioni.Subject', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('uda', 'subject')
        verbose_name = "UDA Subject"
        verbose_name_plural = "UDA Subjects"

    def __str__(self):
        return f"{self.uda.title} - {self.subject.name}"

class UDAContent(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('LESSON', 'Lesson'),
        ('QUIZ', 'Quiz'), # MODIFICATO da QUIZ_TEMPLATE
        ('NOTE', 'Note'),
        ('ACTIVITY', 'Activity'),
    ]
    uda = models.ForeignKey(
        UDA,
        on_delete=models.CASCADE,
        related_name='contents'
    )
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES
    )
    lesson = models.ForeignKey(
        'lezioni.Lesson', # Modificato da education.Lesson
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    quiz_template = models.ForeignKey( # Rinominato da quiz a quiz_template
        'education.QuizTemplate', # Modificato per puntare a QuizTemplate
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Riferimento al template del quiz da cui istanziare un quiz concreto in un secondo momento"
    )
    note_title = models.CharField(max_length=255, blank=True, null=True)
    note_content = models.TextField(blank=True, null=True)
    activity_title = models.CharField(max_length=255, blank=True, null=True)
    activity_description = models.TextField(blank=True, null=True)
    activity_attachment_url = models.FileField(upload_to='uda_attachments/', blank=True, null=True) # o CharField se URL esterno
    activity_completed = models.BooleanField(default=False) # Specifico per ACTIVITY
    teacher_marked_completed = models.BooleanField(default=False) # Per tutti i tipi, marcato dal docente
    order = models.PositiveIntegerField()
    estimated_hours = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        help_text="Tempo stimato in ore (es. 1.5 per 1 ora e mezza)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = "UDA Content"
        verbose_name_plural = "UDA Contents"

    def __str__(self):
        return f"{self.get_content_type_display()} in {self.uda.title} (Order: {self.order})"
