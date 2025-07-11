# Piano di Implementazione: Sistema di Avvisi Modali

**Versione:** 1.1
**Data:** 2025-07-11

## 1. Obiettivo del Progetto

Implementare un sistema di gestione avvisi nell'admin di Django per creare messaggi (con rich text) da mostrare agli utenti (Docenti e/o Studenti) all'interno di una modale al momento del login.

### Requisiti Chiave:
- **Creazione Admin:** L'admin deve poter creare, modificare e gestire gli avvisi.
- **Contenuto Rich Text:** Supporto per la formattazione del testo negli avvisi.
- **Targeting:** Possibilità di indirizzare gli avvisi a Docenti, Studenti o a entrambi.
- **Priorità:** Un flag "Importante" per mostrare certi avvisi prima di altri. L'ordine secondario è la data di creazione.
- **Visualizzazione Modale:** Gli avvisi devono apparire in una modale al login.
- **Sequenza:** Gli avvisi vengono mostrati uno dopo l'altro alla chiusura del precedente.
- **Controllo Utente:** La modale deve avere un pulsante "Chiudi" e un'opzione "Non mostrare più" che persiste per l'utente.

---

## 2. Lavoro Completato (Backend)

L'intera infrastruttura backend per il sistema di avvisi è stata implementata con successo e versionata sul branch `announcements`.

- **Creazione App Django:**
  - È stata creata manualmente una nuova app Django chiamata `announcements`.

- **Definizione Modelli (`models.py`):**
  - **`Announcement`**: Modello per contenere i dati dell'avviso.
  - **`UserAnnouncementView`**: Modello per tracciare le interazioni degli utenti con gli avvisi.

- **Configurazione Admin (`admin.py`):**
  - I modelli sono stati registrati nell'interfaccia di amministrazione di Django per una facile gestione.

- **Registrazione e Migrazioni:**
  - L'app è stata registrata in `settings.py` e le migrazioni del database sono state create e applicate.

- **Implementazione API (`views.py`, `urls.py`, `serializers.py`):**
  - **`GET /api/announcements/`**: Endpoint per recuperare la lista degli avvisi pertinenti per l'utente loggato.
  - **`POST /api/announcements/{id}/mark-as-read/`**: Endpoint per registrare la visualizzazione di un avviso.
  - **`POST /api/announcements/{id}/do-not-show-again/`**: Endpoint per permettere all'utente di nascondere permanentemente un avviso.
  - Gli URL sono stati registrati e resi disponibili a livello di progetto.

- **Controllo Versioni (Git):**
  - È stato creato un nuovo branch `announcements`.
  - Tutte le modifiche sono state committate e pushate sul repository remoto.

- **Editor Rich Text (WYSIWYG):**
  - Per il campo `content` è stato implementato un editor WYSIWYG (`django-ckeditor-5`) nell'admin di Django.
  - Questa scelta è stata fatta dopo aver scartato `django-ckeditor` a causa di warning di sicurezza e problemi tecnici con l'upload di file.
  - L'editor supporta la formattazione del testo, l'upload di immagini e l'inserimento di contenuti multimediali, migliorando significativamente la gestione degli avvisi.

---

## 3. Prossimi Passi (Next Steps)

### 3.1. Frontend (Docente & Studente)

Il backend è ora pronto. Il prossimo passo è l'integrazione con le applicazioni frontend.

- **Servizio API:**
  - Creare o aggiornare un servizio API (es. `announcementService.ts`) per comunicare con i nuovi endpoint del backend.

- **Store Management (Pinia/Vuex):**
  - Creare uno store per gestire lo stato degli avvisi (lista da mostrare, avviso corrente, stato della modale).

- **Componente Modale (`AnnouncementModal.vue`):**
  - Sviluppare un componente Vue riutilizzabile per la modale.
  - La modale deve poter renderizzare contenuto HTML (rich text) in modo sicuro.
  - Deve includere i pulsanti "Chiudi" e "Non mostrare più".

- **Logica di Visualizzazione:**
  - Al login dell'utente (o al refresh dell'app se l'utente è già loggato), effettuare una chiamata all'endpoint `GET /api/announcements/`.
  - Se la lista non è vuota, salvare gli avvisi nello store e mostrare il primo della lista nella modale.
  - Alla chiusura della modale, chiamare l'endpoint `mark-as-read` e mostrare l'avviso successivo nella lista, se presente.
  - Se l'utente clicca "Non mostrare più", chiamare l'endpoint `do-not-show-again` e chiudere la modale.