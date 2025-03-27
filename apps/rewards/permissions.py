from rest_framework import permissions
from apps.users.models import UserRole

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permette accesso completo agli Admin, accesso in sola lettura agli altri utenti autenticati.
    Utile per i template globali.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True # Tutti gli utenti autenticati possono leggere
        return request.user.role == UserRole.ADMIN # Solo Admin possono scrivere

class IsRewardTemplateOwnerOrAdmin(permissions.BasePermission):
    """
    Permette modifiche solo al Docente creatore del template locale o a un Admin.
    Permette lettura a tutti gli utenti autenticati (per template locali e globali).
    """
    def has_object_permission(self, request, view, obj):
        # La lettura è permessa a tutti gli autenticati (gestita a livello di vista/queryset)
        if request.method in permissions.SAFE_METHODS:
            return True

        # La scrittura è permessa solo al creatore (se locale) o a un Admin (se globale o locale)
        is_admin = request.user.role == UserRole.ADMIN
        is_owner = obj.creator == request.user

        if obj.scope == 'LOCAL':
            return is_owner or is_admin # Admin può modificare anche template locali? Decidiamo di sì per ora.
        elif obj.scope == 'GLOBAL':
            return is_admin # Solo Admin modifica globali
        return False

class IsRewardOwner(permissions.BasePermission):
    """
    Permette modifiche solo al Docente creatore della Ricompensa specifica.
    """
    def has_object_permission(self, request, view, obj):
        # La lettura potrebbe essere permessa anche agli studenti a cui è disponibile (gestito nella view)
        if request.method in permissions.SAFE_METHODS:
            # Potremmo aggiungere qui logica per studenti, ma è più semplice nel queryset della view
            return True

        # La scrittura è permessa solo al Docente creatore
        return obj.teacher == request.user and request.user.role == UserRole.TEACHER

class IsStudentOwnerForPurchase(permissions.BasePermission):
    """
    Permette accesso solo allo Studente che ha effettuato l'acquisto.
    """
    def has_object_permission(self, request, view, obj):
        # Usa request.student impostato da StudentJWTAuthentication
        student = getattr(request, 'student', None)
        return student is not None and obj.student == student

class IsTeacherOfStudentForPurchase(permissions.BasePermission):
    """
    Permette accesso al Docente associato allo Studente che ha effettuato l'acquisto.
    """
    def has_object_permission(self, request, view, obj):
        # obj è RewardPurchase, obj.student è lo Studente, obj.student.teacher è il Docente
        return obj.student.teacher == request.user and request.user.role == UserRole.TEACHER

# Potremmo aggiungere altri permessi specifici se necessario