from django.apps import AppConfig


class RewardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.rewards' # Use the full path

    def ready(self):
        """
        Importa i segnali quando l'app è pronta.
        """
        import apps.rewards.signals # Importa il modulo dei segnali
