from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.users.models import Student
from .models import StudentGroup, StudentGroupMembership
import secrets # Per generare il token

User = get_user_model()

class StudentBasicSerializer(serializers.ModelSerializer):
    """Serializer minimale per lo studente."""
    class Meta:
        model = Student
        fields = ['id', 'unique_identifier', 'first_name', 'last_name']

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
    teacher = serializers.PrimaryKeyRelatedField(read_only=True) # Il docente è l'utente autenticato che crea
    members = StudentGroupMembershipSerializer(source='studentgroupmembership_set', many=True, read_only=True)
    student_count = serializers.SerializerMethodField()
    # Sostituiamo registration_token con registration_link
    registration_link = serializers.URLField(read_only=True, help_text="Link completo per l'auto-registrazione (sola lettura)", allow_null=True)

    class Meta:
        model = StudentGroup
        fields = [
            'id',
            'teacher',
            'name',
            'description',
            'registration_link', # Campo aggiornato
            'created_at',
            'is_active',
            'members', # Mostra i membri attuali
            'student_count',
        ]
        read_only_fields = ['id', 'teacher', 'created_at', 'registration_link'] # Campo aggiornato
        # Rimosso UniqueTogetherValidator, la logica è spostata nel metodo validate

    def get_student_count(self, obj):
        """Restituisce il numero di studenti nel gruppo."""
        return obj.memberships.count() # Usa il related_name corretto 'memberships'

    def validate(self, data):
        """
        Controlla che non esista già un gruppo con lo stesso nome per il docente corrente.
        """
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            # Questo non dovrebbe accadere in un contesto DRF normale
            raise serializers.ValidationError("Contesto della richiesta non valido.")

        teacher = request.user
        name = data.get('name')

        # Controlla l'esistenza solo se il nome è fornito (dovrebbe esserlo, ma per sicurezza)
        if name and StudentGroup.objects.filter(teacher=teacher, name=name).exists():
            # Se stiamo aggiornando (self.instance esiste) e il nome non è cambiato,
            # non sollevare l'errore. Altrimenti, solleva l'errore.
            if not self.instance or self.instance.name != name:
                 raise serializers.ValidationError(
                     {"name": "Esiste già un gruppo con questo nome per questo docente."}
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

        teacher = request.user
        # print(f"[DEBUG] Validating student_id: {value} for teacher: ID={teacher.id}, Username={teacher.username}") # DEBUG REMOVED

        try:
            # Verifica esistenza E appartenenza al docente
            student = Student.objects.get(pk=value, teacher=teacher)
            # print(f"[DEBUG] Student found: {student.full_name}") # DEBUG REMOVED
        except Student.DoesNotExist:
            # print(f"[DEBUG] Student.DoesNotExist exception for ID: {value}, Teacher ID: {teacher.id}") # DEBUG REMOVED
            raise serializers.ValidationError(f"Studente con ID {value} non trovato o non appartenente a questo docente.")

        # Potremmo aggiungere un controllo per vedere se lo studente è già nel gruppo qui,
        # ma è meglio gestirlo nella view (con get_or_create) per evitare race conditions.

        # Restituiamo l'istanza dello studente invece dell'ID,
        # così la view non deve fare un'altra query.
        # NB: Questo cambia ciò che validated_data conterrà.
        # La view dovrà essere adattata.
        # return student # <-- Modifica 1: Restituisce l'istanza

        # Alternativa: Restituiamo l'ID se la view si aspetta l'ID
        return value # <-- Manteniamo l'ID per ora, la view fa già il get_object_or_404