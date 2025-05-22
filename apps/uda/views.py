from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated # Permesso base, da affinare
from rest_framework import permissions # Per IsOwnerOrReadOnly
from django.db import transaction # Per operazioni atomiche
from django.http import HttpResponse # Per l'export DOCX
from django.template.loader import render_to_string
from xhtml2pdf import pisa # Importa pisa da xhtml2pdf
# from weasyprint.fonts import FontConfiguration # Non più necessario per xhtml2pdf

from .models import Course, UDATemplate, UDA, UDAContent, UDATemplateContent # Aggiunto Course
from .serializers import (
   CourseSerializer, UDATemplateSerializer, UDASerializer, # Aggiunto CourseSerializer
   UDAContentSerializer, UDATemplateContentSerializer
)
# Import per python-docx
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from io import BytesIO
from django.db.models import Sum
from django.utils.text import get_valid_filename
from bs4 import BeautifulSoup # Per estrarre testo da HTML
import logging # Assicurati che logging sia importato

logger = logging.getLogger(__name__)

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it,
    while allowing read-only access for safe methods if authenticated.
    """
    def has_permission(self, request, view):
        # Allow access if user is authenticated. Object-level permission will handle ownership.
        # This check is often redundant if IsAuthenticated is also in permission_classes,
        # but good for clarity if IsOwnerOrReadOnly is used alone.
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed if the user is authenticated (covered by has_permission
        # and IsAuthenticated in the view's permission_classes).
        # The get_queryset method in the view is responsible for filtering objects
        # so that users only see their own objects for SAFE_METHODS.
        if request.method in permissions.SAFE_METHODS:
            return True # Further filtering by get_queryset
        # Write permissions are only allowed to the teacher of the object.
        return obj.teacher == request.user


class CourseViewSet(viewsets.ModelViewSet):
   """
   ViewSet per gestire i Corsi (Course).
   Permette CRUD sui corsi e azioni custom per listare e riordinare le UDA.
   """
   queryset = Course.objects.all()
   serializer_class = CourseSerializer
   permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

   def get_queryset(self):
       user = self.request.user
       if user.is_authenticated:
           return Course.objects.filter(teacher=user)
       return Course.objects.none()

   def perform_create(self, serializer):
       serializer.save(teacher=self.request.user)

   @action(detail=True, methods=['get'], url_path='udas')
   def udas_in_course(self, request, pk=None):
       course = self.get_object()
       # Assicurati che l'utente possa accedere a questo corso (permesso IsOwner già applicato)
       udas = UDA.objects.filter(course=course).order_by('order_in_course', 'title')
       serializer = UDASerializer(udas, many=True, context={'request': request})
       return Response(serializer.data)

   @action(detail=True, methods=['post'], url_path='udas/reorder')
   def reorder_udas(self, request, pk=None):
       course = self.get_object()
       uda_ids = request.data.get('uda_ids', [])

       if not isinstance(uda_ids, list):
           return Response({'error': 'uda_ids must be a list.'}, status=status.HTTP_400_BAD_REQUEST)

       current_udas_in_course = UDA.objects.filter(course=course)
       current_uda_ids_map = {uda.id: uda for uda in current_udas_in_course}

       # Verifica che tutti gli ID forniti appartengano al corso e siano validi
       for index, uda_id in enumerate(uda_ids):
           if uda_id not in current_uda_ids_map:
               return Response({'error': f'UDA with id {uda_id} not found in this course or is invalid.'},
                               status=status.HTTP_400_BAD_REQUEST)
           
           uda_to_update = current_uda_ids_map[uda_id]
           if uda_to_update.order_in_course != index + 1: # L'ordine è 1-based
               uda_to_update.order_in_course = index + 1
               uda_to_update.save(update_fields=['order_in_course'])
       
       # Opzionale: verifica se ci sono UDA nel corso non presenti in uda_ids
       # e gestiscile (es. mettile alla fine o segnala errore)

       return Response({'status': 'UDA reordered successfully.'}, status=status.HTTP_200_OK)

   # @action(detail=True, methods=['get'], url_path='export-udas') # Rimosso -docx dal path
   # def export_udas(self, request, pk=None): # Rimosso _docx dal nome metodo
   #     logger.info(f"EXPORT_UDAS CALLED FOR COURSE PK: {pk} WITH FORMAT: {request.query_params.get('format')}")
   #     course = self.get_object()
   #     udas_queryset = UDA.objects.filter(course=course).order_by('order_in_course', 'title')
   #     export_format = request.query_params.get('format', 'docx').lower()

   #     # Prepara i dati per il template/documento
   #     processed_udas = []
   #     for uda_instance in udas_queryset:
   #         # Calcolo ore totali UDA
   #         total_estimated_hours_val = uda_instance.contents.aggregate(Sum('estimated_hours'))['estimated_hours__sum'] or 0
   #         try:
   #             total_estimated_hours_display = f"{float(total_estimated_hours_val):.1f}"
   #         except (ValueError, TypeError):
   #             total_estimated_hours_display = "N/D"

   #         # Gestione altre discipline
   #         other_subjects_display = uda_instance.other_involved_subjects_text
   #         if not other_subjects_display and uda_instance.subjects.exists():
   #             other_subjects_display = ", ".join([s.name for s in uda_instance.subjects.all()])
           
   #         # Gestione annotazioni (per PDF, consideriamo se è HTML o testo semplice)
   #         annotations_text_for_pdf = uda_instance.description # Default
   #         is_html_annotations = False
   #         if uda_instance.export_specific_annotations_html:
   #             annotations_text_for_pdf = uda_instance.export_specific_annotations_html
   #             is_html_annotations = True # Il template HTML lo gestirà con |safe
           
   #         # Prepara i contenuti delle lezioni per il template PDF
   #         lesson_contents_for_template = []
   #         lesson_contents_queryset = uda_instance.contents.filter(content_type='LESSON').select_related('lesson')
   #         if lesson_contents_queryset.exists():
   #             for lc in lesson_contents_queryset:
   #                 hours_to_display_lc = None
   #                 if lc.estimated_hours is not None:
   #                     hours_to_display_lc = lc.estimated_hours
   #                 elif lc.lesson and lc.lesson.estimated_hours is not None:
   #                     hours_to_display_lc = lc.lesson.estimated_hours
                   
   #                 lc_hours_text = "N/D"
   #                 if hours_to_display_lc is not None:
   #                     try:
   #                         lc_hours_text = f"{float(hours_to_display_lc):.1f}"
   #                     except (ValueError, TypeError):
   #                         lc_hours_text = "N/D (err)"
   #                 lesson_contents_for_template.append({
   #                     'lesson': lc.lesson, # L'oggetto Lesson intero
   #                     'hours_display_pdf': lc_hours_text
   #                 })

   #         processed_udas.append({
   #             'title': uda_instance.title,
   #             'competences_html': uda_instance.competences_html,
   #             'topics_string': ", ".join([topic.name for topic in uda_instance.topics.all()]),
   #             'knowledge_html': uda_instance.knowledge_html,
   #             'skills_html': uda_instance.skills_html,
   #             'total_estimated_hours_display': total_estimated_hours_display,
   #             'didactic_strategies_html': uda_instance.didactic_strategies_html,
   #             'materials_tools_html': uda_instance.materials_tools_html,
   #             'assessment_type_html': uda_instance.assessment_type_html,
   #             'evaluation_html': uda_instance.evaluation_html,
   #             'other_involved_subjects_display': other_subjects_display or "N/D",
   #             'annotations_display': annotations_text_for_pdf or "N/D", # Usato per PDF
   #             'is_html_annotations': is_html_annotations, # Per PDF, per sapere se usare |safe
   #             'is_civic_education': uda_instance.is_civic_education,
   #             'lesson_contents': lesson_contents_for_template,
   #             # Campi necessari anche per DOCX se la logica viene unificata
   #             'description': uda_instance.description,
   #             'export_specific_annotations_html': uda_instance.export_specific_annotations_html,
   #         })

   #     # Sanitizza il nome del corso per il nome del file
   #     course_name_sanitized = get_valid_filename(course.name)
   #     if not course_name_sanitized:
   #         course_name_sanitized = "corso"
   #     while course_name_sanitized.endswith("_"):
   #         course_name_sanitized = course_name_sanitized[:-1]
   #     if not course_name_sanitized:
   #         course_name_sanitized = "corso"

   #     if export_format == 'pdf':
   #         try:
   #             context = {
   #                 'course': course,
   #                 'udas': processed_udas,
   #                 'teacher_name': request.user.get_full_name() or request.user.username
   #             }
   #             html_string = render_to_string('uda_export/uda_pdf_template.html', context)
               
   #             pdf_file_stream = BytesIO()
   #             # Passare l'HTML direttamente come stringa a pisa.CreatePDF
   #             # pisa si aspetta una stringa o un oggetto file-like per src.
   #             pdf = pisa.CreatePDF(
   #                 html_string,
   #                 dest=pdf_file_stream,
   #                 encoding='UTF-8' # L'encoding dell'HTML sorgente
   #             )
   #             pdf_file_stream.seek(0)

   #             if pdf.err:
   #                 # pdf.err è un codice di errore intero, pdf.log è una lista di messaggi
   #                 error_messages = "; ".join([str(msg) for msg in pdf.log if msg.level >= pisa.ERROR]) if hasattr(pdf, 'log') else str(pdf.err)
   #                 logger.error(f"Errore pisa.CreatePDF per corso {course.id}: codice {pdf.err} - {error_messages}")
   #                 return HttpResponse(f"Errore durante la generazione del PDF (codice: {pdf.err})", status=500)

   #             response = HttpResponse(pdf_file_stream.read(), content_type='application/pdf')
   #             filename = f"export_udas_{course_name_sanitized}.pdf"
   #             response['Content-Disposition'] = f'attachment; filename="{filename}"'
   #             return response
   #         except Exception as e:
   #             logger.error(f"Eccezione durante la generazione del PDF per corso {course.id}: {e}", exc_info=True)
   #             # Restituisci un errore 500 più generico, ma logga i dettagli.
   #             # In un ambiente di produzione, potresti voler evitare di esporre dettagli dell'eccezione.
   #             return HttpResponse(f"Errore interno del server durante la generazione del PDF: {str(e)}", status=500)

   #     # Default to DOCX o se export_format == 'docx'
   #     else: # Gestione DOCX (logica precedente adattata)
   #         document = Document()
   #         document.add_heading(f'Programmazione Didattica Individuale - UDA del Corso: {course.name}', level=1)
   #         p_docente = document.add_paragraph()
   #         p_docente.add_run(f"Docente: {request.user.get_full_name() or request.user.username}").bold = True

   #         def add_table_row_docx(table, label, value_html_or_text, is_html=True):
   #             row_cells = table.add_row().cells
   #             row_cells[0].text = label
   #             processed_value = "N/D"
   #             if value_html_or_text:
   #                 if is_html:
   #                     soup = BeautifulSoup(str(value_html_or_text), 'html.parser')
   #                     processed_value = soup.get_text(separator='\n', strip=True) or "N/D"
   #                 else:
   #                     processed_value = str(value_html_or_text)
   #             row_cells[1].text = processed_value
   #             row_cells[0].paragraphs[0].runs[0].bold = True
           
   #         for index, uda_data in enumerate(processed_udas): # Usa i dati processati
   #             document.add_heading(f'UdA n. {index + 1}: {uda_data["title"]}', level=2)
   #             table_details = document.add_table(rows=0, cols=2)
   #             table_details.style = 'TableGrid'
   #             table_details.alignment = WD_TABLE_ALIGNMENT.CENTER
   #             table_details.columns[0].width = Inches(2.0)
   #             table_details.columns[1].width = Inches(4.5)

   #             add_table_row_docx(table_details, 'Competenze attese a livello di UdA', uda_data['competences_html'])
   #             add_table_row_docx(table_details, 'Argomenti Uda', uda_data['topics_string'], is_html=False)
   #             add_table_row_docx(table_details, 'Conoscenze ADA (sapere)', uda_data['knowledge_html'])
   #             add_table_row_docx(table_details, 'Abilità-Capacità ADA (saper fare)', uda_data['skills_html'])
   #             add_table_row_docx(table_details, 'Tempi (durata in ore)', f"{uda_data['total_estimated_hours_display']} ore", is_html=False)
   #             add_table_row_docx(table_details, 'Strategie didattiche', uda_data['didactic_strategies_html'])
   #             add_table_row_docx(table_details, 'Materiali e strumenti', uda_data['materials_tools_html'])
   #             add_table_row_docx(table_details, 'Tipo di verifiche', uda_data['assessment_type_html'])
   #             add_table_row_docx(table_details, 'Valutazione', uda_data['evaluation_html'])
   #             add_table_row_docx(table_details, 'Altre Discipline coinvolte', uda_data['other_involved_subjects_display'], is_html=False)
               
   #             # Per DOCX, usa la logica originale per le annotazioni
   #             annotations_text_docx = uda_data['export_specific_annotations_html']
   #             is_html_annotations_docx = bool(uda_data['export_specific_annotations_html'])
   #             if not annotations_text_docx:
   #                 annotations_text_docx = uda_data['description']
   #                 is_html_annotations_docx = False # Description è testo semplice
   #             add_table_row_docx(table_details, 'Annotazioni', annotations_text_docx, is_html=is_html_annotations_docx)

   #             if uda_data['is_civic_education']:
   #                 add_table_row_docx(table_details, 'Educazione Civica', 'Sì, parte del percorso', is_html=False)

   #             if uda_data['lesson_contents']:
   #                 document.add_heading('Lezioni Previste', level=3)
   #                 table_lessons = document.add_table(rows=1, cols=2)
   #                 table_lessons.style = 'TableGrid'
   #                 table_lessons.alignment = WD_TABLE_ALIGNMENT.CENTER
   #                 hdr_cells = table_lessons.rows[0].cells
   #                 hdr_cells[0].text = 'Titolo Lezione'
   #                 hdr_cells[1].text = 'Durata Stimata (ore)'
   #                 hdr_cells[0].paragraphs[0].runs[0].bold = True
   #                 hdr_cells[1].paragraphs[0].runs[0].bold = True
   #                 for lc_data in uda_data['lesson_contents']:
   #                     row_cells_lc = table_lessons.add_row().cells
   #                     row_cells_lc[0].text = lc_data['lesson'].title if lc_data['lesson'] else "Lezione non specificata"
   #                     row_cells_lc[1].text = lc_data['hours_display_pdf'] # Riutilizziamo la stringa formattata
               
   #             document.add_paragraph()
   #             if index < len(processed_udas) - 1:
   #                 document.add_page_break()

   #         file_stream = BytesIO()
   #         document.save(file_stream)
   #         file_stream.seek(0)
   #         response = HttpResponse(
   #             file_stream.read(),
   #             content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
   #         )
   #         filename_docx = f"export_udas_{course_name_sanitized}.docx"
   #         # La rimozione dell'underscore finale è già gestita da course_name_sanitized
   #         response['Content-Disposition'] = f'attachment; filename="{filename_docx}"'
   #         return response

   @action(detail=True, methods=['get'], url_path='export-udas-docx')
   def export_udas_docx(self, request, pk=None):
       logger.info(f"EXPORT_UDAS_DOCX CALLED FOR COURSE PK: {pk}")
       course = self.get_object()
       udas_queryset = UDA.objects.filter(course=course).order_by('order_in_course', 'title')

       processed_udas = []
       for uda_instance in udas_queryset:
           # Calcolo corretto di total_estimated_hours_val considerando tutti i contenuti
           total_estimated_hours_val = 0
           # Itera su TUTTI i contenuti dell'UDA
           for content in uda_instance.contents.all().select_related('lesson'): # .all() per tutti i tipi
               hours_to_add = None
               if content.estimated_hours is not None:
                   hours_to_add = content.estimated_hours
               # Applica il fallback SOLO se il contenuto è di tipo LESSON e UDAContent.estimated_hours è None
               elif content.content_type == 'LESSON' and content.lesson and content.lesson.estimated_hours is not None:
                   hours_to_add = content.lesson.estimated_hours
               
               if hours_to_add is not None:
                   try:
                       total_estimated_hours_val += float(hours_to_add)
                   except (ValueError, TypeError):
                       # Logga l'errore invece di ignorarlo silenziosamente, potrebbe essere utile per il debug
                       logger.warning(f"Impossibile convertire in float le ore stimate '{hours_to_add}' per il contenuto ID {content.id} dell'UDA ID {uda_instance.id}")
                       pass

           try:
               # Gestione della visualizzazione di total_estimated_hours_display
               if not uda_instance.contents.exists(): # Se non ci sono contenuti di alcun tipo
                   total_estimated_hours_display = "N/D"
               elif total_estimated_hours_val > 0:
                   total_estimated_hours_display = f"{float(total_estimated_hours_val):.1f}"
               else: # Ci sono contenuti, ma la somma è 0 (o tutti i valori erano non validi/None)
                   total_estimated_hours_display = "0.0" # Mostra "0.0" se ci sono contenuti ma la somma è zero
           except (ValueError, TypeError): # Fallback generico in caso di problemi imprevisti con float()
               total_estimated_hours_display = "N/D"
               logger.error(f"Errore imprevisto nella formattazione di total_estimated_hours_display per UDA ID {uda_instance.id}", exc_info=True)

           other_subjects_display = uda_instance.other_involved_subjects_text
           if not other_subjects_display and uda_instance.subjects.exists():
               other_subjects_display = ", ".join([s.name for s in uda_instance.subjects.all()])
           
           lesson_contents_for_template = []
           lesson_contents_queryset = uda_instance.contents.filter(content_type='LESSON').select_related('lesson')
           if lesson_contents_queryset.exists():
               for lc in lesson_contents_queryset:
                   hours_to_display_lc = None
                   if lc.estimated_hours is not None:
                       hours_to_display_lc = lc.estimated_hours
                   elif lc.lesson and lc.lesson.estimated_hours is not None:
                       hours_to_display_lc = lc.lesson.estimated_hours
                   
                   lc_hours_text = "N/D"
                   if hours_to_display_lc is not None:
                       try:
                           lc_hours_text = f"{float(hours_to_display_lc):.1f}"
                       except (ValueError, TypeError):
                           lc_hours_text = "N/D (err)"
                   lesson_contents_for_template.append({
                       'lesson': lc.lesson,
                       'hours_display_pdf': lc_hours_text # Questo nome può rimanere o essere reso più generico
                   })

           processed_udas.append({
               'title': uda_instance.title,
               'competences_html': uda_instance.competences_html,
               'topics_string': ", ".join([topic.name for topic in uda_instance.topics.all()]),
               'knowledge_html': uda_instance.knowledge_html,
               'skills_html': uda_instance.skills_html,
               'total_estimated_hours_display': total_estimated_hours_display,
               'didactic_strategies_html': uda_instance.didactic_strategies_html,
               'materials_tools_html': uda_instance.materials_tools_html,
               'assessment_type_html': uda_instance.assessment_type_html,
               'evaluation_html': uda_instance.evaluation_html,
               'other_involved_subjects_display': other_subjects_display or "N/D",
               'is_civic_education': uda_instance.is_civic_education,
               'lesson_contents': lesson_contents_for_template,
               'description': uda_instance.description,
               'export_specific_annotations_html': uda_instance.export_specific_annotations_html,
           })

       course_name_sanitized = get_valid_filename(course.name)
       if not course_name_sanitized:
           course_name_sanitized = "corso"
       while course_name_sanitized.endswith("_"):
           course_name_sanitized = course_name_sanitized[:-1]
       if not course_name_sanitized:
           course_name_sanitized = "corso"

       document = Document()
       document.add_heading(f'Programmazione Didattica Individuale - UDA del Corso: {course.name}', level=1)
       p_docente = document.add_paragraph()
       p_docente.add_run(f"Docente: {request.user.get_full_name() or request.user.username}").bold = True

       def add_table_row_docx(table, label, value_html_or_text, is_html=True):
           row_cells = table.add_row().cells
           row_cells[0].text = label
           processed_value = "N/D"
           if value_html_or_text:
               if is_html:
                   soup = BeautifulSoup(str(value_html_or_text), 'html.parser')
                   processed_value = soup.get_text(separator='\n', strip=True) or "N/D"
               else:
                   processed_value = str(value_html_or_text)
           row_cells[1].text = processed_value
           row_cells[0].paragraphs[0].runs[0].bold = True
       
       for index, uda_data in enumerate(processed_udas):
           document.add_heading(f'UdA n. {index + 1}: {uda_data["title"]}', level=2)
           table_details = document.add_table(rows=0, cols=2)
           table_details.style = 'TableGrid'
           table_details.alignment = WD_TABLE_ALIGNMENT.CENTER
           table_details.columns[0].width = Inches(2.0)
           table_details.columns[1].width = Inches(4.5)

           add_table_row_docx(table_details, 'Competenze attese a livello di UdA', uda_data['competences_html'])
           add_table_row_docx(table_details, 'Argomenti Uda', uda_data['topics_string'], is_html=False)
           add_table_row_docx(table_details, 'Conoscenze ADA (sapere)', uda_data['knowledge_html'])
           add_table_row_docx(table_details, 'Abilità-Capacità ADA (saper fare)', uda_data['skills_html'])
           add_table_row_docx(table_details, 'Tempi (durata in ore)', f"{uda_data['total_estimated_hours_display']} ore", is_html=False)
           add_table_row_docx(table_details, 'Strategie didattiche', uda_data['didactic_strategies_html'])
           add_table_row_docx(table_details, 'Materiali e strumenti', uda_data['materials_tools_html'])
           add_table_row_docx(table_details, 'Tipo di verifiche', uda_data['assessment_type_html'])
           add_table_row_docx(table_details, 'Valutazione', uda_data['evaluation_html'])
           add_table_row_docx(table_details, 'Altre Discipline coinvolte', uda_data['other_involved_subjects_display'], is_html=False)
           
           annotations_text_docx = uda_data['export_specific_annotations_html']
           is_html_annotations_docx = bool(uda_data['export_specific_annotations_html'])
           if not annotations_text_docx:
               annotations_text_docx = uda_data['description']
               is_html_annotations_docx = False
           add_table_row_docx(table_details, 'Annotazioni', annotations_text_docx, is_html=is_html_annotations_docx)

           if uda_data['is_civic_education']:
               add_table_row_docx(table_details, 'Educazione Civica', 'Sì, parte del percorso', is_html=False)

           if uda_data['lesson_contents']:
               document.add_heading('Lezioni Previste', level=3)
               table_lessons = document.add_table(rows=1, cols=2)
               table_lessons.style = 'TableGrid'
               table_lessons.alignment = WD_TABLE_ALIGNMENT.CENTER
               hdr_cells = table_lessons.rows[0].cells
               hdr_cells[0].text = 'Titolo Lezione'
               hdr_cells[1].text = 'Durata Stimata (ore)'
               hdr_cells[0].paragraphs[0].runs[0].bold = True
               hdr_cells[1].paragraphs[0].runs[0].bold = True
               for lc_data in uda_data['lesson_contents']:
                   row_cells_lc = table_lessons.add_row().cells
                   row_cells_lc[0].text = lc_data['lesson'].title if lc_data['lesson'] else "Lezione non specificata"
                   row_cells_lc[1].text = lc_data['hours_display_pdf']
           
           document.add_paragraph()
           if index < len(processed_udas) - 1:
               document.add_page_break()

       file_stream = BytesIO()
       document.save(file_stream)
       file_stream.seek(0)
       response = HttpResponse(
           file_stream.read(),
           content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
       )
       filename_docx = f"export_udas_{course_name_sanitized}.docx"
       response['Content-Disposition'] = f'attachment; filename="{filename_docx}"'
       return response

   @action(detail=True, methods=['get'], url_path='export-udas-pdf')
   def export_udas_pdf(self, request, pk=None):
       logger.info(f"EXPORT_UDAS_PDF CALLED FOR COURSE PK: {pk}")
       course = self.get_object()
       udas_queryset = UDA.objects.filter(course=course).order_by('order_in_course', 'title')

       processed_udas = []
       for uda_instance in udas_queryset:
           total_estimated_hours_val = uda_instance.contents.aggregate(Sum('estimated_hours'))['estimated_hours__sum'] or 0
           try:
               total_estimated_hours_display = f"{float(total_estimated_hours_val):.1f}"
           except (ValueError, TypeError):
               total_estimated_hours_display = "N/D"

           other_subjects_display = uda_instance.other_involved_subjects_text
           if not other_subjects_display and uda_instance.subjects.exists():
               other_subjects_display = ", ".join([s.name for s in uda_instance.subjects.all()])
           
           annotations_text_for_pdf = uda_instance.description
           is_html_annotations = False
           if uda_instance.export_specific_annotations_html:
               annotations_text_for_pdf = uda_instance.export_specific_annotations_html
               is_html_annotations = True
           
           lesson_contents_for_template = []
           lesson_contents_queryset = uda_instance.contents.filter(content_type='LESSON').select_related('lesson')
           if lesson_contents_queryset.exists():
               for lc in lesson_contents_queryset:
                   hours_to_display_lc = None
                   if lc.estimated_hours is not None:
                       hours_to_display_lc = lc.estimated_hours
                   elif lc.lesson and lc.lesson.estimated_hours is not None:
                       hours_to_display_lc = lc.lesson.estimated_hours
                   
                   lc_hours_text = "N/D"
                   if hours_to_display_lc is not None:
                       try:
                           lc_hours_text = f"{float(hours_to_display_lc):.1f}"
                       except (ValueError, TypeError):
                           lc_hours_text = "N/D (err)"
                   lesson_contents_for_template.append({
                       'lesson': lc.lesson,
                       'hours_display_pdf': lc_hours_text
                   })

           processed_udas.append({
               'title': uda_instance.title,
               'competences_html': uda_instance.competences_html,
               'topics_string': ", ".join([topic.name for topic in uda_instance.topics.all()]),
               'knowledge_html': uda_instance.knowledge_html,
               'skills_html': uda_instance.skills_html,
               'total_estimated_hours_display': total_estimated_hours_display,
               'didactic_strategies_html': uda_instance.didactic_strategies_html,
               'materials_tools_html': uda_instance.materials_tools_html,
               'assessment_type_html': uda_instance.assessment_type_html,
               'evaluation_html': uda_instance.evaluation_html,
               'other_involved_subjects_display': other_subjects_display or "N/D",
               'annotations_display': annotations_text_for_pdf or "N/D",
               'is_html_annotations': is_html_annotations,
               'is_civic_education': uda_instance.is_civic_education,
               'lesson_contents': lesson_contents_for_template,
           })

       course_name_sanitized = get_valid_filename(course.name)
       if not course_name_sanitized:
           course_name_sanitized = "corso"
       while course_name_sanitized.endswith("_"):
           course_name_sanitized = course_name_sanitized[:-1]
       if not course_name_sanitized:
           course_name_sanitized = "corso"

       try:
           context = {
               'course': course,
               'udas': processed_udas,
               'teacher_name': request.user.get_full_name() or request.user.username
           }
           html_string = render_to_string('uda_export/uda_pdf_template.html', context)
           
           pdf_file_stream = BytesIO()
           pdf = pisa.CreatePDF(
               html_string,
               dest=pdf_file_stream,
               encoding='UTF-8'
           )
           pdf_file_stream.seek(0)

           if pdf.err:
               error_messages = "; ".join([str(msg) for msg in pdf.log if msg.level >= pisa.ERROR]) if hasattr(pdf, 'log') else str(pdf.err)
               logger.error(f"Errore pisa.CreatePDF per corso {course.id}: codice {pdf.err} - {error_messages}")
               return HttpResponse(f"Errore durante la generazione del PDF (codice: {pdf.err})", status=500)

           response = HttpResponse(pdf_file_stream.read(), content_type='application/pdf')
           filename = f"export_udas_{course_name_sanitized}.pdf"
           response['Content-Disposition'] = f'attachment; filename="{filename}"'
           return response
       except Exception as e:
           logger.error(f"Eccezione durante la generazione del PDF per corso {course.id}: {e}", exc_info=True)
           return HttpResponse(f"Errore interno del server durante la generazione del PDF: {str(e)}", status=500)

class UDATemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestire i Template UDA (UDATemplate).
    Permette CRUD sui template e gestione dei loro contenuti.
    """
    queryset = UDATemplate.objects.all()
    serializer_class = UDATemplateSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
 
    def get_queryset(self):
        # Filtra i template per mostrare solo quelli del docente loggato
        user = self.request.user
        if user.is_authenticated:
            return UDATemplate.objects.filter(teacher=user)
        return UDATemplate.objects.none() # Nessun template se non autenticato

    def perform_create(self, serializer):
        # Il teacher viene già impostato nel serializer create method
        # serializer.save(teacher=self.request.user)
        serializer.save()

    @action(detail=True, methods=['get', 'post'], serializer_class=UDATemplateContentSerializer, url_path='contents')
    def contents(self, request, pk=None):
        template = self.get_object()
        if request.method == 'GET':
            contents = template.contents.all()
            serializer = UDATemplateContentSerializer(contents, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = UDATemplateContentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(uda_template=template)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get', 'put', 'patch', 'delete'],
            serializer_class=UDATemplateContentSerializer,
            url_path='contents/(?P<content_pk>[^/.]+)')
    def single_content(self, request, pk=None, content_pk=None):
        template = self.get_object()
        try:
            content = template.contents.get(pk=content_pk)
        except UDATemplateContent.DoesNotExist:
            return Response({'error': 'Content not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = UDATemplateContentSerializer(content)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'PATCH']:
            serializer = UDATemplateContentSerializer(content, data=request.data, partial=request.method == 'PATCH')
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            content.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class UDAViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestire le UDA.
    Permette CRUD sulle UDA e gestione dei loro contenuti, incluso il completamento delle attività.
    """
    queryset = UDA.objects.all()
    serializer_class = UDASerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
 
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # Filtra per stato e per corso se forniti come query param
            status_filter = self.request.query_params.get('status')
            course_filter = self.request.query_params.get('course_id')
            
            queryset = UDA.objects.filter(teacher=user)
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            if course_filter:
               try:
                   course_id = int(course_filter)
                   queryset = queryset.filter(course_id=course_id)
               except ValueError:
                   # Ignora il filtro se course_id non è un intero valido
                   pass
           
            # Ordina per corso e poi per ordine all'interno del corso, poi per titolo
            queryset = queryset.order_by('course__name', 'order_in_course', 'title')
            return queryset
        return UDA.objects.none()

    def perform_create(self, serializer):
        # Il teacher viene già impostato nel serializer create method
        # serializer.save(teacher=self.request.user)
        serializer.save()

    @action(detail=True, methods=['get', 'post'], serializer_class=UDAContentSerializer, url_path='contents')
    def contents(self, request, pk=None):
        uda = self.get_object()
        if request.method == 'GET':
            contents = uda.contents.all()
            serializer = UDAContentSerializer(contents, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = UDAContentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(uda=uda)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get', 'put', 'patch', 'delete'],
            serializer_class=UDAContentSerializer,
            url_path='contents/(?P<content_pk>[^/.]+)')
    def single_content(self, request, pk=None, content_pk=None):
        uda = self.get_object()
        try:
            content = uda.contents.get(pk=content_pk)
        except UDAContent.DoesNotExist:
            return Response({'error': 'Content not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = UDAContentSerializer(content)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'PATCH']:
            serializer = UDAContentSerializer(content, data=request.data, partial=request.method == 'PATCH')
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            content.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['patch'],
            url_path='contents/(?P<content_pk>[^/.]+)/complete-activity')
    def complete_activity(self, request, pk=None, content_pk=None):
        uda = self.get_object()
        try:
            content = uda.contents.get(pk=content_pk, content_type='ACTIVITY')
        except UDAContent.DoesNotExist:
            return Response({'error': 'Activity content not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        content.activity_completed = True
        content.save(update_fields=['activity_completed'])
        serializer = UDAContentSerializer(content)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'],
            url_path='contents/(?P<content_pk>[^/.]+)/update-teacher-completion')
    def update_teacher_completion(self, request, pk=None, content_pk=None):
        uda = self.get_object()
        try:
            content = uda.contents.get(pk=content_pk)
        except UDAContent.DoesNotExist:
            return Response({'error': 'Content not found.'}, status=status.HTTP_404_NOT_FOUND)

        completed = request.data.get('completed')
        if not isinstance(completed, bool):
            return Response({'error': "'completed' field must be a boolean."}, status=status.HTTP_400_BAD_REQUEST)

        content.teacher_marked_completed = completed
        content.save(update_fields=['teacher_marked_completed'])
        serializer = UDAContentSerializer(content)
        return Response(serializer.data)
    @action(detail=True, methods=['post'], url_path='contents/reorder')
    def reorder_contents(self, request, pk=None):
        """
        Riordina i contenuti (UDAContent) di una specifica UDA.
        Si aspetta una lista di ID di contenuti nell'ordine desiderato nel body della richiesta:
        { "content_ids": [3, 1, 2] }
        """
        uda = self.get_object() # Ottiene l'UDA, il permesso IsOwnerOrReadOnly è già applicato
        content_ids = request.data.get('content_ids', [])

        if not isinstance(content_ids, list):
            return Response({'error': 'content_ids must be a list.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica che tutti gli ID siano interi
        try:
            content_ids = [int(cid) for cid in content_ids]
        except (ValueError, TypeError):
            return Response({'error': 'All content_ids must be valid integers.'}, status=status.HTTP_400_BAD_REQUEST)

        # Recupera tutti i contenuti attuali dell'UDA per verifica
        current_contents = uda.contents.all()
        current_content_map = {content.id: content for content in current_contents}
        current_content_ids_set = set(current_content_map.keys())
        provided_content_ids_set = set(content_ids)

        # Verifica che tutti gli ID forniti appartengano effettivamente a questa UDA
        if not provided_content_ids_set.issubset(current_content_ids_set):
            invalid_ids = list(provided_content_ids_set - current_content_ids_set)
            return Response({'error': f'Invalid or non-existent content IDs for this UDA: {invalid_ids}'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Verifica che tutti i contenuti dell'UDA siano presenti nella lista fornita
        if current_content_ids_set != provided_content_ids_set:
            missing_ids = list(current_content_ids_set - provided_content_ids_set)
            return Response({'error': f'Missing content IDs in the provided list: {missing_ids}'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Aggiorna l'ordine
        # Usiamo un ciclo per aggiornare l'ordine. Per performance su liste molto grandi,
        # si potrebbero considerare strategie diverse, ma per un numero tipico di contenuti UDA
        # questo approccio è generalmente accettabile.
        updated_count = 0
        for index, content_id in enumerate(content_ids):
            content_to_update = current_content_map[content_id]
            new_order = index + 1 # L'ordine è 1-based
            if content_to_update.order != new_order:
                content_to_update.order = new_order
                content_to_update.save(update_fields=['order'])
                updated_count += 1

        # Restituisce i contenuti riordinati
        # Ricarica i contenuti dall'UDA per assicurarsi che l'ordine sia corretto
        reordered_contents = uda.contents.order_by('order')
        serializer = UDAContentSerializer(reordered_contents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='copy')
    @transaction.atomic # Assicura che l'intera operazione di copia sia atomica
    def copy_uda(self, request, pk=None):
        """
        Crea una copia di una UDA esistente, inclusi i suoi contenuti.
        La nuova UDA non sarà associata a nessun corso.
        """
        original_uda = self.get_object() # Ottiene l'UDA originale, permessi già controllati

        # Crea la nuova UDA
        new_uda = UDA.objects.create(
            teacher=request.user,
            title=f"Copia di {original_uda.title}",
            description=original_uda.description,
            start_date=original_uda.start_date,
            end_date=original_uda.end_date,
            status='TODO',  # O lo stato originale, o uno di default come 'TODO'
            course=None, # Non associata a un corso inizialmente
            order_in_course=None,
            source_template=None # Non deriva da un template
        )

        # Copia le relazioni ManyToMany (subjects e topics)
        new_uda.subjects.set(original_uda.subjects.all())
        new_uda.topics.set(original_uda.topics.all())

        # Copia i contenuti
        original_contents = original_uda.contents.all().order_by('order')
        for original_content in original_contents:
            UDAContent.objects.create(
                uda=new_uda,
                content_type=original_content.content_type,
                lesson=original_content.lesson,
                quiz_template=original_content.quiz_template,
                note_title=original_content.note_title,
                note_content=original_content.note_content,
                activity_title=original_content.activity_title,
                activity_description=original_content.activity_description,
                activity_attachment_url=original_content.activity_attachment_url, # Assicurati che la gestione del file sia appropriata (potrebbe richiedere la copia del file fisico se non è solo un URL)
                activity_completed=False, # Reset per la nuova UDA
                teacher_marked_completed=False, # Reset per la nuova UDA
                order=original_content.order,
                estimated_hours=original_content.estimated_hours
            )
        
        # Serializza e restituisci la nuova UDA
        # È importante ricaricare la new_uda per includere i contenuti appena creati se il serializer li gestisce come nested
        new_uda.refresh_from_db()
        serializer = UDASerializer(new_uda, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
