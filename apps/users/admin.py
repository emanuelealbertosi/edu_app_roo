from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Student

# Definiamo un admin personalizzato per il nostro User model
class UserAdmin(BaseUserAdmin):
    # Aggiungiamo 'role' ai campi visualizzati nella lista e nei form
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'role')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Ruolo', {'fields': ('role',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Ruolo', {'fields': ('role',)}),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

# Registriamo il nostro User model con l'admin personalizzato
admin.site.register(User, UserAdmin)

# Registriamo il modello Student con una configurazione base
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'teacher', 'is_active', 'created_at')
    list_filter = ('is_active', 'teacher')
    search_fields = ('first_name', 'last_name', 'teacher__username')
    ordering = ('last_name', 'first_name')
    # Rendiamo il campo teacher readonly se non si è superuser?
    # readonly_fields = ('created_at',) # Esempio
