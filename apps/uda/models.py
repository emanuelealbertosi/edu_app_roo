from django.db import models
from django.conf import settings # Per AUTH_USER_MODEL
import re # Import per espressioni regolari
import bleach # Import bleach per la sanitizzazione HTML
import logging

logger = logging.getLogger(__name__)
# Assumiamo che i modelli Subject, Topic, Lesson, Quiz siano definiti altrove
# e importabili. Ad esempio:
# from apps.education.models import Subject, Topic, Lesson, Quiz
# Per ora, useremo stringhe per le relazioni ForeignKey e ManyToManyField
# se i modelli non sono ancora definiti o per evitare import circolari.
# Sarà necessario sostituirli con i riferimenti corretti ai modelli.

# Configurazione per Bleach

# Funzione per validare che l'attributo 'style' contenga solo la proprietà 'color'
def is_safe_css_color_property(tag, name, value):
    """
    Verifica se la stringa CSS per l'attributo 'style' rappresenta solo la proprietà 'color'.
    Esempio: "color: #FF0000", "color: red", "   color  : blue ;  "
    Non permette altre proprietà: "color: red; font-weight: bold" -> False
    """
    # Dividi le dichiarazioni CSS per ';'
    # Ignora dichiarazioni vuote risultanti da ';;' o ';' finale.
    declarations = [d.strip() for d in value.split(';') if d.strip()]

    if not declarations:
        # Stile vuoto o solo spazi/punti e virgola. Non contiene 'color'.
        return False

    if len(declarations) > 1: # Più di una proprietà CSS definita
        return False
        
    declaration = declarations[0]
    
    # Verifica che la singola dichiarazione sia 'color: valore'
    # Il valore del colore può essere complesso (es. rgb(), nomi, hex).
    # Non validiamo il *valore* del colore qui, solo la *proprietà*.
    match = re.fullmatch(r'color\s*:[^;]+', declaration, re.IGNORECASE)
    return bool(match)

ALLOWED_TAGS = [
    'p', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'br',
    'span', # Per il colore del testo
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'span': {'style': is_safe_css_color_property}, # Permette solo 'color' in style
    'ul': True, # Permette tutti gli attributi per <ul>
    'ol': True, # Permette tutti gli attributi per <ol>
    'li': True, # Permette tutti gli attributi per <li>
}
# ALLOWED_STYLES non è più necessario con bleach >= 5.0 e la callback per 'style'

