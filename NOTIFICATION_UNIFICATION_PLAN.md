# Piano di Uniformazione delle Notifiche Toast

**Obiettivo:** Uniformare il sistema di notifiche a comparsa (toast) per successo, errore, info e warning tra i frontend `fe-lessons`, `frontend-student` e `frontend-teacher`, garantendo coerenza visiva e funzionale.

**Principi Guida:**
*   Massima coerenza visiva e funzionale.
*   Le notifiche server/badge specifiche di `frontend-student` rimangono invariate e separate da questo intervento.
*   Riutilizzo del codice esistente, partendo dalla soluzione di `fe-lessons` come base.

**Stato Attuale (26 Maggio 2025):**
*   L'infrastruttura di base per le notifiche toast uniformi è stata implementata nei tre frontend.
*   Le Fasi 1, 3, 4 e i passaggi principali della Fase 5 relativi alla creazione/modifica degli store e dei componenti di visualizzazione sono stati completati.

## Fase 1: Analisi e Preparazione (Comune) - COMPLETATA

1.  **Definizione Interfaccia Notifica Unificata:** - **COMPLETATA**
    *   Adottata la seguente interfaccia TypeScript:
        ```typescript
        export interface UniformNotification {
          id: string; // Stringa per flessibilità e coerenza con fe-lessons
          message: string;
          type: 'success' | 'error' | 'info' | 'warning'; // Tipi base
          duration?: number; // in ms, default 5000ms
          title?: string; // Titolo opzionale
        }
        ```

2.  **Scelta Stile Visivo Unificato:** - **COMPLETATA**
    *   Base: Stile di `frontend-lessons/src/components/common/GlobalNotificationDisplay.vue`, con aggiunta di icone emoji e supporto per il titolo.

## Fase 2: Creazione Modulo Notifiche Condiviso - SCARTATA

*   Si è optato per copiare e adattare i file base. - **DECISIONE PRESA**

## Fase 3: Implementazione in `frontend-lessons` (Rifattorizzazione Minima) - COMPLETATA

1.  **Aggiornamento Store:** - **COMPLETATO**
    *   `frontend-lessons/src/stores/ui.ts` aggiornato per includere `title?` nell'interfaccia `Notification`.
2.  **Aggiornamento Componente:** - **COMPLETATO**
    *   `frontend-lessons/src/components/common/GlobalNotificationDisplay.vue` modificato per visualizzare titolo e icone.

## Fase 4: Implementazione in `frontend-teacher` (Nuova Implementazione) - COMPLETATA

1.  **Integrazione Logica Store:** - **COMPLETATO**
    *   `frontend-teacher/src/stores/ui.ts` aggiornato con la logica di gestione delle notifiche e l'interfaccia `UniformNotification`.
2.  **Creazione Componente di Visualizzazione:** - **COMPLETATO**
    *   Creato `frontend-teacher/src/components/common/UniformNotificationDisplay.vue`.
    *   Importato e utilizzato in `frontend-teacher/src/App.vue`.
3.  **Integrazione Chiamate:** - **DA FARE**
    *   Nei punti del codice di `frontend-teacher` dove è necessario mostrare notifiche (es. gestione errori API, feedback azioni utente), importare `useUiStore` e chiamare `addNotification`.

## Fase 5: Implementazione in `frontend-student` (Adattamento Selettivo) - PARZIALMENTE COMPLETATA

1.  **Adattamento Store `notification.ts`:** - **COMPLETATO**
    *   In `frontend-student/src/stores/notification.ts`:
        *   Introdotta l'interfaccia `UniformNotification`.
        *   Aggiunto nuovo state (`uniformToastNotifications`) e azioni (`addUniformToastNotification`, `removeUniformToastNotification`).
        *   Mantenuta logica per `legacyToastNotifications` (badge) e `serverNotifications`.
        *   Corretto errore TypeScript relativo a `serverNotificationsError.value`.
2.  **Introduzione Componente di Visualizzazione Uniformato:** - **COMPLETATO**
    *   Creato `frontend-student/src/components/common/UniformNotificationDisplay.vue`.
    *   Importato e utilizzato in `frontend-student/src/App.vue` accanto a `NotificationContainer.vue` (per i badge).
