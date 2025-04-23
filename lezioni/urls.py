from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers # Importa router annidati

# Importa le view definite
from .views import (
    SubjectViewSet,
    TopicViewSet,
    LessonViewSet,
    LessonContentViewSet,
    LessonAssignmentViewSet
)

app_name = 'lezioni'

# Router principale per le risorse di primo livello
router = DefaultRouter()
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'topics', TopicViewSet, basename='topic')
router.register(r'lessons', LessonViewSet, basename='lesson') # Include azioni custom come /assign e /contents
router.register(r'assignments', LessonAssignmentViewSet, basename='lessonassignment') # Per listare/recuperare assegnazioni

# Router annidato per i contenuti delle lezioni
# Crea un router annidato sotto 'lessons' (identificato da 'lesson_pk')
lessons_router = routers.NestedSimpleRouter(router, r'lessons', lookup='lesson')
# Registra il ViewSet per i contenuti all'interno del router annidato
# L'URL sarà del tipo /api/lezioni/lessons/{lesson_pk}/contents/
lessons_router.register(r'contents', LessonContentViewSet, basename='lesson-content')


urlpatterns = [
    # Include gli URL generati dal router principale
    path('', include(router.urls)),
    # Include gli URL generati dal router annidato per i contenuti
    path('', include(lessons_router.urls)),

    # Eventuali URL specifici non gestiti dai router possono essere aggiunti qui
    # Ad esempio, se avessimo endpoint specifici per studenti/docenti non legati a un ViewSet standard.
    # path('student/assigned-lessons/', StudentAssignedLessonsView.as_view(), name='student-assigned-lessons'),
]

# Il risultato finale includerà URL come:
# /api/lezioni/subjects/
# /api/lezioni/topics/
# /api/lezioni/lessons/
# /api/lezioni/lessons/{lesson_pk}/
# /api/lezioni/lessons/{lesson_pk}/assign/  (Azione custom)
# /api/lezioni/lessons/{lesson_pk}/contents/ (Lista contenuti - dal router annidato)
# /api/lezioni/lessons/{lesson_pk}/contents/{content_pk}/ (Dettaglio contenuto - dal router annidato)
# /api/lezioni/assignments/
# /api/lezioni/assignments/{assignment_pk}/
# /api/lezioni/assignments/{assignment_pk}/mark-viewed/ (Azione custom)