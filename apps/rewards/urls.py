from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RewardTemplateViewSet, RewardViewSet, StudentShopViewSet,
    StudentWalletViewSet, StudentPurchasesViewSet, TeacherRewardDeliveryViewSet,
    StudentWalletInfoView, # Importa la view del wallet
    BadgeViewSet, StudentEarnedBadgeViewSet # Importa i ViewSet dei Badge
)

# Crea un router e registra le viewset standard
router = DefaultRouter()
router.register(r'reward-templates', RewardTemplateViewSet, basename='reward-template')
router.register(r'rewards', RewardViewSet, basename='reward') # Gestione Docente/Admin
# ViewSet specifici per studenti (potrebbero avere un prefisso /student/)
router.register(r'student/shop', StudentShopViewSet, basename='student-shop')
router.register(r'student/wallet', StudentWalletViewSet, basename='student-wallet')
router.register(r'student/purchases', StudentPurchasesViewSet, basename='student-purchases')
# ViewSet specifico per docenti
router.register(r'teacher/delivery', TeacherRewardDeliveryViewSet, basename='teacher-delivery')
# Registra i nuovi endpoint per i Badge
router.register(r'badges', BadgeViewSet, basename='badge') # Lista definizioni badge
router.register(r'student/earned-badges', StudentEarnedBadgeViewSet, basename='student-earned-badge') # Badge guadagnati dallo studente


# Gli URL dell'API sono determinati automaticamente dal router.
urlpatterns = [
    path('', include(router.urls)),
    # Rimosso URL specifico per dashboard/wallet/, verrà gestito in config/urls.py
]

# Nota: Gli URL generati saranno tipo:
# /api/rewards/reward-templates/
# /api/rewards/rewards/
# /api/rewards/rewards/{pk}/make-available/  (Azione custom)
# /api/rewards/rewards/{pk}/revoke-availability/ (Azione custom)
# /api/rewards/student/shop/
# /api/rewards/student/shop/{pk}/purchase/
# /api/rewards/student/wallet/
# /api/rewards/student/wallet/{pk}/transactions/ # Azione custom (corretto)
# /api/rewards/student/purchases/
# /api/rewards/teacher/delivery/pending-delivery/ (Azione custom)
# /api/rewards/teacher/delivery/{pk}/mark-delivered/ (Azione custom)