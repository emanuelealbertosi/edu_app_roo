# Piano di Aggiornamento Grafico

Questo documento traccia i file modificati e quelli rimanenti per l'aggiornamento grafico basato sull'immagine fornita.

## File Modificati

### Frontend Studente (`frontend-student`)

*   `tailwind.config.js`: Aggiornata configurazione colori e font.
*   `src/App.vue`: Aggiornati stili layout principale (sidebar, header, sfondo).
*   `src/views/DashboardView.vue`: Aggiornati stili header, card, bottoni, testi.
*   `src/components/common/BaseButton.vue`: Aggiornate varianti colori e aggiunta `secondary-outline`.
*   `src/components/WalletCard.vue`: Aggiornati stili card, testi, colori transazioni.
*   `src/components/QuizList.vue`: Aggiornati stili card, testi, badge, bottoni.
*   `src/components/PathwayList.vue`: Aggiornati stili card, testi, barre progresso, bottoni.
*   `src/views/ShopView.vue`: Aggiornati stili header, card ricompense, bottoni, testi.
*   `src/views/PurchasesView.vue`: Aggiornati stili header, tabella, testi.
*   `src/views/BadgesView.vue`: Aggiornati stili header, testi, colori badge guadagnati.
*   `src/components/common/AnimatedBadge.vue`: Aggiornati stili placeholder e testo.

### Frontend Docente (`frontend-teacher`)

*   `tailwind.config.js`: Aggiornata configurazione colori e font (copiata da `frontend-student`).
*   `src/App.vue`: Aggiornati stili layout principale (sidebar, header, sfondo).
*   `src/views/DashboardView.vue`: Aggiornati stili header, stat cards, icone (Heroicons), quick links.
*   `src/views/StudentsView.vue`: Aggiornati stili header, sezione link registrazione, tabella, bottoni.
*   `src/views/QuizTemplatesView.vue`: Aggiornati stili header, form upload, tabella, bottoni.
*   `src/views/PathwayTemplatesView.vue`: Aggiornati stili header, tabella, bottoni.
*   `src/views/RewardsView.vue`: Aggiornati stili header, tabella, bottoni.
*   `src/views/AssignmentView.vue`: Aggiornati stili header, form selezione, lista studenti, bottoni.
*   `src/views/AssignedQuizzesView.vue`: Aggiornati stili header, tabella, bottoni.
*   `src/views/AssignedPathwaysView.vue`: Aggiornati stili header, tabella, bottoni.
*   `src/views/GradingView.vue`: Aggiornati stili header, card risposte, bottoni.
*   `src/views/DeliveryView.vue`: Aggiornati stili header, card consegne, bottoni, textarea.
*   `src/views/StudentProgressView.vue`: Aggiornati stili header, tabella, bottoni.
*   `src/views/QuizTemplateFormView.vue`: Aggiornati stili header, form, sezione domande, bottoni.
*   `src/views/PathwayTemplateFormView.vue`: Aggiornati stili header, form, sezione quiz, bottoni.

## File Rimanenti da Modificare (`frontend-teacher`)

*   `src/views/RewardFormView.vue`: Form creazione/modifica ricompense (prossimo passo).
*   `src/views/QuizFormView.vue`: Form creazione/modifica istanze quiz.
*   `src/views/PathwayFormView.vue`: Form creazione/modifica istanze percorsi.
*   `src/views/QuestionTemplateFormView.vue`: Form creazione/modifica domande template.
*   `src/views/QuestionFormView.vue`: Form creazione/modifica domande istanza.
*   `src/views/ProfileView.vue`: Vista profilo docente.
*   `src/views/LoginView.vue`: Vista login (opzionale, meno prioritaria).
*   `src/components/common/BaseButton.vue`: Necessita aggiornamento varianti colori (come fatto per `frontend-student`).
*   `src/components/common/BaseModal.vue`: Verificare se gli stili interni necessitano adeguamento.
*   `src/components/common/BaseTabs.vue`: Verificare se gli stili interni necessitano adeguamento.
*   `src/components/common/GlobalLoadingIndicator.vue`: Verificare se gli stili necessitano adeguamento.
*   Altri componenti specifici usati nelle viste rimanenti (es. `TemplateQuestionEditor.vue`) potrebbero richiedere piccoli aggiustamenti di stile.
## File da Modificare (`frontend-lessons`) - Pagine UDA e Template UDA

*   **Pagine Coinvolte:**
    *   `src/views/UdaTemplateFormView.vue`
    *   `src/views/UdaFormView.vue`
    *   Componenti correlati (es. `UdaContentEditor.vue`, modali di aggiunta/modifica contenuto, menu di aggiunta contenuti)
