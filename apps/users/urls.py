from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Importa le viste necessarie
from .views import (
    UserViewSet,
    StudentViewSet,
    StudentGroupViewSet,
    StudentLoginView,
    StudentProtectedTestView,
    TeacherStudentProgressSummaryView,
    TeacherDashboardDataView,
    # Viste per registrazione con token
    StudentRegistrationTokenViewSet,
    ValidateStudentRegistrationTokenView,
    StudentSelfRegisterView
)

# Crea un router e registra le nostre viewset
router = DefaultRouter()
router.register(r'admin/users', UserViewSet, basename='admin-user')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'teacher/groups', StudentGroupViewSet, basename='teacher-group')
# ViewSet per i token di registrazione (gestiti dal docente)
router.register(r'teacher/registration-tokens', StudentRegistrationTokenViewSet, basename='teacher-registration-token')

# Gli URL dell'API sono determinati automaticamente dal router.
# Aggiungiamo URL specifici per le azioni non coperte dal router.
urlpatterns = [
    path('', include(router.urls)), # Include le URL del router

    # --- Autenticazione Studente ---
    path('auth/student/login/', StudentLoginView.as_view(), name='student-login'),
    path('student/test-auth/', StudentProtectedTestView.as_view(), name='student-test-auth'), # Test autenticazione

    # --- Viste Docente ---
    path('teacher/student-progress-summary/', TeacherStudentProgressSummaryView.as_view(), name='teacher-student-progress-summary'),
    path('teacher/dashboard-data/', TeacherDashboardDataView.as_view(), name='teacher-dashboard-data'),

    # --- Registrazione Studente con Token (Pubbliche) ---
    # Valida un token (GET)
    # Modificato per accettare stringa, la validazione UUID avviene nella view
    path('register/validate-token/<str:token>/', ValidateStudentRegistrationTokenView.as_view(), name='validate-registration-token'),
    # Completa la registrazione (POST)
    path('register/complete/', StudentSelfRegisterView.as_view(), name='student-self-register'),
]