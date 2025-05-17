import logging
import os
from django.db import models # Import models for pre_save check
from django.db.models.signals import post_delete, pre_save # Import pre_save
from django.dispatch import receiver
from .models import Badge

logger = logging.getLogger(__name__)

@receiver(post_delete, sender=Badge)
def delete_badge_files_on_delete(sender, instance, **kwargs):
    """
    Deletes the main file and thumbnail from filesystem when a Badge object is deleted.
    """
    # Delete main file
    if instance.file:
        if hasattr(instance.file, 'path') and os.path.exists(instance.file.path):
            try:
                instance.file.delete(save=False)
                logger.info(f"File {instance.file.name} eliminato per Badge ID {instance.id} eliminato.")
            except Exception as e:
                logger.error(f"Errore durante l'eliminazione del file {instance.file.name} per Badge ID {instance.id}: {e}", exc_info=True)
        else:
            logger.warning(f"File non trovato ({instance.file.name}) per Badge ID {instance.id} durante il tentativo di eliminazione post_delete.")
    else:
        logger.debug(f"Nessun file principale da eliminare per Badge ID {instance.id} eliminato.")

    # Delete thumbnail
    if instance.thumbnail:
        if hasattr(instance.thumbnail, 'path') and os.path.exists(instance.thumbnail.path):
            try:
                instance.thumbnail.delete(save=False)
                logger.info(f"Thumbnail {instance.thumbnail.name} eliminato per Badge ID {instance.id} eliminato.")
            except Exception as e:
                logger.error(f"Errore durante l'eliminazione del thumbnail {instance.thumbnail.name} per Badge ID {instance.id}: {e}", exc_info=True)
        else:
            logger.warning(f"File thumbnail non trovato ({instance.thumbnail.name}) per Badge ID {instance.id} durante il tentativo di eliminazione post_delete.")
    else:
        logger.debug(f"Nessun thumbnail da eliminare per Badge ID {instance.id} eliminato.")


@receiver(pre_save, sender=Badge)
def delete_old_badge_files_on_change(sender, instance, **kwargs):
    """
    Deletes the old main file and/or thumbnail from filesystem when the
    Badge file or thumbnail fields are updated or cleared.
    """
    if not instance.pk: # If this is a new object, do nothing
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return # Old instance not found

    # Check and delete old main file
    if old_instance.file and old_instance.file != instance.file:
        old_file_path = old_instance.file.path
        if hasattr(old_instance.file, 'path') and os.path.exists(old_file_path):
            try:
                old_instance.file.delete(save=False)
                logger.info(f"Vecchio file {old_file_path} eliminato per Badge ID {instance.id} durante l'aggiornamento.")
            except Exception as e:
                logger.error(f"Errore durante l'eliminazione del vecchio file {old_file_path} per Badge ID {instance.id}: {e}", exc_info=True)
        else:
            logger.warning(f"Vecchio file non trovato ({old_file_path}) per Badge ID {instance.id} durante il tentativo di eliminazione pre_save.")

    # Check and delete old thumbnail
    if old_instance.thumbnail and old_instance.thumbnail != instance.thumbnail:
        old_thumbnail_path = old_instance.thumbnail.path
        if hasattr(old_instance.thumbnail, 'path') and os.path.exists(old_thumbnail_path):
            try:
                old_instance.thumbnail.delete(save=False)
                logger.info(f"Vecchio thumbnail {old_thumbnail_path} eliminato per Badge ID {instance.id} durante l'aggiornamento.")
            except Exception as e:
                logger.error(f"Errore durante l'eliminazione del vecchio thumbnail {old_thumbnail_path} per Badge ID {instance.id}: {e}", exc_info=True)
        else:
            logger.warning(f"Vecchio file thumbnail non trovato ({old_thumbnail_path}) per Badge ID {instance.id} durante il tentativo di eliminazione pre_save.")