from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from lezioni.models import LessonGroup, Lesson
from lezioni.serializers import LessonGroupSerializer
from lezioni.permissions import IsTeacherOwner

class LessonGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet per la gestione dei gruppi di lezioni.
    """
    queryset = LessonGroup.objects.all()
    serializer_class = LessonGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtra i gruppi per mostrare solo quelli creati dall'utente corrente.
        """
        return self.queryset.filter(creator=self.request.user)

    def perform_create(self, serializer):
        """
        Associa l'utente corrente come creatore del gruppo.
        """
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'], url_path='assign-lessons')
    def assign_lessons(self, request, pk=None):
        """
        Azione custom per assegnare una o più lezioni a un gruppo.
        L'ID delle lezioni da assegnare deve essere passato nel body della richiesta.
        Esempio body: { "lesson_ids": [1, 2, 3] }
        """
        group = self.get_object()
        lesson_ids = request.data.get('lesson_ids', [])

        if not isinstance(lesson_ids, list):
            return Response(
                {"detail": "Il campo 'lesson_ids' deve essere una lista di ID."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Controlla che l'utente sia il proprietario delle lezioni che sta cercando di assegnare
        lessons_to_assign = Lesson.objects.filter(id__in=lesson_ids, creator=request.user)
        
        found_lesson_ids = [lesson.id for lesson in lessons_to_assign]
        not_found_ids = set(lesson_ids) - set(found_lesson_ids)

        if not_found_ids:
            return Response(
                {"detail": f"Lezioni non trovate o non autorizzate: {list(not_found_ids)}"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Assegna le lezioni al gruppo
        for lesson in lessons_to_assign:
            lesson.group = group
            lesson.save()

        return Response(
            {"status": f"{len(lessons_to_assign)} lezioni assegnate al gruppo '{group.name}'."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='unassign-lesson')
    def unassign_lesson(self, request, pk=None):
        """
        Azione custom per rimuovere una lezione da questo gruppo.
        L'ID della lezione da rimuovere deve essere passato nel body.
        Esempio body: { "lesson_id": 1 }
        """
        group = self.get_object()
        lesson_id = request.data.get('lesson_id')

        if not lesson_id:
            return Response({"detail": "ID della lezione mancante."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lesson = Lesson.objects.get(id=lesson_id, group=group, creator=request.user)
        except Lesson.DoesNotExist:
            return Response({"detail": "Lezione non trovata in questo gruppo o non autorizzata."}, status=status.HTTP_404_NOT_FOUND)

        lesson.group = None
        lesson.save()

        return Response({"status": f"Lezione '{lesson.title}' rimossa dal gruppo '{group.name}'."}, status=status.HTTP_200_OK)