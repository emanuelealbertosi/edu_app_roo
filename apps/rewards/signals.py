import logging
import os
from django.db import models # Import models for pre_save check
from django.db.models.signals import post_delete, pre_save # Import pre_save
from django.dispatch import receiver
from .models import Badge

logger = logging.getLogger(__name__)

@receiver(post_delete, sender=Badge)
def delete_badge_image_on_delete(sender, instance, **kwargs):
    """
    Deletes the image file from filesystem when a Badge object is deleted.
    """
    # Verifica se l'istanza ha un file immagine associato
    if instance.image:
        # Verifica se il file esiste effettivamente prima di tentare la cancellazione
        if hasattr(instance.image, 'path') and os.path.exists(instance.image.path):
            try:
                instance.image.delete(save=False) # save=False evita di salvare di nuovo il modello
                logger.info(f"Immagine {instance.image.name} eliminata per Badge ID {instance.id} eliminato.")
            except Exception as e:
                logger.error(f"Errore durante l'eliminazione del file immagine {instance.image.name} per Badge ID {instance.id}: {e}", exc_info=True)
        else:
            logger.warning(f"File immagine non trovato ({instance.image.name}) per Badge ID {instance.id} durante il tentativo di eliminazione post_delete.")
    else:
        logger.debug(f"Nessuna immagine da eliminare per Badge ID {instance.id} eliminato.")


@receiver(pre_save, sender=Badge)
def delete_old_badge_image_on_change(sender, instance, **kwargs):
    """
    Deletes the old image file from filesystem when the Badge image field is updated or cleared.
    """
    if not instance.pk: # If this is a new object, do nothing
        return

    try:
        # Get the old instance from the database
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return # Old instance not found, maybe deleted concurrently?

    # Check if the image field has changed and the old instance had an image
    if old_instance.image and old_instance.image != instance.image:
        old_image_path = old_instance.image.path
        if hasattr(old_instance.image, 'path') and os.path.exists(old_image_path):
            try:
                old_instance.image.delete(save=False)
                logger.info(f"Vecchia immagine {old_image_path} eliminata per Badge ID {instance.id} durante l'aggiornamento.")
            except Exception as e:
                logger.error(f"Errore durante l'eliminazione della vecchia immagine {old_image_path} per Badge ID {instance.id}: {e}", exc_info=True)
        else:
             logger.warning(f"Vecchio file immagine non trovato ({old_image_path}) per Badge ID {instance.id} durante il tentativo di eliminazione pre_save.")