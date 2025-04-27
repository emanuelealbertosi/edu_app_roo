from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentGroupViewSet

# Crea un router e registra il nostro ViewSet
router = DefaultRouter()
router.register(r'', StudentGroupViewSet, basename='studentgroup') # Usa prefisso vuoto
# Il basename è importante, specialmente se il queryset nel ViewSet è dinamico o complesso.

# Gli URL API sono ora determinati automaticamente dal router.
# Esempi:
# /api/student-groups/groups/ -> GET (list), POST (create)
# /api/student-groups/groups/{pk}/ -> GET (retrieve), PUT (update), PATCH (partial_update), DELETE (destroy)
# /api/student-groups/groups/{pk}/add-student/ -> POST
# /api/student-groups/groups/{pk}/remove-student/{student_pk}/ -> POST
# /api/student-groups/groups/{pk}/generate-token/ -> POST
# /api/student-groups/groups/{pk}/delete-token/ -> POST

app_name = 'student_groups' # Namespace per gli URL, utile per reverse lookups

urlpatterns = [
    path('', include(router.urls)),
    # Eventuali altri URL specifici dell'app possono essere aggiunti qui
]