from django.contrib import admin
from django.db import models # Import models
from django_json_widget.widgets import JSONEditorWidget # Import the widget
from .models import (
    Wallet, PointTransaction, RewardTemplate, Reward,
    RewardStudentSpecificAvailability, RewardPurchase,
    Badge, EarnedBadge # Aggiunto Badge e EarnedBadge
)

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('student', 'current_points')
    search_fields = ('student__first_name', 'student__last_name')
    readonly_fields = ('student', 'current_points') # Gestito internamente

@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'points_change', 'reason', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('wallet__student__first_name', 'wallet__student__last_name', 'reason')
    readonly_fields = ('wallet', 'points_change', 'reason', 'timestamp') # Solo visualizzazione

# Inline per mostrare la disponibilità specifica direttamente nella Reward
class RewardStudentSpecificAvailabilityInline(admin.TabularInline):
    model = RewardStudentSpecificAvailability
    extra = 1 # Numero di righe vuote da mostrare
    autocomplete_fields = ['student'] # Rende più facile selezionare studenti

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'type', 'cost_points', 'availability_type', 'is_active')
    list_filter = ('type', 'availability_type', 'is_active', 'teacher')
    search_fields = ('name', 'description', 'teacher__username')
    autocomplete_fields = ['teacher', 'template'] # Se si hanno molti template/docenti
    inlines = [RewardStudentSpecificAvailabilityInline] # Mostra la M2M inline
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
    readonly_fields = ('points_spent', 'purchased_at') # Campi gestiti automaticamente/dal docente
    list_select_related = ('student', 'reward', 'delivered_by') # Ottimizzazione query

    # Azione per marcare come consegnato?
    # def mark_delivered_action(modeladmin, request, queryset):
    #     queryset.update(status=RewardPurchase.PurchaseStatus.DELIVERED, delivered_by=request.user, delivered_at=timezone.now())
    # mark_delivered_action.short_description = "Mark selected purchases as delivered"
    # actions = [mark_delivered_action]

# Non registriamo RewardStudentSpecificAvailability direttamente, è gestito dall'inline.

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_thumbnail', 'trigger_type', 'is_active', 'created_at') # Aggiunto image_thumbnail
    list_filter = ('trigger_type', 'is_active')
    search_fields = ('name', 'description')
    # Definisci i campi mostrati nel form di modifica/creazione
    fields = ('name', 'description', 'image', 'trigger_type', 'trigger_condition', 'is_active')
    readonly_fields = ('image_thumbnail',) # Mostra anteprima ma non renderla modificabile direttamente qui
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

    # Metodo per mostrare un'anteprima dell'immagine nella lista
    @admin.display(description='Image Preview')
    def image_thumbnail(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "No Image"

@admin.register(EarnedBadge)
class EarnedBadgeAdmin(admin.ModelAdmin):
    list_display = ('student', 'badge', 'earned_at')
    list_filter = ('earned_at', 'badge')
    search_fields = ('student__first_name', 'student__last_name', 'badge__name')
    autocomplete_fields = ['student', 'badge']
    readonly_fields = ('student', 'badge', 'earned_at') # Record creato automaticamente
