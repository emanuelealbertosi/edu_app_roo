from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Importa anche le view di test e registrazione
from .views import (
    UserViewSet, StudentViewSet, StudentLoginView, StudentProtectedTestView,
    TeacherStudentProgressSummaryView, RegistrationTokenViewSet, StudentRegistrationView, # Aggiunte nuove viste
    StudentTokenRefreshView, # Aggiunta view refresh studente
    UserDataExportView, # Aggiunta view per export dati GDPR
    StudentProfileUpdateView, # Aggiunta view per aggiornamento profilo studente GDPR
    UserDataDeletionRequestView, # Aggiunta view per richiesta cancellazione dati GDPR
    ParentalConsentVerificationView # Aggiunta view per verifica consenso parentale
)

# Crea un router e registra le nostre viewset
router = DefaultRouter()
# Nota: Usiamo 'admin/users' per la gestione utenti da parte dell'admin
# e 'students' per la gestione studenti da parte del docente/admin.
router.register(r'admin/users', UserViewSet, basename='admin-user') # Endpoint per Admin
router.register(r'students', StudentViewSet, basename='student') # Endpoint per Docente/Admin
# Endpoint per Docente per gestire i token di registrazione
router.register(r'teacher/registration-tokens', RegistrationTokenViewSet, basename='teacher-registration-token')

# Gli URL dell'API sono determinati automaticamente dal router.
urlpatterns = [
    path('', include(router.urls)),
    # URL specifico per il login studente
    path('auth/student/login/', StudentLoginView.as_view(), name='student-login'),
    # URL per la view di test protetta per studenti
    path('student/test-auth/', StudentProtectedTestView.as_view(), name='student-test-auth'),
    # URL specifico per il sommario progressi studenti (per Docente)
    path('teacher/student-progress-summary/', TeacherStudentProgressSummaryView.as_view(), name='teacher-student-progress-summary'),
    # URL pubblico per la registrazione studente tramite token
    path('register/student/', StudentRegistrationView.as_view(), name='student-register-token'),
    # URL specifico per il refresh del token studente
    path('auth/student/token/refresh/', StudentTokenRefreshView.as_view(), name='student-token-refresh'),
    # URL per GDPR - Diritto di Accesso
    path('profile/my-data/', UserDataExportView.as_view(), name='user-data-export'),
    # URL per GDPR - Diritto di Rettifica (Profilo Studente)
    path('profile/me/', StudentProfileUpdateView.as_view(), name='student-profile-update'),
    # URL per GDPR - Diritto alla Cancellazione (Richiesta)
    path('profile/request-deletion/', UserDataDeletionRequestView.as_view(), name='user-data-deletion-request'),
    # URL pubblico per la verifica del consenso parentale tramite token
    path('verify/parental-consent/<uuid:token>/', ParentalConsentVerificationView.as_view(), name='parental_consent_verify'),
]