from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.users.models import Student, UserRole # Importa UserRole
from .models import StudentGroup, StudentGroupMembership, GroupAccessRequest # Importa GroupAccessRequest
from django.utils.translation import gettext_lazy as _ # Import per traduzioni
import secrets # Per generare il token

User = get_user_model()

class StudentBasicSerializer(serializers.ModelSerializer):
    """Serializer minimale per lo studente."""
    class Meta:
        model = Student
        fields = ['id', 'student_code', 'first_name', 'last_name'] # Corretto: unique_identifier -> student_code

class StudentGroupMembershipSerializer(serializers.ModelSerializer):
    """Serializer per la membership di uno studente a un gruppo."""
    student = StudentBasicSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), source='student', write_only=True
    )

    class Meta:
        model = StudentGroupMembership
        fields = ['id', 'student', 'student_id', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class StudentGroupSerializer(serializers.ModelSerializer):
    """Serializer per il modello StudentGroup."""
    # Sostituito teacher con owner
    owner = serializers.PrimaryKeyRelatedField(read_only=True, help_text="ID del docente proprietario del gruppo.")
    owner_name = serializers.SerializerMethodField(help_text="Nome completo del docente proprietario.") # NUOVO CAMPO
    members = StudentGroupMembershipSerializer(source='memberships', many=True, read_only=True) # Aggiornato source a 'memberships'
    student_count = serializers.SerializerMethodField()
    # Aggiunto campo per contare le richieste pendenti (solo per owner)
    pending_requests_count = serializers.SerializerMethodField()
    # Sostituiamo registration_token con registration_link
    registration_link = serializers.URLField(read_only=True, help_text="Link completo per l'auto-registrazione (sola lettura)", allow_null=True)

    class Meta:
        model = StudentGroup
        fields = [
            'id',
            'owner', # Aggiornato
            'owner_name', # NUOVO CAMPO
            'name',
            'description',
            'is_public', # Aggiunto
            'registration_link', # Campo aggiornato
            'created_at',
            'is_active',
            'members', # Mostra i membri attuali
            'student_count',
            'pending_requests_count', # Aggiunto campo
        ]
        # Aggiunto is_public ai campi modificabili (con logica permessi nella view)
        read_only_fields = ['id', 'owner', 'created_at', 'registration_link'] # Aggiornato
        # Rimosso UniqueTogetherValidator, la logica è spostata nel metodo validate

    def get_student_count(self, obj):
        """Restituisce il numero di studenti nel gruppo."""
        return obj.memberships.count() # Usa il related_name corretto 'memberships'

    def get_owner_name(self, obj):
        """Restituisce il nome completo del proprietario."""
        if obj.owner:
            # Puoi scegliere tra username, get_full_name, o altro
            return obj.owner.get_full_name() or obj.owner.username
        return None

    def get_pending_requests_count(self, obj):
        """
        Restituisce il numero di richieste di accesso pendenti per questo gruppo,
       solo se l'utente corrente è il proprietario.
       """
        request = self.context.get('request')
        # Verifica che l'utente sia autenticato e sia il proprietario del gruppo 'obj'
        if request and hasattr(request, 'user') and request.user.is_authenticated and obj.owner == request.user:
            # Conta solo le richieste PENDING per questo gruppo
            return GroupAccessRequest.objects.filter(
                group=obj,
                status=GroupAccessRequest.AccessStatus.PENDING
            ).count()
        # Restituisce None o 0 se l'utente non è il proprietario o non ci sono richieste
        # Restituire None potrebbe essere più chiaro per distinguerlo da 0 richieste effettive.
        return None
    def validate(self, data):
        """
        Controlla che non esista già un gruppo con lo stesso nome per il docente corrente.
        """
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            # Questo non dovrebbe accadere in un contesto DRF normale
            raise serializers.ValidationError("Contesto della richiesta non valido.")

        owner = request.user # Aggiornato a owner
        name = data.get('name')
        is_public = data.get('is_public', False) # Ottieni is_public, default a False

        # Controlla l'esistenza solo se il nome è fornito (dovrebbe esserlo, ma per sicurezza)
        # Aggiornato a owner
        if name and StudentGroup.objects.filter(owner=owner, name=name).exists():
            # Se stiamo aggiornando (self.instance esiste) e il nome non è cambiato,
            # non sollevare l'errore. Altrimenti, solleva l'errore.
            if not self.instance or self.instance.name != name:
                 raise serializers.ValidationError(
                     {"name": "Esiste già un gruppo con questo nome per te."} # Aggiornato messaggio
                 )

        # Controlla se l'utente può creare gruppi pubblici
        if is_public and not owner.can_create_public_groups:
             raise serializers.ValidationError(
                 {"is_public": "Non hai i permessi per creare gruppi pubblici."}
             )

        return data

    # Rimosso metodo create ridondante. La logica è gestita da perform_create nel ViewSet.
    # def create(self, validated_data):
    #     """Associa il docente autenticato durante la creazione."""
    #     validated_data['teacher'] = self.context['request'].user
    #     return super().create(validated_data)

class StudentGroupDetailSerializer(StudentGroupSerializer):
    """Serializer dettagliato per StudentGroup, usato per retrieve/update."""
    # Eventualmente aggiungere altri dettagli se necessario per la vista dettaglio
    pass


class GenerateTokenSerializer(serializers.Serializer):
    """Serializer per restituire il link di registrazione generato."""
    registration_link = serializers.URLField(read_only=True)

class AddStudentSerializer(serializers.Serializer):
    """Serializer per aggiungere uno studente a un gruppo."""
    # Usiamo IntegerField invece di PrimaryKeyRelatedField per gestire la validazione manualmente
    student_id = serializers.IntegerField()

    def validate_student_id(self, value):
        """
        Verifica che lo studente esista e appartenga al docente che effettua la richiesta.
        """
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise serializers.ValidationError("Contesto della richiesta non valido.")

        # Rimosso il controllo sull'appartenenza dello studente al docente.
        # Ora verifichiamo solo che lo studente esista.
        # Il controllo dei permessi del docente per aggiungere al gruppo avverrà nella view.
        if not Student.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"Studente con ID {value} non trovato.")

        # Potremmo aggiungere un controllo per vedere se lo studente è già nel gruppo qui,
        # ma è meglio gestirlo nella view (con get_or_create) per evitare race conditions.

        # Restituiamo l'istanza dello studente invece dell'ID,
        # così la view non deve fare un'altra query.
        # NB: Questo cambia ciò che validated_data conterrà.
        # La view dovrà essere adattata.
        # return student # <-- Modifica 1: Restituisce l'istanza

        # Alternativa: Restituiamo l'ID se la view si aspetta l'ID
        return value # <-- Manteniamo l'ID per ora, la view fa già il get_object_or_404


