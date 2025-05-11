from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, UDATemplateViewSet, UDAViewSet # Aggiunto CourseViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course') # Aggiunto CourseViewSet
router.register(r'uda-templates', UDATemplateViewSet, basename='udatemplate')
router.register(r'udas', UDAViewSet, basename='uda')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]