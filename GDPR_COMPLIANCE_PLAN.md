# Piano di Conformità GDPR per Applicazione Educativa

**Versione:** 1.0 (3 Maggio 2025)

## 1. Obiettivo

Questo documento delinea le modifiche e le integrazioni necessarie per rendere l'applicazione educativa conforme al Regolamento Generale sulla Protezione dei Dati (GDPR - Regolamento UE 2016/679).

## 2. Architettura Generale della Conformità

Tutte le operazioni sostanziali sui dati personali (raccolta, trattamento, accesso, modifica, cancellazione, anonimizzazione) avverranno esclusivamente nel **Backend (BE)**. Il **Frontend (FE)** fungerà da interfaccia utente per visualizzare informazioni (policy), raccogliere consensi specifici e permettere agli utenti di interagire con le funzionalità GDPR esposte dalle API del Backend.

## 3. Piano Dettagliato

```mermaid
graph TD
    A[Start: Analisi Requisiti GDPR] --> B(Definizione Basi Giuridiche);
    B --> C{Consenso Necessario? (es. minori)};
    C -- Sì --> D[Implementazione Gestione Consensi Specifici];
    C -- No --> E[Verifica Altre Basi Giuridiche];
    D --> F(Redazione Informativa Privacy & Cookie Policy - Solo Tecnici);
    E --> F;
    F --> G(Implementazione Diritti Interessati - Self Service via API BE);
    G --> H(Revisione Sicurezza Dati - Inclusa Anonimizzazione IP pre-logging);
    H --> I(Gestione Dati Minori);
    I --> J(Definizione Policy Data Retention - Inclusa Gestione Log IP);
    J --> K[Aggiornamento Documentazione Tecnica];
    K --> L[End: Applicazione Conforme];

    subgraph "Fase 1: Fondamenta Legali e Trasparenza"
        direction LR
        B; D; E; F;
    end

    subgraph "Fase 2: Funzionalità Utente e Dati"
        direction LR
        G; I; J;
    end

    subgraph "Fase 3: Sicurezza e Documentazione"
        direction LR
        H; K;
    end
```

### 3.1. Informativa Privacy & Cookie Policy

*   **Azione:** Creare/aggiornare i documenti `privacy_policy.md` e `cookie_policy.md` (o una sezione dedicata nella privacy policy).
*   **Contenuto Privacy Policy:** Dettagliare Titolare, DPO (se presente), Finalità, Basi Giuridiche (consenso, contratto, ecc.), Categorie Dati, Destinatari, Trasferimenti Extra-UE, Periodo Conservazione, Diritti Interessati (e come esercitarli), Diritto Revoca Consenso, Diritto Reclamo, Natura Obbligatoria/Facoltativa conferimento dati, Processi Decisionali Automatizzati.
*   **Contenuto Cookie Policy:** Chiarire l'uso **esclusivo di cookie tecnici** necessari al funzionamento (es. sessione JWT). Specificare che non richiedono consenso preventivo.
*   **Integrazione FE:** Linkare le policy nel footer. Richiedere accettazione esplicita (checkbox non pre-flaggata) della Privacy Policy e Termini di Servizio durante la registrazione.

### 3.2. Gestione del Consenso

*   **Registrazione:** Implementare nel BE la registrazione dell'avvenuta accettazione (data/ora, versione policy) della Privacy Policy/Termini.
*   **Minori:** Implementare nel BE e FE un meccanismo di verifica dell'età. Se sotto l'età del consenso digitale, implementare un flusso verificabile per ottenere il consenso parentale prima di completare la registrazione/attivazione dell'account.
*   **Cookie:** Nessun banner di consenso attivo necessario, data l'assenza di cookie non tecnici.

### 3.3. Implementazione Diritti Interessati (Self-Service via API BE)

