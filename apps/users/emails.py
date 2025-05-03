from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

def send_parental_consent_email(student):
    """
    Invia un'email al genitore/tutore per richiedere il consenso alla registrazione dello studente.
    """
    if not student.parental_consent_status == 'PENDING' or not student.parent_email or not student.parental_consent_verification_token:
        # Non inviare se lo stato non è PENDING, manca l'email o manca il token
        return

    # Costruisci l'URL di verifica assoluto
    # Assicurati che 'parental_consent_verify' sia il nome dell'URL pattern che definiremo
    # e che settings.SITE_URL sia definito nelle impostazioni Django (es. 'http://localhost:8000')
    verification_path = reverse('parental_consent_verify', kwargs={'token': str(student.parental_consent_verification_token)})
    # Fallback a localhost se SITE_URL non è definito (meglio definirlo!)
    base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    verification_url = base_url + verification_path

    subject = _("Richiesta di Consenso Parentale per Registrazione")
    # Costruisci l'URL della privacy policy (meglio se definito in settings)
    privacy_policy_path = getattr(settings, 'PRIVACY_POLICY_PATH', '/privacy-policy/') # Esempio di path
    privacy_policy_url = base_url.rstrip('/') + privacy_policy_path # Assicura uno slash singolo

    context = {
        'student_name': student.full_name,
        'verification_url': verification_url,
        'site_name': getattr(settings, 'SITE_NAME', 'La Nostra Piattaforma Edu'), # Aggiungi SITE_NAME a settings
        'consent_expiry_days': getattr(settings, 'PARENTAL_CONSENT_TOKEN_EXPIRY_DAYS', 7),
        'privacy_policy_url': privacy_policy_url, # Aggiunto URL privacy policy
    }

    # Potremmo usare template HTML più complessi
    html_message = render_to_string('emails/parental_consent_request.html', context)
    plain_message = strip_tags(html_message) # Messaggio di testo semplice come fallback
    from_email = settings.DEFAULT_FROM_EMAIL # Assicurati che sia configurato in settings.py
    recipient_list = [student.parent_email]

    try:
        send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
        # Log successo opzionale
    except Exception as e:
        # Loggare l'errore è importante!
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Errore invio email consenso parentale per studente {student.id} a {student.parent_email}: {e}", exc_info=True)
        # Considerare se sollevare un'eccezione o gestire l'errore in altro modo

# --- Template Esempio (da creare in templates/emails/parental_consent_request.html) ---
"""
<!DOCTYPE html>
<html>
<head>
    <title>{{ subject }}</title>
</head>
<body>
    <p>Gentile Genitore/Tutore,</p>
    <p>
        Suo figlio/a, <strong>{{ student_name }}</strong>, ha richiesto di registrarsi alla piattaforma educativa {{ site_name }}.
        Poiché ha meno di 14 anni, è richiesto il Suo consenso per completare la registrazione e attivare l'account.
    </p>
    <p>
        Per favore, clicchi sul link sottostante per rivedere la richiesta e fornire il Suo consenso o negarlo.
        Questo link scadrà tra {{ consent_expiry_days }} giorni.
    </p>
    <p>
        <a href="{{ verification_url }}">Verifica Richiesta di Consenso</a>
    </p>
    <p>
        Se non ha avviato Lei questa richiesta o non riconosce questa attività, può ignorare questa email in tutta sicurezza.
    </p>
    <p>
        Grazie,<br>
        Il Team di {{ site_name }}
    </p>
</body>
</html>
"""