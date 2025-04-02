import { test, expect } from '@playwright/test';
import fs from 'fs'; // Importa fs per leggere il token (se necessario, anche se il setup lo gestisce)
import path from 'path'; // Importa path

// Percorso al file del token salvato dal setup
const tokenFile = 'playwright/.auth/teacher_token.txt';

test.describe('Gestione Quiz', () => {
  // Forza l'esecuzione seriale per evitare conflitti tra test CRUD
  test.describe.configure({ mode: 'serial' });

  // Hook eseguito prima di ogni test in questo describe block
  test.beforeEach(async ({ page }) => {
    // Leggi il token dal file
    if (!fs.existsSync(tokenFile)) {
      throw new Error(`Token file not found at ${tokenFile}. Run setup first.`);
    }
    const accessToken = fs.readFileSync(tokenFile, 'utf-8');

    // Vai a una pagina iniziale (es. login) PRIMA di iniettare il token
    await page.goto('/login');

    // Inietta il token nel localStorage nel contesto della pagina di login
    await page.evaluate(token => {
      localStorage.setItem('teacher_access_token', token);
    }, accessToken);

    // Ora naviga alla pagina principale. L'app dovrebbe inizializzare leggendo il token.
    await page.goto('/');

    // Attendi che la navigazione sia visibile
    await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible({ timeout: 15000 });
  });

  test('dovrebbe permettere la creazione di un nuovo quiz', async ({ page }) => {
    const newQuizTitle = `Quiz Test E2E - ${Date.now()}`;
    const newQuizDescription = 'Descrizione creata dal test E2E.';

    // 1. Navigare alla pagina Quiz
    await page.getByRole('link', { name: 'Quiz' }).click();
    await expect(page).toHaveURL('/quizzes');
    await expect(page.locator('h1:has-text("Gestione Quiz")')).toBeVisible();

    // 2. Cliccare sul pulsante "Crea Nuovo Quiz"
    await page.getByRole('button', { name: 'Crea Nuovo Quiz' }).click();

    // 3. Verificare la navigazione al form di creazione e l'intestazione corretta
    await expect(page).toHaveURL('/quizzes/new');
    await expect(page.locator('h1:has-text("Crea Nuovo Quiz")')).toBeVisible(); // Corretto a h1

    // 4. Compilare il form (usando gli ID corretti)
    await page.locator('#title').fill(newQuizTitle);
    await page.locator('#description').fill(newQuizDescription);

    // 5. Salvare il quiz (usando il selettore type=submit, più robusto al cambio testo)
    await page.locator('button[type="submit"]').click();

    // 6. Verificare il reindirizzamento alla lista quiz
    await expect(page).toHaveURL('/quizzes', { timeout: 10000 }); // Timeout aumentato per attesa API

    // 7. Verificare che il nuovo quiz sia presente nella lista
    //    Cerchiamo una riga della tabella che contenga il titolo del nuovo quiz
    await expect(page.locator(`tr:has-text("${newQuizTitle}")`)).toBeVisible();
    // Potremmo anche verificare la descrizione se visibile nella tabella
    // await expect(page.locator(`tr:has-text("${newQuizTitle}")`).locator(`text=${newQuizDescription}`)).toBeVisible();
  });

  test('non dovrebbe permettere la creazione di un quiz senza titolo', async ({ page }) => {
    // 1. Navigare alla pagina Quiz e poi al form di creazione
    await page.getByRole('link', { name: 'Quiz' }).click();
    await expect(page).toHaveURL('/quizzes');
    await page.getByRole('button', { name: 'Crea Nuovo Quiz' }).click();
    await expect(page).toHaveURL('/quizzes/new');
    await expect(page.locator('h1:has-text("Crea Nuovo Quiz")')).toBeVisible();

    // 2. Compilare solo la descrizione (lasciando il titolo vuoto)
    await page.locator('#description').fill('Descrizione senza titolo');

    // 3. Tentare di salvare
    await page.locator('button[type="submit"]').click();

    // 4. Verificare che si rimanga sulla stessa pagina (il salvataggio non è avvenuto)
    await expect(page).toHaveURL('/quizzes/new');

    // 5. Verificare che il campo titolo sia marcato come invalido (assumendo validazione HTML5)
    // Playwright non ha un matcher diretto per :invalid, quindi controlliamo l'attributo o un messaggio di errore
    const titleInput = page.locator('#title');
    // Opzione A: Controllare se il browser aggiunge un attributo o classe per l'invalidità (dipende dall'implementazione)
    // await expect(titleInput).toHaveAttribute('aria-invalid', 'true'); // Esempio
    // Opzione B: Verificare se appare un messaggio di errore specifico vicino al campo (più robusto se implementato)
    // await expect(page.locator('#title + .error-message')).toBeVisible(); // Esempio selettore

    // Per ora, verifichiamo solo che siamo rimasti sulla pagina,
    // implicando che la validazione ha bloccato il submit.
    // Una verifica più specifica sulla segnalazione dell'errore sarebbe ideale.
    await expect(titleInput).toBeVisible(); // Assicura che il campo sia ancora lì
  });

  // Aggiungere qui altri test per modifica ed eliminazione

  test('dovrebbe permettere la modifica di un quiz esistente', async ({ page }) => {
    const modificationSuffix = ' - Modificato E2E';

    // 1. Navigare alla pagina Quiz
    await page.getByRole('link', { name: 'Quiz' }).click();
    await expect(page).toHaveURL('/quizzes');
    await expect(page.locator('h1:has-text("Gestione Quiz")')).toBeVisible();

    // 2. Trovare il primo pulsante "Modifica" e cliccarlo
    //    Assumendo che i pulsanti siano in una cella <td> dentro una riga <tr> nel <tbody>
    const firstEditButton = page.locator('tbody tr:first-child td button:has-text("Modifica")');
    await expect(firstEditButton).toBeVisible({ timeout: 10000 }); // Attendi che sia visibile (potrebbe richiedere caricamento dati)
    await firstEditButton.click();

    // 3. Verificare la navigazione alla pagina di modifica (URL conterrà /edit)
    await expect(page).toHaveURL(/\/quizzes\/\d+\/edit/, { timeout: 10000 }); // \d+ per l'ID numerico
    await expect(page.locator('h1:has-text("Modifica Quiz")')).toBeVisible();

    // 4. Leggere il titolo attuale e modificarlo
    const titleInput = page.locator('#title');
    await expect(titleInput).toBeVisible(); // Assicurati che l'input sia caricato
    const currentTitle = await titleInput.inputValue();
    // Rimuovi eventuali suffissi precedenti prima di aggiungerne uno nuovo
    const baseTitle = currentTitle.replace(modificationSuffix, '');
    const modifiedTitle = baseTitle + modificationSuffix;
    await titleInput.fill(modifiedTitle);

    // 5. Salvare le modifiche
    await page.locator('button[type="submit"]').click();

    // 6. Verificare il reindirizzamento alla lista quiz
    await expect(page).toHaveURL('/quizzes', { timeout: 10000 });

    // 7. Verificare che il quiz con il titolo modificato sia presente nella lista
    await page.waitForTimeout(500); // Piccola pausa aggiuntiva
    await expect(page.locator(`tr:has-text("${modifiedTitle}")`)).toBeVisible({ timeout: 15000 }); // Aumentato timeout
  });

  test('dovrebbe permettere l\'eliminazione del primo quiz nella lista', async ({ page }) => {
    // 1. Navigare alla pagina Quiz
    await page.getByRole('link', { name: 'Quiz' }).click();
    await expect(page).toHaveURL('/quizzes');
    await expect(page.locator('h1:has-text("Gestione Quiz")')).toBeVisible();

    // 2. Attendere che la tabella sia caricata e contare le righe iniziali
    const tableBody = page.locator('tbody');
    await expect(tableBody.locator('tr').first()).toBeVisible({ timeout: 10000 }); // Attendi almeno una riga
    const initialRowCount = await tableBody.locator('tr').count();
    console.log(`Numero iniziale di quiz: ${initialRowCount}`);
    expect(initialRowCount).toBeGreaterThan(0); // Assicurati che ci sia almeno un quiz da eliminare

    // 3. Trovare il pulsante "Elimina" della prima riga e cliccarlo
    const firstQuizRow = tableBody.locator('tr').first();
    const deleteButton = firstQuizRow.locator('button:has-text("Elimina")');
    await expect(deleteButton).toBeVisible();

    // 3. Gestire esplicitamente la finestra di dialogo 'confirm' e cliccare su "Elimina"
    page.once('dialog', async dialog => {
      console.log(`Dialog message: ${dialog.message()}`);
      await dialog.accept(); // Accetta la conferma
    });

    // Attendere la risposta API DOPO aver cliccato (non in parallelo, per evitare race condition con il dialog)
    await deleteButton.click();
    await page.waitForResponse(response =>
        response.url().includes('/api/education/quizzes/') && response.request().method() === 'DELETE' && response.status() === 204,
        { timeout: 10000 } // Timeout per la risposta API
    );

    // 4. Verificare che il numero di righe sia diminuito
    await expect(tableBody.locator('tr')).toHaveCount(initialRowCount - 1, { timeout: 5000 }); // Timeout può essere ridotto ora
    console.log(`Numero finale di quiz: ${await tableBody.locator('tr').count()}`);
  });

  test('dovrebbe permettere l\'aggiunta e la modifica di una domanda a scelta multipla con opzioni', async ({ page }) => {
    const quizTitle = `Quiz Domande MC E2E - ${Date.now()}`;
    const questionText = 'Qual è la capitale dell\'Italia? (Test E2E)';
    const option1Text = 'Roma';
    const option2Text = 'Milano';
    const option3Text = 'Napoli';

    // --- 1. Creare un quiz di base ---
    await page.getByRole('link', { name: 'Quiz' }).click();
    await expect(page).toHaveURL('/quizzes');
    await page.getByRole('button', { name: 'Crea Nuovo Quiz' }).click();
    await expect(page).toHaveURL('/quizzes/new');
    await page.locator('#title').fill(quizTitle);
    await page.locator('#description').fill('Quiz per testare aggiunta domanda MC.');
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL('/quizzes', { timeout: 10000 });
    await expect(page.locator(`tr:has-text("${quizTitle}")`)).toBeVisible();

    // --- 2. Navigare alla modifica del quiz ---
    const quizRow = page.locator(`tr:has-text("${quizTitle}")`);
    await quizRow.locator('button:has-text("Modifica")').click();
    await expect(page).toHaveURL(/\/quizzes\/\d+\/edit/, { timeout: 10000 });
    await expect(page.locator('h1:has-text("Modifica Quiz")')).toBeVisible();

    // --- 3. Cliccare "Aggiungi Domanda" ---
    const addQuestionButton = page.locator('.questions-section button:has-text("Aggiungi Domanda")');
    await expect(addQuestionButton).toBeVisible();
    await addQuestionButton.click();

    // Attendiamo esplicitamente che l'URL cambi prima dell'asserzione
    await page.waitForURL(/\/quizzes\/\d+\/questions\/new/, { timeout: 10000 });

    // --- 4. Compilare form domanda (MC_SINGLE) ---
    // Ora l'asserzione dovrebbe passare se waitForURL ha successo
    await expect(page).toHaveURL(/\/quizzes\/\d+\/questions\/new/); // Rimuoviamo il timeout qui, già atteso sopra
    await expect(page.locator('h1:has-text("Aggiungi Nuova Domanda")')).toBeVisible();
    await page.locator('textarea#text').fill(questionText);
    await page.locator('select#question_type').selectOption({ value: 'MC_SINGLE' });

    // --- 5. Salvare la domanda (verrà reindirizzato alla modifica domanda) ---
    await page.locator('form button[type="submit"]').click();
    await expect(page).toHaveURL(/\/quizzes\/\d+\/questions\/\d+\/edit/, { timeout: 10000 });
    await expect(page.locator('.question-form-view h1')).toBeVisible({ timeout: 10000 }); // Verifica intestazione generica
    await page.waitForTimeout(200); // Piccola attesa aggiuntiva per il rendering
    await expect(page.locator('textarea#text')).toHaveValue(questionText); // Verifica testo domanda

    // --- 6. Verificare che l'editor opzioni sia visibile ---
    const optionsEditor = page.locator('.answer-options-section');
    // Attendiamo prima che l'elemento sia attaccato al DOM, poi verifichiamo la visibilità
    await optionsEditor.waitFor({ state: 'attached', timeout: 7000 });
    await expect(optionsEditor).toBeVisible({ timeout: 5000 }); // Timeout visibilità ridotto

    // --- 7. Aggiungere opzioni di risposta ---
    // Assumiamo selettori dentro AnswerOptionsEditor.vue:
    // input[placeholder="Testo opzione"], button:has-text("Aggiungi Opzione"), input[type="radio"] (per is_correct)
    // Attendiamo esplicitamente che il pulsante sia visibile dentro l'editor
    // Proviamo a selezionare il bottone in base alla struttura: il primo bottone dopo la lista ul
    const addOptionButtonLocator = optionsEditor.locator('ul.options-list + button');
    await expect(addOptionButtonLocator).toBeVisible({ timeout: 10000 }); // Attendiamo che sia visibile
    // Verifichiamo anche il testo per sicurezza
    await expect(addOptionButtonLocator).toHaveText("Aggiungi Opzione");
    const addOptionButton = addOptionButtonLocator; // Assegna il locator verificato
    // Selettore per l'input di testo dell'opzione (sarà cercato DOPO aver aggiunto una riga)
    const optionTextInputSelector = 'input[placeholder="Testo opzione"]';

    // Aggiungi Opzione 1 (Corretta)
    await addOptionButton.click(); // Prima clicca per aggiungere la riga
    // Trova l'input nella nuova riga (più robusto: l'ultimo input di quel tipo)
    const newOptionInput = optionsEditor.locator(optionTextInputSelector).last();
    await newOptionInput.fill(option1Text);
    // Attendi che l'input abbia il valore corretto
    await expect(newOptionInput).toHaveValue(option1Text);
    // Trova la riga (li) che contiene questo input specifico
    const option1Row = optionsEditor.locator('li').filter({ has: newOptionInput });
    // Ora marca come corretta all'interno di quella riga
    await option1Row.locator('input[type="radio"]').check();

    // Aggiungi Opzione 2
    await addOptionButton.click(); // Aggiungi riga per opzione 2
    await optionsEditor.locator('li:last-child').locator(optionTextInputSelector).fill(option2Text); // Compila opzione 2
    await expect(optionsEditor.locator(`li:has-text("${option2Text}")`)).toBeVisible();

    // Aggiungi Opzione 3
    await addOptionButton.click(); // Aggiungi riga per opzione 3
    await optionsEditor.locator('li:last-child').locator(optionTextInputSelector).fill(option3Text); // Compila opzione 3
    await expect(optionsEditor.locator(`li:has-text("${option3Text}")`)).toBeVisible();

    // --- 8. Salvare le opzioni (assumendo un bottone "Salva Opzioni" nell'editor) ---
    const saveOptionsButton = optionsEditor.locator('button:has-text("Salva Opzioni")');
    await expect(saveOptionsButton).toBeVisible();
    await saveOptionsButton.click();
    // Aggiungere un'attesa o verifica di successo se l'API/UI fornisce feedback
    await page.waitForTimeout(500); // Piccola pausa per permettere salvataggio

    // --- 9. Tornare alla modifica quiz ---
    await page.getByRole('button', { name: 'Annulla' }).click(); // Torna alla modifica quiz
    await expect(page).toHaveURL(/\/quizzes\/\d+\/edit/, { timeout: 10000 });

    // --- 10. Verificare presenza domanda nella lista del quiz ---
    await expect(page.locator('.question-list').locator(`text=${questionText}`)).toBeVisible();

    // --- 11. Navigare di nuovo alla modifica della domanda ---
    await page.locator('.question-list').locator(`text=${questionText}`).click(); // Assumendo che cliccare apra la modifica
    await expect(page).toHaveURL(/\/quizzes\/\d+\/questions\/\d+\/edit/, { timeout: 10000 });

    // --- 12. Verificare che la pagina non sia bianca e le opzioni siano presenti ---
    await expect(page.locator('.question-form-view h1')).toBeVisible({ timeout: 10000 }); // Intestazione visibile
    await expect(page.locator('textarea#text')).toHaveValue(questionText); // Testo domanda corretto
    await expect(optionsEditor).toBeVisible(); // Editor opzioni visibile
    await expect(optionsEditor.locator(`li:has-text("${option1Text}")`)).toBeVisible();
    await expect(optionsEditor.locator(`li:has-text("${option2Text}")`)).toBeVisible();
    await expect(optionsEditor.locator(`li:has-text("${option3Text}")`)).toBeVisible();
    // Verifica che l'opzione corretta sia selezionata
    await expect(optionsEditor.locator(`li:has-text("${option1Text}")`).locator('input[type="radio"]')).toBeChecked();
  });

});