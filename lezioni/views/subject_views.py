from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied

from ..models import Subject
from ..serializers import SubjectSerializer
from ..permissions import IsAdminOrTeacher # Permesso per Admin e Docenti

class SubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet per visualizzare e modificare le Materie (Subject).
    Accesso consentito solo ad Admin e Docenti.
    """
    queryset = Subject.objects.all().order_by('name')
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrTeacher] # Solo utenti loggati Admin o Docenti

    def perform_create(self, serializer):
        """
        Imposta automaticamente il creatore della materia sull'utente loggato.
        """
        serializer.save(creator=self.request.user)

    def perform_update(self, serializer):
        """
        Impedisce la modifica del creatore originale.
        (Anche se il campo è read_only nel serializer, è una buona pratica aggiuntiva)
        """
        # Non permettiamo di cambiare il creatore, ma salviamo le altre modifiche
        serializer.save()

    def perform_destroy(self, instance):
        """
        Aggiungere logica di controllo se necessario prima di eliminare.
        Ad esempio, impedire l'eliminazione se ci sono Argomenti collegati?
        (Il modello Topic ha on_delete=CASCADE, quindi verranno eliminati anche gli argomenti.
         Potremmo voler cambiare questo comportamento o aggiungere un controllo qui).
        Per ora, permettiamo l'eliminazione.
        """
        # Controllo opzionale:
        # if instance.topics.exists():
        #     raise PermissionDenied("Impossibile eliminare la materia perché contiene argomenti.")
        instance.delete()