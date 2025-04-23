# Questo file rende 'views' un package Python e
# può essere usato per importare/esportare le classi ViewSet.

# Importa le classi ViewSet dai moduli specifici
from .subject_views import SubjectViewSet
from .topic_views import TopicViewSet
from .lesson_views import LessonViewSet, LessonContentViewSet
from .assignment_views import LessonAssignmentViewSet

# Esporta le classi per l'uso in urls.py
__all__ = [
    'SubjectViewSet',
    'TopicViewSet',
    'LessonViewSet',
    'LessonContentViewSet',
    'LessonAssignmentViewSet',
]