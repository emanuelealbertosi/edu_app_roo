from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from ..models import Topic, Subject
from ..serializers import TopicSerializer
from ..permissions import IsAdminOrTeacher # Permesso per Admin e Docenti

class TopicViewSet(viewsets.ModelViewSet):
    """
    ViewSet per visualizzare e modificare gli Argomenti (Topic).
    Accesso consentito solo ad Admin e Docenti.
    Permette il filtraggio per materia (subject_id).
    """
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrTeacher] # Solo utenti loggati Admin o Docenti

    def get_queryset(self):
        """
        Restituisce gli argomenti, opzionalmente filtrati per materia.
        """
        queryset = Topic.objects.select_related('subject').all() # Ottimizza recuperando la materia correlata
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        return queryset.order_by('subject__name', 'name')

    def perform_create(self, serializer):
        """
        Imposta automaticamente il creatore dell'argomento sull'utente loggato.
        Verifica che la materia specificata esista.
        """
        # Verifica esistenza materia (anche se il ModelChoiceField del serializer dovrebbe farlo)
        subject_id = serializer.validated_data.get('subject').id
        if not Subject.objects.filter(id=subject_id).exists():
             # Questo caso è improbabile se il serializer valida correttamente, ma è una sicurezza aggiuntiva
             return Response({"detail": f"Materia con ID {subject_id} non trovata."}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        """
        Impedisce la modifica del creatore originale.
        """
        serializer.save()

    def perform_destroy(self, instance):
        """
        Impedisce l'eliminazione se ci sono Lezioni collegate all'argomento.
        Il modello Lesson ha on_delete=PROTECT su topic, quindi il DB solleverà
        un'eccezione IntegrityError. Intercettiamo questo e restituiamo un errore 403.
        """
        if instance.lessons.exists():
             raise PermissionDenied(f"Impossibile eliminare l'argomento '{instance.name}' perché contiene lezioni associate.")
        instance.delete()