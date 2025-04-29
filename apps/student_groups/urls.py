from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Importa anche la nuova vista
from .views import StudentGroupViewSet, PublicGroupsListView, GroupAccessRequestViewSet

# Crea un router e registra i ViewSet che seguono lo schema REST standard
router = DefaultRouter()
router.register(r'groups', StudentGroupViewSet, basename='studentgroup') # Usa 'groups' come prefisso
# Registra anche il ViewSet per le richieste di accesso
router.register(r'access-requests', GroupAccessRequestViewSet, basename='groupaccessrequest')

# Il basename è importante, specialmente se il queryset nel ViewSet è dinamico o complesso.

# Gli URL API sono ora determinati automaticamente dal router.
# Esempi:
# /api/student-groups/groups/ -> GET (list), POST (create)
# /api/student-groups/groups/{pk}/ -> GET (retrieve), PUT (update), PATCH (partial_update), DELETE (destroy)
# /api/student-groups/groups/{pk}/students/ -> GET
# /api/student-groups/groups/{pk}/add-student/ -> POST
# /api/student-groups/groups/{pk}/remove-student/{student_pk}/ -> POST
# /api/student-groups/groups/{pk}/generate-token/ -> POST
# /api/student-groups/groups/{pk}/delete-token/ -> DELETE
# /api/student-groups/groups/{pk}/access-requests/ -> GET (per owner)
# /api/student-groups/groups/{pk}/respond-request/ -> POST (per owner)
# /api/student-groups/access-requests/ -> GET (list proprie), POST (create)
# /api/student-groups/access-requests/{pk}/ -> GET (retrieve propria)

app_name = 'student_groups' # Namespace per gli URL, utile per reverse lookups

urlpatterns = [
    # Include gli URL generati dal router
    path('', include(router.urls)),
    # Aggiungi l'URL specifico per la lista dei gruppi pubblici
    path('public/', PublicGroupsListView.as_view(), name='public-group-list'),
]