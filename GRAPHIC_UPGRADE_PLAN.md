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