# --- Serializers per Group Access Request ---

class GroupAccessRequestSerializer(serializers.ModelSerializer):
    """ Serializer per creare e visualizzare le richieste di accesso ai gruppi. """
    requesting_teacher = serializers.PrimaryKeyRelatedField(read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    group_owner_username = serializers.CharField(source='group.owner.username', read_only=True)
    # Aggiunto campo per il nome del docente richiedente
    requesting_teacher_name = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = GroupAccessRequest
        fields = [
            'id',
            'group',
            'group_name', # Campo aggiunto per leggibilità
            'group_owner_username', # Campo aggiunto per leggibilità
            'requesting_teacher',
            'requesting_teacher_name', # Aggiunto campo
            'status',
            'status_display', # Campo aggiunto per leggibilità
            'requested_at',
            'responded_at',
            'responder',
        ]
        read_only_fields = [
            'id',
            'requesting_teacher',
            'status', # Lo stato viene modificato tramite un endpoint dedicato (PATCH)
            'requested_at',
            'responded_at',
            'responder',
            'group_name',
            'group_owner_username',
            'requesting_teacher_name', # Aggiunto campo
            'status_display',
        ]

    def get_requesting_teacher_name(self, obj):
        """Restituisce il nome completo del docente richiedente."""
        if obj.requesting_teacher:
            return obj.requesting_teacher.get_full_name() or obj.requesting_teacher.username
        return None

    def validate_group(self, group):
        """
        Validazione durante la creazione della richiesta:
        - Il gruppo deve essere pubblico.
        - Il richiedente non deve essere l'owner.
        - Non deve esistere già una richiesta (PENDING o APPROVED) per questo utente/gruppo.
        """
        request = self.context.get('request')
        requesting_teacher = request.user

        if not group.is_public:
            raise serializers.ValidationError("Puoi richiedere accesso solo a gruppi pubblici.")

        if group.owner == requesting_teacher:
            raise serializers.ValidationError("Non puoi richiedere accesso a un tuo gruppo.")

        # Controlla richieste esistenti PENDING o APPROVED
        existing_request = GroupAccessRequest.objects.filter(
            group=group,
            requesting_teacher=requesting_teacher,
            status__in=[GroupAccessRequest.AccessStatus.PENDING, GroupAccessRequest.AccessStatus.APPROVED]
        ).exists()

        if existing_request:
            raise serializers.ValidationError("Hai già una richiesta in attesa o approvata per questo gruppo.")

        return group

    def create(self, validated_data):
        """ Associa il docente richiedente durante la creazione. """
        validated_data['requesting_teacher'] = self.context['request'].user
        return super().create(validated_data)


class RespondGroupAccessRequestSerializer(serializers.Serializer): # Cambiato a serializers.Serializer
    """ Serializer per validare i dati inviati per rispondere a una richiesta di accesso. """
    request_id = serializers.IntegerField() # Aggiunto campo request_id
    status = serializers.ChoiceField(choices=GroupAccessRequest.AccessStatus.choices) # Usiamo ChoiceField per validare lo stato

    def validate_status(self, value):
        """ Permette solo di impostare lo stato a APPROVED o REJECTED. """
        # La validazione ChoiceField gestisce già la presenza nelle choices.
        # Questa validazione aggiuntiva è ridondante ma innocua.
        # Potrebbe essere rimossa se si usa solo ChoiceField.
        if value not in [GroupAccessRequest.AccessStatus.APPROVED, GroupAccessRequest.AccessStatus.REJECTED]:
             raise serializers.ValidationError("Lo stato può essere solo 'Approvato' o 'Rifiutato'.")
        return value

    # Non c'è più bisogno della Meta class
    # La logica per aggiornare il modello GroupAccessRequest è nella view.