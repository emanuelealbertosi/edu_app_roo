# apps/rewards/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.users.models import Student # Importa il modello Student
from .models import Wallet # Importa il modello Wallet
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Student)
def create_student_wallet(sender, instance, created, **kwargs):
    """
    Crea automaticamente un Wallet per ogni nuovo Studente creato.
    """
    if created:
        try:
            Wallet.objects.create(student=instance)
            logger.info(f"Wallet creato per il nuovo studente {instance.id} ({instance.student_code})")
        except Exception as e:
            # Logga eventuali errori durante la creazione del wallet
            logger.error(f"Errore nella creazione del wallet per lo studente {instance.id}: {e}", exc_info=True)

# Potremmo aggiungere anche un segnale pre_delete per Student se necessario,
# ma CASCADE sul OneToOneField dovrebbe gestire l'eliminazione del Wallet.