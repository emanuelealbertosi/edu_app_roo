from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _ # Importa per verbose_name


class RewardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.rewards'
    verbose_name = _('Rewards & Gamification') # Nome più descrittivo per l'admin

    def ready(self):
        """
        Importa i segnali quando l'app è pronta.
        """
        import apps.rewards.signals # Importa il modulo dei segnali
