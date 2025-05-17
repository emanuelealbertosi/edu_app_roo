# Piano per il Cambio Font a "Titillium Web" (con Integrazione Tailwind CSS)

Questo documento descrive i passaggi per cambiare il font predefinito di un progetto frontend a "Titillium Web, sans-serif" utilizzando Google Fonts, con particolare attenzione all'integrazione con Tailwind CSS.

**Obiettivi:**
*   Impostare "Titillium Web" come font principale.
*   Assicurare la corretta applicazione del font in un ambiente che utilizza Tailwind CSS.
*   Mantenere la possibilità di utilizzare i font di fallback standard.

## Diagramma del Piano (Aggiornato)

```mermaid
graph TD
    A[Inizio: Richiesta cambio font a "Titillium Web, sans-serif"] --> B[Recuperare link Google Fonts per "Titillium Web"];
    B --> C[Inserire link Google Fonts in <head> di index.html];
    C --> D[Verificare/Impostare font-family in CSS globale (es. style.css)];
    D --> E{Progetto usa Tailwind CSS?};
    E -- Sì --> F[Creare/Modificare tailwind.config.js];
    F --> G[Configurare "Titillium Web" in theme.fontFamily.sans];
    G --> H[Verificare ordine import CSS in main.ts/js];
    E -- No --> H;
    H --> I[Rimuovere override di font-family specifici nei componenti];
    I --> J[Testare UI/UX (Riavviare dev server, Hard Refresh)];
    J --> K{Problemi di visualizzazione?};
    K -- Sì --> L[Debug: Specificità CSS, Cache, Errori Console];
    L --> J;
    K -- No --> M[Verificare build e deployment];
    M --> N[Fine: Font aggiornato];
```

## Passi Dettagliati del Piano

