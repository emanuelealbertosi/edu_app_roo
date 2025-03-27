from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RewardTemplateViewSet, RewardViewSet, StudentShopViewSet,
    StudentWalletViewSet, StudentPurchasesViewSet, TeacherRewardDeliveryViewSet
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


# Gli URL dell'API sono determinati automaticamente dal router.
urlpatterns = [
    path('', include(router.urls)),
]

# Nota: Gli URL generati saranno tipo:
# /api/rewards/reward-templates/
# /api/rewards/rewards/
# /api/rewards/student/shop/
# /api/rewards/student/shop/{pk}/purchase/
# /api/rewards/student/wallet/
# /api/rewards/student/wallet/{pk}/transactions/
# /api/rewards/student/purchases/
# /api/rewards/teacher/delivery/pending-delivery/
# /api/rewards/teacher/delivery/{pk}/mark-delivered/