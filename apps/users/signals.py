from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Student
# Importa Wallet qui per evitare import circolari a livello di modulo
# se rewards importasse qualcosa da users.models
from apps.rewards.models import Wallet
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Student)
def create_student_wallet(sender, instance, created, **kwargs):
    """
    Crea automaticamente un Wallet per un nuovo Studente.
    """
    if created:
        try:
            Wallet.objects.create(student=instance)
            logger.info(f"Wallet creato automaticamente per lo studente {instance.id} ({instance.student_code})")
        except Exception as e:
            # Logga eventuali errori durante la creazione del wallet
            logger.error(f"Errore nella creazione automatica del wallet per lo studente {instance.id}: {e}", exc_info=True)