3.  **Aggiornamento Chiamate:** - **DA FARE**
    *   Identificare nel codice di `frontend-student` i punti in cui vengono generate notifiche toast generiche (es. errori di login, errori di rete, successi generici).
    *   Modificare queste chiamate per utilizzare il nuovo sistema basato su `UniformNotification`.
    *   Le chiamate a `addBadgeToastNotification` rimarranno invariate.

## Fase 6: Test e Rifinitura (Comune) - DA FARE

1.  **Test Funzionali Incrociati:**
    *   Verificare che le notifiche toast generiche (successo, errore, info, warning) appaiano e scompaiano correttamente in tutti e tre i frontend dopo l'integrazione delle chiamate.
    *   Testare specificamente:
        *   Errori di login.
        *   Errori di assegnazione (se applicabile al FE).
        *   Errori di rete simulati.
        *   Notifiche di successo per operazioni comuni.
    *   In `frontend-student`, verificare che le notifiche badge e le notifiche server (se visibili come toast) continuino a funzionare come prima.
2.  **Test Visivi:**
    *   Confrontare l'aspetto delle notifiche toast generiche sui tre frontend.
    *   Verificare il posizionamento e l'eventuale sovrapposizione dei due contenitori di notifiche in `frontend-student` e aggiustare `z-index` se necessario.
3.  **Refactoring e Pulizia:**
    *   Rivedere il codice aggiunto/modificato.

## Lavori Futuri / Da Fare Specifici:

*   **`frontend-teacher`**:
    *   Implementare le chiamate a `uiStore.addNotification(...)` nei gestori di errori API (es. in `apiClient.ts` o wrapper specifici dei servizi), nei componenti dopo azioni utente (es. salvataggio form), ecc. per fornire feedback.
*   **`frontend-student`**:
    *   Sostituire le attuali chiamate a `addToastNotification` (la versione legacy con ID numerico) con chiamate a `notificationStore.addUniformToastNotification(...)` per tutti gli errori generici (login, rete, API) e successi non legati ai badge.
    *   Valutare attentamente lo `z-index` dei due contenitori di notifiche in `App.vue` per evitare sovrapposizioni indesiderate. Il `UniformNotificationDisplay.vue` ha `z-index: 50` ereditato; potrebbe essere necessario che `NotificationContainer.vue` (per i badge) abbia uno `z-index` diverso o che quello di `UniformNotificationDisplay` venga leggermente aumentato se devono coesistere senza sovrapporsi in modo errato.

## Diagramma di Flusso (Mermaid) - (Invariato, riflette il piano originale)

```mermaid
graph TD
    A[Inizio: Uniformare Notifiche Toast] --> B{Analisi Esistente};
    B -- fe-lessons --> B1[Store: ui.ts, Comp: GlobalNotificationDisplay.vue];
    B -- fe-student --> B2[Store: notification.ts (Toast+Server+Badge), Comp: NotificationContainer.vue];
    B -- fe-teacher --> B3[Store: ui.ts (solo API loading), Comp: Assente];

    A --> C{Definizione Standard};
    C --> C1[Interfaccia UniformNotification];
    C --> C2[Stile Visivo Unificato (base fe-lessons)];

    A --> D{Piano Implementazione};

    D -- frontend-lessons --> E[Rifattorizzare fe-lessons];
    E --> E1[Adattare Store ui.ts a UniformNotification];
    E --> E2[Adattare Comp. GlobalNotificationDisplay allo stile unificato];

    D -- frontend-teacher --> F[Implementare in fe-teacher];
    F --> F1[Copiare/Adattare logica Store da fe-lessons in ui.ts];
    F --> F2[Copiare/Creare Comp. UniformNotificationDisplay.vue];
    F --> F3[Integrare chiamate a addNotification];

    D -- frontend-student --> G[Adattare fe-student];
    G --> G1[Modificare Store notification.ts per supportare UniformNotification per toast generici];
    G --> G2[Mantenere logica Server/Badge toast separata e funzionante];
    G --> G3[Introdurre Comp. UniformNotificationDisplay.vue per toast generici];
    G --> G4[Aggiornare chiamate per toast generici];

    E2 --> H{Test};
    F3 --> H;
    G4 --> H;
    H --> I[Rilascio];

    subgraph Legenda Tipi Notifica Considerati
        L1[UniformNotification (Toast Generici)]
        L2[frontend-student: LegacyBadgeToast (Invariato)]
        L3[frontend-student: ServerNotification (Campanella - Invariato)]
    end