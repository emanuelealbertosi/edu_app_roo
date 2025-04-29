from django import forms # Aggiunto import
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Student
# Definiamo un admin personalizzato per il nostro User model
class UserAdmin(BaseUserAdmin):
    # Aggiungiamo 'role' e 'can_create_public_groups' ai campi visualizzati nella lista e nei form
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role', 'can_create_public_groups', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'role', 'can_create_public_groups') # Aggiunto filtro
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Permessi Personalizzati', {'fields': ('role', 'can_create_public_groups')}), # Aggiunto campo al fieldset
    )
    # Non è necessario aggiungerlo ad add_fieldsets se non vogliamo impostarlo alla creazione utente da admin
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Permessi Personalizzati', {'fields': ('role',)}), # Lasciamo solo role qui per ora
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

# Registriamo il nostro User model con l'admin personalizzato
admin.site.register(User, UserAdmin)

# --- Modifiche per StudentAdmin ---

# Form personalizzato per StudentAdmin
class StudentAdminForm(forms.ModelForm):
    # Campo per inserire/modificare il PIN in chiaro
    pin = forms.CharField(
        label='PIN',
        widget=forms.PasswordInput(render_value=False), # Non mostrare il valore precedente
        required=False, # Gestito da get_form in StudentAdmin
        help_text='Inserire un PIN numerico di almeno 4 cifre. Lasciare vuoto per non modificare.'
    )

    class Meta:
        model = Student
        # Escludiamo pin_hash perché lo gestiamo tramite il campo 'pin'
        exclude = ('pin_hash',)
        # Includiamo tutti gli altri campi desiderati nel form (rimosso 'teacher')
        fields = ('student_code', 'pin', 'first_name', 'last_name', 'is_active')

    def clean_pin(self):
        """
        Valida il PIN inserito.
        """
        raw_pin = self.cleaned_data.get('pin')
        is_creation = self.instance.pk is None # Verifica se è una nuova istanza

        # Se è la creazione e il PIN è vuoto (anche se get_form lo imposta required)
        if is_creation and not raw_pin:
             raise forms.ValidationError("Il PIN è obbligatorio per i nuovi studenti.")

        # Se un PIN è stato inserito (sia in creazione che modifica)
        if raw_pin:
            if not raw_pin.isdigit():
                raise forms.ValidationError("Il PIN deve contenere solo cifre.")
            if len(raw_pin) < 4:
                raise forms.ValidationError("Il PIN deve essere di almeno 4 cifre.")
            # La validazione è completa, restituiamo il PIN pulito
        return raw_pin # Restituisce il PIN pulito (o None se non inserito in modifica)


# Registriamo il modello Student con una configurazione personalizzata
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form = StudentAdminForm # Usa il nostro form personalizzato
    # Rimosso 'teacher' da list_display, list_filter, search_fields
    list_display = ('full_name', 'student_code', 'is_active', 'created_at')
    list_filter = ('is_active',) # Rimosso 'teacher'
    search_fields = ('first_name', 'last_name', 'student_code') # Rimosso 'teacher__username'
    ordering = ('last_name', 'first_name')
    # readonly_fields = ('created_at',) # Esempio

    def get_form(self, request, obj=None, **kwargs):
        """
        Sovrascrive get_form per rendere il campo PIN obbligatorio
        solo durante la creazione di un nuovo studente (quando obj is None).
        """
        form = super().get_form(request, obj, **kwargs)
        # Imposta 'required' e help_text dinamicamente
        if obj is None: # Siamo in fase di creazione
            form.base_fields['pin'].required = True
            form.base_fields['pin'].help_text = 'Inserire un PIN numerico di almeno 4 cifre (Obbligatorio).'
        else: # Siamo in fase di modifica
            form.base_fields['pin'].required = False # Non obbligatorio in modifica
            form.base_fields['pin'].help_text = 'Inserire un nuovo PIN numerico di almeno 4 cifre per modificarlo. Lasciare vuoto per mantenere il PIN attuale.'
        return form

    def save_model(self, request, obj, form, change):
        """
        Sovrascrive save_model per impostare l'hash del PIN
        se un nuovo PIN valido è stato fornito nel form.
        """
        # Prendiamo il PIN validato dal form (se fornito)
        raw_pin = form.cleaned_data.get('pin')

        # Se è stato fornito un PIN valido (la validazione è avvenuta in clean_pin),
        # usa il metodo set_pin del modello per impostare l'hash.
        if raw_pin:
            obj.set_pin(raw_pin) # set_pin ora fa solo l'hashing

        # Salva l'oggetto studente (con o senza il PIN aggiornato)
        super().save_model(request, obj, form, change)
