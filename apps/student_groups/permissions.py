from rest_framework import permissions
from .models import GroupAccessRequest

class IsGroupOwner(permissions.BasePermission):
    """
    Permesso custom per consentire azioni solo al proprietario del gruppo.
    """
    message = "Devi essere il proprietario del gruppo per eseguire questa azione."

    def has_object_permission(self, request, view, obj):
        # obj è l'istanza di StudentGroup
        return obj.owner == request.user

class HasGroupAccess(permissions.BasePermission):
    """
    Permesso custom per verificare se l'utente ha accesso approvato al gruppo.
    """
    message = "Devi avere accesso approvato al gruppo per eseguire questa azione."

    def has_object_permission(self, request, view, obj):
        # obj è l'istanza di StudentGroup
        user = request.user
        if not user.is_authenticated:
            return False

        # Verifica se esiste una richiesta di accesso approvata per questo utente e gruppo
        return GroupAccessRequest.objects.filter(
            group=obj,
            requesting_teacher=user,
            status=GroupAccessRequest.AccessStatus.APPROVED
        ).exists()

class IsOwnerOrHasAccess(permissions.BasePermission):
    """
    Permesso custom che combina IsGroupOwner e HasGroupAccess (OR).
    Utile per azioni consentite sia al proprietario che a chi ha accesso.
    """
    message = "Devi essere il proprietario o avere accesso approvato al gruppo per eseguire questa azione."

    def has_object_permission(self, request, view, obj):
        # obj è l'istanza di StudentGroup
        user = request.user
        if not user.is_authenticated:
            return False

        is_owner = (obj.owner == user)
        has_access = GroupAccessRequest.objects.filter(
            group=obj,
            requesting_teacher=user,
            status=GroupAccessRequest.AccessStatus.APPROVED
        ).exists()

        return is_owner or has_access

class IsRequestingTeacher(permissions.BasePermission):
    """
    Permesso custom per consentire azioni solo al docente che ha creato la richiesta di accesso.
    """
    message = "Puoi visualizzare o modificare solo le tue richieste di accesso."

    def has_object_permission(self, request, view, obj):
        # obj è l'istanza di GroupAccessRequest
        return obj.requesting_teacher == request.user