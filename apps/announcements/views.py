from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Announcement, UserAnnouncementView
from .serializers import AnnouncementSerializer
from apps.users.models import Student, User

class AnnouncementListView(generics.ListAPIView):
    """
    API view to retrieve a list of active announcements for the current user.
    
    - Filters announcements based on the user's role (Teacher or Student).
    - Excludes announcements that the user has marked as "do not show again".
    - Orders announcements by importance and creation date (as per model's Meta).
    """
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Determine if the authenticated user is a Student or a User (Teacher/Admin)
        is_student = isinstance(user, Student)
        
        # Get IDs of announcements the user has chosen not to see again
        if is_student:
            hidden_announcements_ids = UserAnnouncementView.objects.filter(
                student=user,
                do_not_show_again=True
            ).values_list('announcement_id', flat=True)
            # Filter for audience: ALL or STUDENTS
            audience_filter = Q(target_audience='ALL') | Q(target_audience='STUDENTS')
        else: # It's a User (Teacher/Admin)
            hidden_announcements_ids = UserAnnouncementView.objects.filter(
                user=user,
                do_not_show_again=True
            ).values_list('announcement_id', flat=True)
            # Filter for audience: ALL or TEACHERS
            audience_filter = Q(target_audience='ALL') | Q(target_audience='TEACHERS')

        # Build the final queryset
        queryset = Announcement.objects.filter(
            is_active=True
        ).filter(
            audience_filter
        ).exclude(
            id__in=hidden_announcements_ids
        )
        
        return queryset

class MarkAnnouncementBaseView(APIView):
    """
    Base class for views that mark an announcement for a user.
    Handles getting the announcement and identifying the user type.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        announcement = get_object_or_404(Announcement, pk=pk)
        user = self.request.user
        is_student = isinstance(user, Student)
        
        view_data = {
            'announcement': announcement,
            'user': user if not is_student else None,
            'student': user if is_student else None,
        }
        
        self.handle_action(view_data)
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    def handle_action(self, view_data):
        raise NotImplementedError("Subclasses must implement this method.")


class MarkAsReadView(MarkAnnouncementBaseView):
    """
    Marks an announcement as read by the user for the current session.
    This creates a view record without setting 'do_not_show_again'.
    This can be used by the client to not show the same announcement again
    during the same login session.
    """
    def handle_action(self, view_data):
        # get_or_create ensures we don't create duplicate records for the same view action.
        UserAnnouncementView.objects.get_or_create(
            announcement=view_data['announcement'],
            user=view_data['user'],
            student=view_data['student'],
            defaults={'do_not_show_again': False} # Explicitly set default
        )


class DoNotShowAgainView(MarkAnnouncementBaseView):
    """
    Marks an announcement to not be shown again to the user permanently.
    This creates or updates a view record, setting 'do_not_show_again' to True.
    """
    def handle_action(self, view_data):
        # Use update_or_create to set the flag, creating the record if it doesn't exist.
        UserAnnouncementView.objects.update_or_create(
            announcement=view_data['announcement'],
            user=view_data['user'],
            student=view_data['student'],
            defaults={'do_not_show_again': True}
        )