### 1. Fase di Preparazione (Google Fonts)
*   **P1.1:** Visitare [Google Fonts](https://fonts.google.com/).
*   **P1.2:** Cercare il font "Titillium Web".
*   **P1.3:** Selezionare i pesi e gli stili desiderati (es. Light 300, Regular 400, Regular 400 Italic, SemiBold 600, Bold 700). È importante includere tutti i pesi che si prevede di utilizzare.
*   **P1.4:** Copiare i tag `<link>` forniti da Google Fonts. Esempio per i pesi 300, 400, 600, 700 e corsivo 400:
    ```html
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Titillium+Web:ital,wght@0,300;0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
    ```

### 2. Fase di Implementazione
*   **P2.1:** Aprire il file `index.html` principale del progetto frontend (es. `NOME_PROGETTO/index.html`).
*   **P2.2:** Incollare i tag `<link>` di Google Fonts (ottenuti al passo P1.4) all'interno del tag `<head>`.
*   **P2.3:** Aprire il file CSS globale principale (es. `NOME_PROGETTO/src/style.css` o `NOME_PROGETTO/src/assets/main.css`).
*   **P2.4:** Assicurarsi che la `font-family` di base sia impostata per includere "Titillium Web". Questo può essere fatto su `:root`, `html`, o `body`. Esempio:
    ```css
    /* In src/style.css o simile */
    :root { /* o html, body */
      font-family: "Titillium Web", system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
      /* Altre proprietà di base come line-height possono essere definite qui.
         Evitare di definire font-weight globalmente qui se si usa Tailwind,
         poiché Tailwind gestisce i pesi con le sue utility. */
    }
    ```
    *Nota: La lista dei font di fallback è stata estesa per una migliore compatibilità.*
*   **P2.5 (Integrazione Tailwind CSS):** Se il progetto utilizza Tailwind CSS:
    *   **P2.5.1:** Creare (se non esiste) o modificare il file `tailwind.config.js` (o `.ts`, `.cjs`, `.mjs`) nella directory principale del progetto frontend (es. `NOME_PROGETTO/tailwind.config.js`).
    *   **P2.5.2:** Configurare "Titillium Web" come font primario per la famiglia `sans` (o altre famiglie rilevanti come `serif` o `mono` se necessario) estendendo il tema di Tailwind.
        ```javascript
        // tailwind.config.js
        const defaultTheme = require('tailwindcss/defaultTheme');

        module.exports = {
          content: [
            "./index.html", // Percorso al file HTML principale
            "./src/**/*.{vue,js,ts,jsx,tsx}", // Percorsi ai file sorgente del progetto
          ],
          theme: {
            extend: {
              fontFamily: {
                // Aggiunge "Titillium Web" come prima scelta per la pila di font sans-serif
                sans: ['"Titillium Web"', ...defaultTheme.fontFamily.sans],
                // Esempio se si volesse usare Titillium anche per serif (improbabile per Titillium):
                // serif: ['"Titillium Web"', ...defaultTheme.fontFamily.serif],
              },
            },
          },
          plugins: [],
        };
        ```
        *Assicurarsi che il percorso in `content` corrisponda alla struttura del progetto.*
    *   **P2.5.3:** Verificare l'ordine di importazione dei file CSS nel file di entry point JavaScript/TypeScript (es. `NOME_PROGETTO/src/main.ts`). È cruciale che il file CSS che importa Tailwind (es. `src/index.css` contenente `@tailwind base; @tailwind components; @tailwind utilities;`) sia importato prima di qualsiasi altro file CSS personalizzato globale (`src/style.css`), se si desidera che gli stili personalizzati possano sovrascrivere Tailwind. Tuttavia, per l'impostazione della `font-family` di base tramite `tailwind.config.js`, l'ordine di `style.css` e `index.css` diventa meno critico per questo specifico aspetto, ma è buona norma importare prima Tailwind.
        ```typescript
        // Esempio src/main.ts
        import './index.css'; // Contiene le direttive @tailwind (importare prima)
        import './style.css'; // CSS personalizzato globale (importare dopo se si vogliono override)
        // ... resto del codice di inizializzazione app
        ```
*   **P2.6:** Rimuovere eventuali override di `font-family` da componenti specifici (es. stili `<style scoped>` nei file `.vue`) che potrebbero impedire l'applicazione del font configurato tramite Tailwind o il CSS globale.

### 3. Fase di Test e Rifinitura
*   **P3.1:** **Riavviare il server di sviluppo.** Questo è un passaggio cruciale dopo aver modificato `tailwind.config.js` affinché Tailwind rigeneri i suoi stili con la nuova configurazione.
*   **P3.2:** Eseguire un **"hard refresh"** del browser (es. Ctrl+Shift+R su Windows/Linux, Cmd+Shift+R su Mac) sulla pagina dell'applicazione per assicurarsi che il browser carichi gli ultimi file CSS e non utilizzi versioni in cache.
*   **P3.3:** Navigare attraverso le varie pagine e componenti dell'applicazione, prestando particolare attenzione a:
    *   Leggibilità del testo con il nuovo font.
    *   Corretta applicazione dei diversi pesi del font (Light, Regular, SemiBold, Bold) dove previsto.
    *   Allineamenti, spaziature e possibili rotture del layout.
    *   Aspetto generale dell'interfaccia utente.
*   **P3.4:** Eseguire test su diversi browser (es. Chrome, Firefox, Safari, Edge) e, se possibile, su diversi dispositivi o utilizzando gli strumenti di emulazione del browser.
*   **P3.5:** Se si riscontrano problemi visivi o di layout (es. il font non si applica a elementi specifici, problemi di peso del font):
    *   Ispezionare gli elementi problematici con gli strumenti di sviluppo del browser per verificare quali regole CSS `font-family` e `font-weight` vengono applicate e da quale foglio di stile provengono.
    *   Verificare la specificità delle regole CSS.
    *   Assicurarsi che i pesi del font richiesti siano stati inclusi nel link di Google Fonts (P1.3, P1.4).
    *   Se necessario, apportare aggiustamenti mirati al CSS globale o, in rari casi, a stili di componenti specifici, preferendo sempre la configurazione di Tailwind se possibile.

### 4. Fase di Finalizzazione
*   **P4.1:** Una volta che l'aspetto è soddisfacente su tutte le pagine e i dispositivi target, eseguire il processo di build del progetto (es. `npm run build`) per assicurarsi che non ci siano errori e che le modifiche siano applicate correttamente nella build di produzione.
*   **P4.2:** Se si utilizza un sistema di controllo versione (es. Git), committare tutte le modifiche apportate (inclusi `index.html`, `style.css`, `tailwind.config.js`, ecc.) con un messaggio descrittivo.

Questo piano aggiornato dovrebbe guidare l'implementazione del font "Titillium Web" in progetti frontend che utilizzano Tailwind CSS. Ricordarsi di sostituire "NOME_PROGETTO" con il nome effettivo della cartella del progetto (es. `frontend-lessons` o `FE-teacher`).