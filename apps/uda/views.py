from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated # Permesso base, da affinare
from rest_framework import permissions # Per IsOwnerOrReadOnly
from django.db import transaction # Per operazioni atomiche

from .models import Course, UDATemplate, UDA, UDAContent, UDATemplateContent # Aggiunto Course
from .serializers import (
   CourseSerializer, UDATemplateSerializer, UDASerializer, # Aggiunto CourseSerializer
   UDAContentSerializer, UDATemplateContentSerializer
)

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