def sanitize_html(html_content):
    logger.debug(f"Sanitizing HTML (input type: {type(html_content)}): '{str(html_content)[:200]}'")
    if html_content is None:
        logger.debug("Sanitize HTML: input is None, returning None.")
        return None
    
    sanitized = bleach.clean(
        str(html_content), # Assicura che l'input sia una stringa
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES, # Usa la callback per validare gli stili
        strip=True # Rimuove i tag non permessi invece di renderli innocui
    )
    logger.debug(f"Sanitizing HTML (output type: {type(sanitized)}): '{str(sanitized)[:200]}'")
    return sanitized

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

    def save(self, *args, **kwargs):
        logger.debug(f"UDATemplateContent save called for ID {self.pk}. Original note_template_content: '{str(self.note_template_content)[:100]}', activity_template_description: '{str(self.activity_template_description)[:100]}'")
        if self.note_template_content:
            self.note_template_content = sanitize_html(self.note_template_content)
            logger.debug(f"UDATemplateContent ID {self.pk} after sanitizing note_template_content: '{str(self.note_template_content)[:100]}'")
        if self.activity_template_description:
            self.activity_template_description = sanitize_html(self.activity_template_description)
            logger.debug(f"UDATemplateContent ID {self.pk} after sanitizing activity_template_description: '{str(self.activity_template_description)[:100]}'")
        super().save(*args, **kwargs)
        logger.debug(f"UDATemplateContent ID {self.pk} save completed.")

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
    # Nuovi campi per conoscenze, abilità, competenze
    knowledge_html = models.TextField(blank=True, null=True, help_text="Contenuto HTML per le conoscenze")
    skills_html = models.TextField(blank=True, null=True, help_text="Contenuto HTML per le abilità")
    competences_html = models.TextField(blank=True, null=True, help_text="Contenuto HTML per le competenze")

    # Campi per Export DOCX
    is_civic_education = models.BooleanField(default=False, help_text="Indica se l'UDA rientra nel percorso di Educazione Civica")
    didactic_strategies_html = models.TextField(blank=True, null=True, help_text="Contenuto HTML per le strategie didattiche (export)")
    materials_tools_html = models.TextField(blank=True, null=True, help_text="Contenuto HTML per materiali e strumenti (export)")
    assessment_type_html = models.TextField(blank=True, null=True, help_text="Contenuto HTML per il tipo di verifiche (export)")
    evaluation_html = models.TextField(blank=True, null=True, help_text="Contenuto HTML per la valutazione (export)")
    key_and_citizenship_competences_html = models.TextField(blank=True, null=True, help_text="Contenuto HTML per le Competenze chiave e di cittadinanza (export)")
    other_involved_subjects_text = models.TextField(blank=True, null=True, help_text="Testo libero per Altre Discipline Coinvolte (export)")
    export_specific_annotations_html = models.TextField(blank=True, null=True, help_text="Contenuto HTML per Annotazioni specifiche per l'export")

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

    @property
    def total_estimated_hours(self):
        from decimal import Decimal
        total_hours = Decimal('0.0')
        for content in self.contents.all().select_related('lesson'): # Aggiunto select_related per efficienza
            hours_to_add = Decimal('0.0')
            if content.estimated_hours is not None:
                hours_to_add = content.estimated_hours
            elif content.content_type == 'LESSON' and content.lesson and content.lesson.estimated_hours is not None:
                hours_to_add = content.lesson.estimated_hours
            
            if hours_to_add is not None: # Assicura che hours_to_add sia un Decimal o convertibile
                try:
                    total_hours += Decimal(hours_to_add)
                except TypeError: # Gestisce il caso in cui hours_to_add potrebbe essere None nonostante i controlli
                    pass # Non aggiungere nulla se non è un numero valido
        return total_hours

    @property
    def total_lesson_estimated_hours(self):
        from decimal import Decimal
        total_hours = Decimal('0.0')
        lesson_contents = self.contents.filter(content_type='LESSON').select_related('lesson')
        for content in lesson_contents:
            hours_to_add = Decimal('0.0')
            if content.estimated_hours is not None:
                hours_to_add = content.estimated_hours
            elif content.lesson and content.lesson.estimated_hours is not None: # Fallback
                hours_to_add = content.lesson.estimated_hours
            
            if hours_to_add is not None:
                try:
                    total_hours += Decimal(hours_to_add)
                except TypeError:
                    pass
        return total_hours

    @property
    def lesson_count(self):
        return self.contents.filter(content_type='LESSON').count()

    class Meta:
        verbose_name = "UDA"
        verbose_name_plural = "UDAs"

    def save(self, *args, **kwargs):
        logger.debug(f"UDA save called for ID {self.pk}.")
        if self.description:
            self.description = sanitize_html(self.description)
            logger.debug(f"UDA ID {self.pk} after sanitizing description: '{str(self.description)[:100]}'")
        if self.knowledge_html:
            self.knowledge_html = sanitize_html(self.knowledge_html)
            logger.debug(f"UDA ID {self.pk} after sanitizing knowledge_html: '{str(self.knowledge_html)[:100]}'")
        if self.skills_html:
            self.skills_html = sanitize_html(self.skills_html)
            logger.debug(f"UDA ID {self.pk} after sanitizing skills_html: '{str(self.skills_html)[:100]}'")
        if self.competences_html:
            self.competences_html = sanitize_html(self.competences_html)
            logger.debug(f"UDA ID {self.pk} after sanitizing competences_html: '{str(self.competences_html)[:100]}'")
        if self.didactic_strategies_html:
            self.didactic_strategies_html = sanitize_html(self.didactic_strategies_html)
            logger.debug(f"UDA ID {self.pk} after sanitizing didactic_strategies_html: '{str(self.didactic_strategies_html)[:100]}'")
        if self.materials_tools_html:
            self.materials_tools_html = sanitize_html(self.materials_tools_html)
            logger.debug(f"UDA ID {self.pk} after sanitizing materials_tools_html: '{str(self.materials_tools_html)[:100]}'")
        if self.assessment_type_html:
            self.assessment_type_html = sanitize_html(self.assessment_type_html)
            logger.debug(f"UDA ID {self.pk} after sanitizing assessment_type_html: '{str(self.assessment_type_html)[:100]}'")
        if self.evaluation_html:
            self.evaluation_html = sanitize_html(self.evaluation_html)
            logger.debug(f"UDA ID {self.pk} after sanitizing evaluation_html: '{str(self.evaluation_html)[:100]}'")
        if self.key_and_citizenship_competences_html:
            self.key_and_citizenship_competences_html = sanitize_html(self.key_and_citizenship_competences_html)
            logger.debug(f"UDA ID {self.pk} after sanitizing key_and_citizenship_competences_html: '{str(self.key_and_citizenship_competences_html)[:100]}'")
        if self.export_specific_annotations_html:
            self.export_specific_annotations_html = sanitize_html(self.export_specific_annotations_html)
            logger.debug(f"UDA ID {self.pk} after sanitizing export_specific_annotations_html: '{str(self.export_specific_annotations_html)[:100]}'")
        # Il campo other_involved_subjects_text è un TextField semplice, non HTML, quindi non necessita di sanitizzazione con bleach.
        super().save(*args, **kwargs)
        logger.debug(f"UDA ID {self.pk} save completed.")

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
    actual_hours = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        help_text="Tempo effettivo impiegato in ore (es. 1.5 per 1 ora e mezza)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = "UDA Content"
        verbose_name_plural = "UDA Contents"

    def save(self, *args, **kwargs):
        # Log aggiunto per vedere lo stato dell'istanza come arriva a save()
        try:
            logger.debug(f"UDAContent instance __dict__ at start of save for ID {self.pk}: {self.__dict__}")
        except Exception as e:
            logger.error(f"Error logging __dict__ for UDAContent ID {self.pk}: {e}")

        logger.debug(f"UDAContent save called for ID {self.pk}. Current self.note_content: '{str(self.note_content)[:200]}', current self.activity_description: '{str(self.activity_description)[:200]}'")
        if self.note_content is not None: # Controlla esplicitamente per None per permettere stringhe vuote intenzionali
            # Se il campo è una stringa vuota dopo la modifica dell'utente, non dovrebbe essere sanitizzato a None se non è questo il comportamento desiderato.
            # La sanitizzazione di una stringa vuota "" dovrebbe restituire ""
            self.note_content = sanitize_html(self.note_content)
            logger.debug(f"UDAContent ID {self.pk} after sanitizing note_content: '{str(self.note_content)[:200]}'")
        
        if self.activity_description is not None: # Controlla esplicitamente per None
            self.activity_description = sanitize_html(self.activity_description)
            logger.debug(f"UDAContent ID {self.pk} after sanitizing activity_description: '{str(self.activity_description)[:200]}'")
        
        super().save(*args, **kwargs)
        logger.debug(f"UDAContent ID {self.pk} save completed. Final note_content: '{str(self.note_content)[:200]}', final activity_description: '{str(self.activity_description)[:200]}'")

    def __str__(self):
        return f"{self.get_content_type_display()} in {self.uda.title} (Order: {self.order})"
