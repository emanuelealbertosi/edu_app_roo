# Edu App Roo

Applicazione educativa per la gestione di studenti, quiz, percorsi e ricompense.

Backend sviluppato in Django e Django REST Framework.

## Setup (Istruzioni Base)

1.  Clonare il repository.
2.  Creare e attivare un ambiente virtuale Python:
    ```bash
    python -m venv .venv
    # Windows PowerShell:
    .venv\Scripts\Activate.ps1
    # Linux/macOS:
    # source .venv/bin/activate
    ```
3.  Installare le dipendenze:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configurare il database PostgreSQL e creare un file `.env` (vedi `.env.example` se presente).
5.  Applicare le migrazioni:
    ```bash
    python manage.py migrate
    ```
6.  Creare un superutente:
    ```bash
    python manage.py createsuperuser
    ```
7.  Avviare il server di sviluppo:
    ```bash
    python manage.py runserver
    ```

*(Aggiungere ulteriori dettagli su configurazione, API, ecc. in seguito)*