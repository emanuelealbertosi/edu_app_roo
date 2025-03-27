from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, StudentViewSet, StudentLoginView # Importa la nuova view

# Crea un router e registra le nostre viewset
router = DefaultRouter()
# Nota: Usiamo 'admin/users' per la gestione utenti da parte dell'admin
# e 'students' per la gestione studenti da parte del docente/admin.
router.register(r'admin/users', UserViewSet, basename='admin-user') # Endpoint per Admin
router.register(r'students', StudentViewSet, basename='student') # Endpoint per Docente/Admin

# Gli URL dell'API sono determinati automaticamente dal router.
urlpatterns = [
    path('', include(router.urls)),
    # URL specifico per il login studente
    path('auth/student/login/', StudentLoginView.as_view(), name='student-login'),
]