from django.contrib import admin
from django.db import models # Import models
from django_json_widget.widgets import JSONEditorWidget # Import the widget
from .models import (
    Wallet, PointTransaction, RewardTemplate, Reward,
    RewardAvailability, RewardPurchase, # Sostituito RewardStudentSpecificAvailability con RewardAvailability
    Badge, EarnedBadge # Aggiunto Badge e EarnedBadge
)
# import os # Non più necessario qui per BadgeMediaFileAdmin
# from django.conf import settings # Non più necessario qui per BadgeMediaFileAdmin
# from django.contrib import messages # Non più necessario qui per BadgeMediaFileAdmin
from django.utils.html import format_html # Ancora usato da BadgeAdmin

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('student', 'current_points')
    search_fields = ('student__first_name', 'student__last_name')
    # readonly_fields = ('student',) # 'current_points' reso modificabile
    # Nota: Modificare 'current_points' manualmente non crea una PointTransaction.

@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'points_change', 'reason', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('wallet__student__first_name', 'wallet__student__last_name', 'reason')
    readonly_fields = ('wallet', 'points_change', 'reason', 'timestamp') # Solo visualizzazione

# Rimosso RewardStudentSpecificAvailabilityInline

# Inline per mostrare/gestire la disponibilità specifica (studenti/gruppi) direttamente nella Reward
class RewardAvailabilityInline(admin.TabularInline):
    model = RewardAvailability
    extra = 1 # Numero di righe vuote da mostrare
    # Aggiungere autocomplete per student e group se si hanno molti record
    autocomplete_fields = ['student', 'group']
    verbose_name = "Disponibilità Manuale (Studente/Gruppo)"
    verbose_name_plural = "Disponibilità Manuali (Studenti/Gruppi)"
    # Mostra solo i campi rilevanti
    fields = ('student', 'group', 'made_available_at')
    readonly_fields = ('made_available_at',)

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'type', 'cost_points', 'availability_type', 'is_active')
    list_filter = ('type', 'availability_type', 'is_active', 'teacher')
    search_fields = ('name', 'description', 'teacher__username')
    autocomplete_fields = ['teacher', 'template'] # Se si hanno molti template/docenti
    inlines = [RewardAvailabilityInline] # Usa la nuova inline
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    # Potremmo aggiungere logica per mostrare/nascondere l'inline in base a availability_type
    # def get_inlines(self, request, obj=None):
    #     if obj and obj.availability_type == Reward.AvailabilityType.SPECIFIC_STUDENTS:
    #         return [RewardStudentSpecificAvailabilityInline]
    #     return []

@admin.register(RewardTemplate)
class RewardTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'scope', 'type')
    list_filter = ('scope', 'type', 'creator')
    search_fields = ('name', 'description', 'creator__username')
    autocomplete_fields = ['creator']
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

@admin.register(RewardPurchase)
class RewardPurchaseAdmin(admin.ModelAdmin):
    list_display = ('student', 'reward', 'points_spent', 'status', 'purchased_at', 'delivered_by', 'delivered_at')
    list_filter = ('status', 'purchased_at', 'delivered_at', 'reward__type')
    search_fields = ('student__first_name', 'student__last_name', 'reward__name', 'delivered_by__username')
    autocomplete_fields = ['student', 'reward', 'delivered_by']
    # readonly_fields = () # Resi modificabili per correzioni manuali
    # Nota: Modificare 'points_spent' o 'purchased_at' può creare incongruenze.
    list_select_related = ('student', 'reward', 'delivered_by') # Ottimizzazione query

    # Azione per marcare come consegnato?
    # def mark_delivered_action(modeladmin, request, queryset):
    #     queryset.update(status=RewardPurchase.PurchaseStatus.DELIVERED, delivered_by=request.user, delivered_at=timezone.now())
    # mark_delivered_action.short_description = "Mark selected purchases as delivered"
    # actions = [mark_delivered_action]

# Non registriamo RewardAvailability direttamente, è gestito dall'inline.

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'file_preview', 'media_type', 'thumbnail_preview', 'trigger_type', 'is_active', 'created_at')
    list_filter = ('trigger_type', 'is_active', 'media_type')
    search_fields = ('name', 'description')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Media', {
            'fields': ('file', 'file_preview_in_form', 'media_type', 'thumbnail', 'thumbnail_preview_in_form')
        }),
        ('Trigger', {
            'fields': ('trigger_type', 'trigger_condition')
        }),
    )
    readonly_fields = ('media_type', 'file_preview_in_form', 'thumbnail_preview_in_form')
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    @admin.display(description='File Preview')
    def file_preview(self, obj):
        from django.utils.html import format_html
        if obj.file:
            if obj.media_type == obj.MediaType.VIDEO_MP4:
                return format_html(
                    '<video src="{}" controls style="max-height: 60px; max-width: 100px;"><a href="{}">Download</a></video>',
                    obj.file.url, obj.file.url
                )
            elif obj.media_type in [obj.MediaType.IMAGE_STATIC, obj.MediaType.IMAGE_GIF]:
                return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.file.url)
        return "No File"
    
    @admin.display(description='Current File')
    def file_preview_in_form(self, obj): # Usato nel form
        return self.file_preview(obj)

    @admin.display(description='Thumbnail Preview')
    def thumbnail_preview(self, obj):
        from django.utils.html import format_html
        if obj.thumbnail:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.thumbnail.url)
        return "No Thumbnail"

    @admin.display(description='Current Thumbnail')
    def thumbnail_preview_in_form(self, obj): # Usato nel form
        return self.thumbnail_preview(obj)

@admin.register(EarnedBadge)
class EarnedBadgeAdmin(admin.ModelAdmin):
    list_display = ('student', 'badge', 'earned_at')
    list_filter = ('earned_at', 'badge')
    search_fields = ('student__first_name', 'student__last_name', 'badge__name')
    autocomplete_fields = ['student', 'badge']
    # readonly_fields = () # Resi modificabili per correzioni manuali
    # Nota: Modificare questi campi può creare incongruenze storiche.
