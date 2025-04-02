import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

// Credenziali studente e ID quiz di test
const studentCode = 'STUDENT1000';
// const studentPin = '1234'; // PIN non sembra necessario per il login studente
const assignedQuizId = 88; // ID del quiz assegnato

// Percorso al file del token studente (se useremo un setup separato)
// const studentTokenFile = 'playwright/.auth/student_token.json';

test.describe('Svolgimento Quiz Studente', () => {
  // test.describe.configure({ mode: 'serial' }); // Potrebbe servire se i test modificano lo stato

  // --- Setup Autenticazione (da adattare) ---
  // Opzione A: Login diretto in ogni test (più semplice all'inizio)
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.locator('#student_code').fill(studentCode);
    // await page.locator('#pin').fill(studentPin); // Rimosso PIN
    await page.getByRole('button', { name: 'Login' }).click();
    // Attendi il reindirizzamento alla dashboard dello studente
    await expect(page).toHaveURL('/', { timeout: 15000 });
    // Attendi un elemento chiave della dashboard studente
    await expect(page.locator('h1:has-text("Dashboard Studente")')).toBeVisible({ timeout: 10000 }); // Assumendo un h1
  });

  // Opzione B: Usare un file di setup separato come per il teacher (più robusto)
  // test.use({ storageState: 'playwright/.auth/student.json' }); // Se si crea auth.setup.ts per studente

  // --- Test Cases ---

  test('dovrebbe mostrare il quiz assegnato nella dashboard', async ({ page }) => {
    // Vai alla sezione quiz (se esiste) o verifica direttamente nella dashboard
    // await page.getByRole('link', { name: 'I Miei Quiz' }).click(); // Esempio
    // await expect(page).toHaveURL('/my-quizzes'); // Esempio

    // Cerca il quiz specifico assegnato (usando l'ID o il titolo)
    // Assumiamo una card o una riga che contiene un link al quiz
    const quizLink = page.locator(`.quiz-card:has-text("Titolo Quiz ${assignedQuizId}") a`); // Esempio selettore
    // Oppure cerca per ID se più facile
    // const quizLink = page.locator(`[data-quiz-id="${assignedQuizId}"] a`);

    await expect(quizLink).toBeVisible();
    // Potremmo anche verificare altri dettagli se presenti (descrizione, stato, ecc.)
  });

  test('dovrebbe permettere di iniziare un tentativo per il quiz assegnato', async ({ page }) => {
    // Trova il link/pulsante per iniziare il quiz
    const startQuizButton = page.locator(`[data-quiz-id="${assignedQuizId}"] button:has-text("Inizia")`); // Esempio
    await expect(startQuizButton).toBeVisible();
    await startQuizButton.click();

    // Verifica la navigazione alla pagina del tentativo
    // L'URL potrebbe essere /quizzes/:id/attempt o simile
    await expect(page).toHaveURL(new RegExp(`/quizzes/${assignedQuizId}/attempt`), { timeout: 10000 });

    // Verifica elementi chiave della pagina di svolgimento
    await expect(page.locator('.quiz-attempt-view')).toBeVisible(); // Assumendo una classe contenitore
    await expect(page.locator('.question-text')).toBeVisible(); // Assumendo classe per testo domanda
    await expect(page.locator('.answer-options')).toBeVisible(); // Assumendo classe per opzioni
    await expect(page.locator('button:has-text("Invia Risposta")')).toBeVisible(); // O "Prossima Domanda"
  });

  // TODO: Aggiungere test per:
  // - Rispondere a diversi tipi di domande (MC_SINGLE, TF, MC_MULTI, FILL_BLANK)
  // - Navigare tra le domande (se possibile)
  // - Completare il quiz
  // - Verificare il punteggio/risultato (se mostrato subito)
  // - Gestire tentativi multipli (se permessi)

});