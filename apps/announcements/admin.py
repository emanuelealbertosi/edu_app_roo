from django.contrib import admin
from .models import Announcement, UserAnnouncementView

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_audience', 'is_active', 'is_important', 'created_at')
    list_filter = ('is_active', 'is_important', 'target_audience')
    search_fields = ('title', 'content')
    ordering = ('-is_important', '-created_at')

@admin.register(UserAnnouncementView)
class UserAnnouncementViewAdmin(admin.ModelAdmin):
    list_display = ('announcement', 'user', 'student', 'do_not_show_again', 'last_viewed_at')
    list_filter = ('do_not_show_again', 'announcement')
    search_fields = ('user__username', 'student__student_code', 'announcement__title')
    readonly_fields = ('first_viewed_at', 'last_viewed_at')