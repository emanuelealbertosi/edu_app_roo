# Piano di Implementazione: Miglioramento Salvataggio Automatico UDA

**Versione:** 1.0
**Data:** 3 Luglio 2025
**Autore:** Roo (Architect Mode)
**Riferimento Richiesta:** Conversazione del 3 Luglio 2025

## 1. Introduzione

Questo documento descrive il piano di implementazione per la correzione e il miglioramento della funzionalità di salvataggio automatico nel componente `UdaFormView.vue`. L'obiettivo è risolvere i problemi di usabilità causati da un salvataggio troppo frequente, che genera notifiche invasive e interferisce con l'input dell'utente.

## 2. Analisi del Problema

L'attuale implementazione in `UdaFormView.vue` utilizza un `watch` su tutti i campi del form, collegato a una funzione `debounce` con un ritardo di soli 2 secondi. Questo provoca:

1.  **Notifiche Continue:** Ogni salvataggio automatico mostra una notifica a comparsa (`toast`), interrompendo l'utente.
2.  **Perdita di Focus/Input:** Il ricaricamento dei dati dopo il salvataggio può resettare il campo che l'utente sta modificando, causando frustrazione e perdita di dati.

## 3. Obiettivi

1.  **Migliorare l'Esperienza Utente (UX):** Eliminare le notifiche invasive e fornire un feedback di stato discreto e chiaro.
2.  **Prevenire la Perdita di Input:** Garantire che il processo di salvataggio automatico non interferisca con l'editing in corso.
3.  **Mantenere l'Integrità dei Dati:** Assicurare che le modifiche vengano salvate in modo affidabile in background.

## 4. Piano di Implementazione Dettagliato

### Fase 1: Modifiche allo Stato del Componente (`UdaFormView.vue`)

1.  **Introdurre una Variabile di Stato per il Salvataggio:**
    *   Aggiungere una nuova variabile reattiva `saveStatus` che può assumere i seguenti valori: `'IDLE'`, `'DIRTY'`, `'SAVING'`, `'SAVED'`, `'ERROR'`.
    *   Questo stato guiderà la UI e la logica di salvataggio.

    ```typescript
    type SaveStatus = 'IDLE' | 'DIRTY' | 'SAVING' | 'SAVED' | 'ERROR';
    const saveStatus = ref<SaveStatus>('IDLE');
    ```

2.  **Aggiornare la Logica dei `watch`:**
    *   I `watch` esistenti sui `formData` non attiveranno più direttamente `debouncedAutoSave`.
    *   Invece, imposteranno `saveStatus.value = 'DIRTY'` ogni volta che viene rilevata una modifica (dopo il caricamento iniziale).

### Fase 2: Implementazione della Nuova Logica di Salvataggio

1.  **Creare un `watch` dedicato per `saveStatus`:**
    *   Un nuovo `watch` osserverà i cambiamenti di `saveStatus`.
    *   Quando lo stato diventa `'DIRTY'`, questo `watch` avvierà la funzione `debouncedAutoSave`.

2.  **Modificare la Funzione `handleAutoSave`:**
    *   **Prima del salvataggio:** Impostare `saveStatus.value = 'SAVING'`.
    *   **Chiamata API:** La chiamata `udaStore.updateUda` rimarrà invariata.
    *   **Gestione Successo:** In caso di successo, impostare `saveStatus.value = 'SAVED'`. **Cruciale:** Rimuovere la ricarica dei dati dal server o l'aggiornamento di `formData` con la risposta. La UI si fida dello stato locale fino al prossimo caricamento completo della pagina. Rimuovere la notifica `uiStore.addNotification`.
    *   **Gestione Errore:** In caso di errore, impostare `saveStatus.value = 'ERROR'`.

3.  **Aumentare il Delay del `debounce`:**
    *   Modificare la chiamata a `debounce` per usare un ritardo più lungo, ad esempio 3000ms o 5000ms, per dare all'utente più tempo per pensare e scrivere.

    ```typescript
    const debouncedAutoSave = debounce(handleAutoSave, 3000); // Aumentato a 3 secondi
    ```

### Fase 3: Aggiornamento dell'Interfaccia Utente (UI)

1.  **Creare un Componente Indicatore di Stato (`SaveStatusIndicator.vue` - opzionale ma consigliato):**
    *   Creare un piccolo componente che mostri un messaggio e/o un'icona in base al `saveStatus` ricevuto come prop.
    *   Esempi di messaggi:
        *   `DIRTY`: "Modifiche non salvate" (con un'icona di un dischetto o una nuvola)
        *   `SAVING`: "Salvataggio in corso..." (con un'icona di caricamento/spinner)
        *   `SAVED`: "Tutto salvato" (con un'icona di spunta)
        *   `ERROR`: "Errore nel salvataggio. Riprova." (con un'icona di errore)

2.  **Integrare l'Indicatore in `UdaFormView.vue`:**
    *   Aggiungere il componente indicatore nel template, in una posizione fissa e non invasiva, ad esempio vicino ai pulsanti di azione in fondo al form.
    *   Passare la variabile `saveStatus` al componente.

    ```html
    <!-- In UdaFormView.vue, vicino ai pulsanti -->
    <div class="flex items-center justify-end space-x-3 pt-4">
      <SaveStatusIndicator :status="saveStatus" />
      <RouterLink ...>Annulla</RouterLink>
      <button type="submit" ...>Salva Modifiche</button>
    </div>
    ```

## 5. Diagramma di Flusso (Mermaid)

```mermaid
graph TD
    A[Utente modifica un campo] --> B{Imposta saveStatus = 'DIRTY'};
    
    subgraph "Watcher su saveStatus"
        C{Stato è 'DIRTY'?} -- Sì --> D[Avvia timer di debounce (3s)];
    end

    D --> E{Utente continua a modificare?};
    E -- Sì --> B;
    E -- No --> F{Timer scade};
    
    F --> G{Imposta saveStatus = 'SAVING'};
    G --> H[Invia dati al server (handleAutoSave)];
    
    H -- Successo --> I{Imposta saveStatus = 'SAVED'};
    H -- Errore --> J{Imposta saveStatus = 'ERROR'};

    subgraph "Indicatore UI (SaveStatusIndicator)"
        B_UI["Mostra 'Modifiche non salvate'"]
        G_UI["Mostra 'Salvataggio...'"]
        I_UI["Mostra 'Tutto salvato'"]
        J_UI["Mostra 'Errore salvataggio'"]
    end

    B --> B_UI;
    G --> G_UI;
    I --> I_UI;
    J --> J_UI;
```

## 6. Testing

1.  **Test Manuale:**
    *   Verificare che modificando un campo, l'indicatore di stato cambi in "Modifiche non salvate".
    *   Attendere la scadenza del debounce e verificare che lo stato cambi in "Salvataggio..." e poi in "Tutto salvato".
    *   Verificare che durante la digitazione rapida o l'editing continuo, il salvataggio non venga attivato ripetutamente.
    *   Verificare che non compaiano più le notifiche a comparsa per il salvataggio automatico.
    *   Verificare che non ci sia perdita di focus o reset dei campi durante e dopo il salvataggio.
    *   Simulare un errore di rete per verificare che lo stato "Errore" venga mostrato correttamente.
2.  **Test E2E (Opzionale):**
    *   Scrivere uno scenario di test che esegua le verifiche manuali in modo automatico.

## 7. Prossimi Passi

1.  **Approvazione del Piano:** Questo documento.
2.  **Sviluppo Frontend:** Implementazione delle modifiche descritte in `UdaFormView.vue`.
3.  **Testing:** Esecuzione dei test.
4.  **Revisione e Deploy.**