*   **Accesso:** Creare API BE (`GET /api/profile/my-data/`) che restituisca tutti i dati personali dell'utente loggato in formato strutturato (JSON). Il FE fornirà interfaccia per chiamare l'API e visualizzare/scaricare i dati.
*   **Rettifica:** Assicurare che le API BE esistenti (`PUT /api/auth/user/`, ecc.) permettano la modifica dei dati consentiti. Il FE userà i form esistenti.
*   **Cancellazione (Diritto all'Oblio):** Creare API BE (`POST /api/profile/request-deletion/`). Il BE implementerà la logica di cancellazione sicura o anonimizzazione irreversibile dei dati dell'utente nel database e sistemi collegati. Il FE fornirà un'interfaccia per inviare la richiesta. Considerare la gestione asincrona.
*   **Portabilità:** Garantita dall'API di Accesso (`GET /api/profile/my-data/`).

### 3.4. Revisione Sicurezza Dati

*   **Data Breach:** Definire e documentare una procedura interna di gestione e notifica (autorità e interessati, se necessario).
*   **Minimizzazione Dati:** Rivedere tutti i campi (specie JSONB) per assicurare che vengano raccolti solo dati strettamente necessari.
*   **Anonimizzazione IP:** Implementare nel BE (o infrastruttura gestita dal BE) l'**anonimizzazione/troncamento degli indirizzi IP *prima* del loro salvataggio** in qualsiasi log o database. Loggare IP (anche anonimi) solo se strettamente necessario e per finalità documentate.
*   **Valutazione d'Impatto (DPIA):** Valutare se necessaria in base ai rischi (es. trattamento dati minori su larga scala).

### 3.5. Gestione Dati Minori

*   Oltre al consenso parentale (punto 3.2), assicurare che tutte le comunicazioni rivolte ai minori siano chiare e adatte alla loro età. Valutare ulteriori tutele specifiche se vengono trattate categorie particolari di dati.

### 3.6. Policy di Conservazione dei Dati (Data Retention)

*   **Definizione:** Stabilire periodi di conservazione specifici e giustificati per ogni categoria di dato (dati account, log attività, log accesso con IP anonimi, ecc.) basati su finalità e obblighi legali.
*   **Implementazione:** Creare script/comandi Django eseguibili periodicamente sul BE per cancellare o anonimizzare automaticamente i dati che hanno superato il periodo di conservazione definito.

### 3.7. Aggiornamento Documentazione Tecnica

*   **`design_document.md`:** Aggiornare per riflettere tutte le decisioni e implementazioni relative al GDPR.
*   **README.md:** Aggiungere una sezione sulla conformità GDPR e linkare alle policy e alla documentazione rilevante.

## 4. Prossimi Passi

Procedere con l'implementazione tecnica delle modifiche descritte, coordinando gli sforzi tra team Backend e Frontend.
---

## 5. Stato Implementazione (Aggiornato al 3 Maggio 2025, 15:18)

*   **Branch Git:** `gdpr-compliance` creato.
*   **3.2 Gestione del Consenso:**
    *   Registrazione Accettazione Policy:
        *   ✅ Modelli `User` e `Student` aggiornati con campi `privacy_policy_accepted_at`, `terms_of_service_accepted_at`.
        *   ✅ Migrazioni DB create e applicate.
        *   ✅ Serializer (`UserCreateSerializer`, `StudentRegistrationSerializer`, `GroupTokenRegistrationSerializer`) aggiornati per richiedere accettazione e salvare timestamp.
    *   Minori (Consenso Parentale): ✅ COMPLETATO (✅ BE: Modelli, Serializer, Email, View/URL verifica implementati; ✅ FE: Modifiche form `StudentRegistrationView.vue` fatte; ✅ FE: Modifiche form `GroupTokenRegistrationView.vue` fatte)
    *   Cookie Tecnici: Nessuna azione tecnica richiesta oltre all'informativa.
 *   **3.3 Implementazione Diritti Interessati:**
    *   Accesso (`GET /api/profile/my-data/`):
        *   ✅ URL definito in `apps/users/urls.py`.
        *   ✅ View base `UserDataExportView` creata in `apps/users/views.py`.
        *   ✅ Serializer GDPR specifici creati per `apps.rewards` (`GDPRWalletSerializer`, `GDPRPointTransactionSerializer`, `GDPRRewardPurchaseSerializer`).
        *   ✅ FATTO: Creati serializer GDPR specifici per `apps.education` e `apps.student_groups`.
        *   ✅ FATTO: Completata la logica di raccolta dati e serializzazione in `UserDataExportView` per studenti.
        *   ✅ FATTO: Implementata interfaccia FE in `ProfileView.vue` per visualizzare/scaricare dati.
    *   Rettifica:
        *   ✅ FATTO: Creato `StudentProfileUpdateSerializer` per nome/cognome.
        *   ✅ FATTO: Creata `StudentProfileUpdateView` (`PATCH /api/profile/me/`) per studenti.
        *   ✅ FATTO: Registrato URL per `StudentProfileUpdateView` in `apps/users/urls.py`.
        *   ✅ FATTO: Implementata interfaccia FE in `ProfileView.vue` per modifica nome/cognome.
    *   Cancellazione (`POST /api/profile/request-deletion/`): ✅ FATTO (Definito URL, View BE imposta flag `is_deletion_requested`, Interfaccia FE). ✅ FATTO (Comando `process_deletion_requests` creato per logica BE asincrona).
    *   Portabilità: Coperta dall'implementazione del Diritto di Accesso.
*   **3.1 Informativa Privacy & Cookie Policy:** ✅ COMPLETATO (✅ File placeholder `privacy_policy.md` e `cookie_policy.md` creati; ✅ Redazione contenuti COMPLETATA; Integrazione FE: ✅ Link footer aggiunti in `frontend-student/src/App.vue` e `frontend-teacher/src/App.vue`, ✅ Checkbox aggiunte in `StudentRegistrationView.vue`, ✅ Checkbox aggiunte in `GroupTokenRegistrationView.vue`).
*   **3.4 Revisione Sicurezza Dati:** ✅ COMPLETATO (✅ Procedura Data Breach (documentata in design_document.md), ✅ Minimizzazione Dati (revisione modelli completata, OK), ✅ Anonimizzazione IP (Nginx), ⚠️ DPIA: Valutazione preliminare indica necessità/forte raccomandazione - Avviare processo formale).
*   **3.5 Gestione Dati Minori:** ✅ COMPLETATO (✅ BE: Implementazione tecnica consenso parentale fatta; ✅ FE: Modifiche form `StudentRegistrationView.vue` fatte; ✅ FE: Modifiche form `GroupTokenRegistrationView.vue` fatte; ✅ Revisione comunicazioni (email consenso parentale aggiornata)).
*   **3.6 Policy Data Retention:** ✅ COMPLETATO (✅ Definizione policy (proposta iniziale in design_document.md), ✅ Implementazione script BE (`apply_data_retention.py`) creato - **TESTARE E SCHEDULARE**).
*   **3.7 Aggiornamento Documentazione Tecnica:** ✅ COMPLETATO (`design_document.md` aggiornato, ✅ `README.md` aggiornato).