*   **Specifiche Grafiche Dettagliate:**
    *   **1. Coerenza Grafica Generale:**
        *   Allineare lo stile generale (font, colori primari/secondari, palette, spaziature, angoli arrotondati) a quello definito e implementato in `frontend-teacher` e `frontend-student` per un look & feel uniforme.
        *   Utilizzare i token di design (variabili CSS/Tailwind) esistenti per colori, font-size, spacing, ecc.
    *   **2. Evidenziazione e Struttura delle Sezioni:**
        *   Le principali sezioni dei form di modifica UDA/Template UDA (es. "Dati Principali UDA/Template", "Elenco Contenuti", "Menu Aggiunta Nuovo Contenuto") devono essere chiaramente separate e distinguibili.
        *   Utilizzare bordi colorati sottili (es. `border-gray-300` o un colore secondario del tema) e/o sfondi leggermente diversi (es. `bg-gray-50`) per ciascuna macro-sezione.
        *   Introdurre un padding interno consistente (es. `p-4` o `p-6`) all'interno di ogni sezione per dare respiro agli elementi contenuti.
        *   Considerare l'uso di `Card` o componenti contenitore stilizzati per raggruppare elementi correlati all'interno di una sezione.
    *   **3. Layout a Piena Larghezza e Allineamento:**
        *   Gli elementi dei form (input, select, textarea, liste) all'interno di ciascuna sezione devono espandersi per utilizzare l'intera larghezza disponibile del loro contenitore.
        *   Evitare allineamenti fissi a destra o larghezze predefinite che lasciano spazio inutilizzato, specialmente su schermi più grandi.
        *   Le label e i campi input dovrebbero essere allineati in modo chiaro e leggibile (es. label sopra il campo, o label a sinistra con allineamento verticale consistente).
    *   **4. Checkbox e Controlli di Selezione Personalizzati:**
        *   Sostituire le checkbox HTML standard con componenti switch "on/off" stilizzati, in linea con il design system dell'applicazione (se esistente, altrimenti crearne uno coerente).
        *   Questo si applica a opzioni come "Marcato come completato dal docente" o altre opzioni binarie.
        *   Anche i radio button, se usati, dovrebbero seguire uno stile personalizzato.
    *   **5. Differenziazione e Stile dei Bottoni:**
        *   Applicare stili distinti ai bottoni in base alla loro funzione e priorità (primaria, secondaria, di pericolo/eliminazione).
        *   Utilizzare le varianti di colore e stile definite nel componente `BaseButton.vue` (assicurandosi che sia aggiornato e coerente tra i vari frontend).
        *   Esempi:
            *   "Salva Modifiche": Bottone primario (es. colore principale del tema).
            *   "Aggiungi Contenuto": Bottone primario o secondario-accentuato.
            *   "Annulla": Bottone secondario-outline o grigio.
            *   "Elimina": Bottone di pericolo (es. rosso).
        *   Assicurare che i bottoni abbiano un feedback visivo chiaro al passaggio del mouse (`hover`) e alla pressione (`active`).
    *   **6. Restyling Menu/Sezione Aggiunta Contenuti:**
        *   La sezione o il componente utilizzato per aggiungere nuovi tipi di contenuto (Lezione, Quiz Template, Nota, Attività) all'UDA/Template UDA deve essere visivamente prominente e facile da usare.
        *   Potrebbe essere una toolbar, una card dedicata, o una serie di bottoni stilizzati con icone rappresentative per ogni tipo di contenuto.
        *   Deve essere chiaramente separata dal resto del form, magari con un titolo di sezione dedicato (es. "Aggiungi Nuovo Elemento Didattico").
        *   La grafica deve essere accattivante e moderna, in linea con il design generale del portale.
*   **Componenti Comuni da Verificare/Aggiornare (se usati in `frontend-lessons` e rilevanti per UDA):**
    *   `frontend-lessons/src/components/common/BaseButton.vue` (assicurarsi che sia allineato con le versioni in `frontend-teacher`/`frontend-student` o centralizzare il componente).
    *   `frontend-lessons/src/components/common/BaseModal.vue` (verificare stili interni, header, footer, bottoni modale).
    *   `frontend-lessons/src/components/common/BaseTabs.vue` (se utilizzato per navigare tra sotto-sezioni).
    *   `frontend-lessons/src/components/common/BaseCard.vue` (se esistente o da creare per le sezioni).
    *   Eventuali altri componenti UI riutilizzabili (es. selettori, input customizzati) devono essere resi coerenti.
*   **File Specifici da Modificare (lista non esaustiva, da dettagliare durante l'implementazione):**
    *   `frontend-lessons/src/views/UdaTemplateFormView.vue`
    *   `frontend-lessons/src/views/UdaFormView.vue`
    *   `frontend-lessons/src/components/uda/UdaContentEditor.vue`
    *   `frontend-lessons/src/components/uda/SelectExistingContentModal.vue`
    *   `frontend-lessons/src/components/uda/EditNoteContentModal.vue`
    *   `frontend-lessons/src/components/uda/EditActivityContentModal.vue`
    *   Componenti per la visualizzazione dei singoli contenuti UDA (es. `LessonContentDisplay.vue`, ecc.) se impattati dalle modifiche al layout generale della pagina di modifica.