from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, UDATemplateViewSet, UDAViewSet, CourseGroupViewSet, UdaGroupViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'course-groups', CourseGroupViewSet, basename='coursegroup')
router.register(r'uda-groups', UdaGroupViewSet, basename='udagroup')
router.register(r'uda-templates', UDATemplateViewSet, basename='udatemplate')
router.register(r'udas', UDAViewSet, basename='uda')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]