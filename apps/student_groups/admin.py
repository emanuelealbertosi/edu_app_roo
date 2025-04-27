from django.contrib import admin
from .models import StudentGroup, StudentGroupMembership

class StudentGroupMembershipInline(admin.TabularInline):
    """Inline per visualizzare/aggiungere membri direttamente dal gruppo."""
    model = StudentGroupMembership
    extra = 1
    autocomplete_fields = ['student'] # Assumendo che l'admin di Student sia registrato e supporti autocomplete
    verbose_name = "Membro del Gruppo"
    verbose_name_plural = "Membri del Gruppo"

@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    """Admin view for Student Groups."""
    list_display = ('name', 'teacher', 'registration_token', 'is_active', 'created_at')
    list_filter = ('is_active', 'teacher')
    search_fields = ('name', 'description', 'teacher__username')
    autocomplete_fields = ['teacher']
    inlines = [StudentGroupMembershipInline]
    readonly_fields = ('created_at',)
    # Azione per generare/eliminare token?
    actions = ['generate_registration_tokens', 'delete_registration_tokens']

    @admin.action(description='Genera token di registrazione per i gruppi selezionati')
    def generate_registration_tokens(self, request, queryset):
        count = 0
        for group in queryset:
            group.generate_token() # Usa il metodo del modello
            count += 1
        self.message_user(request, f'{count} token di registrazione generati/aggiornati.')

    @admin.action(description='Elimina token di registrazione per i gruppi selezionati')
    def delete_registration_tokens(self, request, queryset):
        count = queryset.update(registration_token=None)
        self.message_user(request, f'{count} token di registrazione eliminati.')

@admin.register(StudentGroupMembership)
class StudentGroupMembershipAdmin(admin.ModelAdmin):
    """Admin view for managing group memberships directly (optional)."""
    list_display = ('student', 'group', 'joined_at')
    list_filter = ('group', 'joined_at')
    search_fields = ('student__first_name', 'student__last_name', 'group__name')
    autocomplete_fields = ['student', 'group']
    readonly_fields = ('joined_at',)

# Nota: Assicurarsi che l'admin per il modello Student (in apps.users.admin)
# abbia 'search_fields' configurato per permettere l'autocomplete.