# Piano di Implementazione: Sistema di Avvisi Modali

**Versione:** 1.0
**Data:** 2025-07-05

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

## 2. Lavoro Completato (Backend - Fase 1)

La struttura di base del backend è stata implementata con successo.

- **Creazione App Django:**
  - È stata creata manualmente una nuova app Django chiamata `announcements` all'interno della directory `apps/`.

- **Definizione Modelli (`models.py`):**
  - **`Announcement`**: Modello per contenere i dati dell'avviso, inclusi `title`, `content`, `is_active`, `is_important`, e `target_audience`.
  - **`UserAnnouncementView`**: Modello per tracciare la relazione tra un utente/studente e un avviso, memorizzando se l'utente ha scelto di non vederlo più (`do_not_show_again`). Gestisce correttamente la distinzione tra `User` (docenti/admin) e `Student`.

- **Configurazione Admin (`admin.py`):**
  - I modelli `Announcement` e `UserAnnouncementView` sono stati registrati nell'interfaccia di amministrazione di Django, consentendo la gestione completa degli avvisi direttamente dal pannello admin.

- **Registrazione App (`settings.py`):**
  - La nuova app `announcements` è stata aggiunta alla lista `INSTALLED_APPS` per integrarla nel progetto.

- **Migrazioni Database:**
  - È stato generato il file di migrazione iniziale (`0001_initial.py`) per i nuovi modelli.
  - La migrazione è stata applicata con successo al database, creando le tabelle necessarie.

---

## 3. Prossimi Passi (Next Steps)

### 3.1. Backend - Fase 2 (API)

- **Potenziamento Serializers (`serializers.py`):**
  - Creare serializer più specifici per le operazioni di lettura e scrittura, se necessario (es. un serializer di sola lettura che includa dati correlati).

- **Implementazione Viste API (`views.py`):**
  - **`AnnouncementListView`**: Creare un endpoint API (`GET /api/announcements/`) che restituisca la lista degli avvisi attivi pertinenti per l'utente autenticato (docente o studente). La logica dovrà:
    - Filtrare gli avvisi in base al `target_audience`.
    - Escludere gli avvisi che l'utente ha contrassegnato con "Non mostrare più" (verificando in `UserAnnouncementView`).
    - Rispettare l'ordinamento (`is_important`, `created_at`).
  - **`MarkAsReadView`**: Creare un endpoint API (`POST /api/announcements/{id}/mark-as-read/`) che permetta al frontend di notificare che un utente ha chiuso un avviso.
  - **`DoNotShowAgainView`**: Creare un endpoint API (`POST /api/announcements/{id}/do-not-show-again/`) per impostare il flag `do_not_show_again` a `True` per un utente e un avviso specifici.

- **Configurazione URL (`urls.py`):**
  - Registrare le nuove viste API per renderle accessibili.

- **Gestione Permessi (`permissions.py`):**
  - Assicurarsi che solo gli utenti autenticati (siano essi `User` o `Student`) possano accedere agli endpoint.

- **Scrittura Test:**
  - Creare test unitari e di integrazione per i nuovi modelli, le viste API e la logica di business.

### 3.2. Frontend (Docente & Studente)

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