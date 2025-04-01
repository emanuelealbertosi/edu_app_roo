"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include # Add include
from rest_framework_simplejwt.views import ( # Add these imports
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # API Authentication URLs (Simple JWT)
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # App APIs
    # API Studente (raggruppate sotto /api/student/)
    path('api/student/', include([
        path('', include('apps.users.urls')), # Per login, test-auth, ecc.
        path('', include('apps.education.urls')), # Per dashboard quizzes/pathways, tentativi, ecc.
        path('', include('apps.rewards.urls')), # Per dashboard wallet, shop, acquisti, ecc.
    ])),
    # API Gestione (Docente/Admin) - Manteniamo /api/ per ora
    # Potremmo voler separare meglio in futuro
    path('api/', include('apps.users.urls')), # Gestione utenti
    path('api/rewards/', include('apps.rewards.urls')), # Gestione ricompense
    path('api/education/', include('apps.education.urls')), # Gestione contenuti educativi
]
