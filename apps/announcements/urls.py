from django.urls import path
from .views import (
    AnnouncementListView,
    MarkAsReadView,
    DoNotShowAgainView,
)

app_name = 'announcements'

urlpatterns = [
    path('', AnnouncementListView.as_view(), name='announcement-list'),
    path('<int:pk>/mark-as-read/', MarkAsReadView.as_view(), name='announcement-mark-as-read'),
    path('<int:pk>/do-not-show-again/', DoNotShowAgainView.as_view(), name='announcement-do-not-show-again'),
]