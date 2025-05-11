from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated # Permesso base, da affinare
from rest_framework import permissions # Per IsOwnerOrReadOnly

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
