from rest_framework import serializers
from .models import Announcement, UserAnnouncementView

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'

class UserAnnouncementViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnnouncementView
        fields = '__all__'