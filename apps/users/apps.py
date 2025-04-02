from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users' # Use the full path

    def ready(self):
        """
        Importa i segnali quando l'app è pronta.
        """
        try:
            import apps.users.signals
        except ImportError:
            pass
