import { test, expect } from '@playwright/test';
import fs from 'fs'; // Importa fs per leggere il token
import path from 'path'; // Importa path

// Percorso al file del token salvato dal setup
const tokenFile = 'playwright/.auth/teacher_token.txt';

test.describe('Autenticazione Docente', () => {
  // Forza l'esecuzione seriale dei test in questo file
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
      console.log(`Token injected into localStorage on /login: ${token ? token.substring(0, 10) + '...' : 'null'}`);
    }, accessToken);

    // Ora naviga alla pagina principale. L'app dovrebbe inizializzare leggendo il token.
    await page.goto('/');

    // Attendi che la navigazione sia visibile (indicatore che lo stato è stato riconosciuto)
    await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible({ timeout: 15000 });
  });

  test('dovrebbe essere già loggato e sulla dashboard', async ({ page }) => {
    // Dato che usiamo lo stato salvato e beforeEach ci porta a '/',
    // verifichiamo solo che siamo effettivamente lì e un elemento chiave (il link Dashboard) sia visibile.
    await expect(page).toHaveURL('/');
    await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible(); // Verifica link Dashboard
    // Potresti verificare un titolo o un elemento specifico della dashboard qui
    // await expect(page.locator('h2:has-text("Dashboard")')).toBeVisible();
  });

  test('dovrebbe mostrare l\'elenco studenti', async ({ page }) => {
    // Il beforeEach ha già preparato lo stato di login

    // 1. Navigare alla pagina Studenti (cliccando sul link nella navbar)
    await page.getByRole('link', { name: 'Studenti' }).click();

    // 2. Verificare che la pagina Studenti sia caricata correttamente
    await expect(page).toHaveURL('/students', { timeout: 10000 }); // Aumenta timeout se necessario
    await expect(page.locator('h1:has-text("Gestione Studenti")')).toBeVisible(); // Corretto selettore a h1

    // 3. Opzionale: Verificare la presenza della tabella degli studenti
    // await expect(page.locator('table.students-table')).toBeVisible(); // Usa un selettore più specifico se possibile
  });

// Aggiungere qui altri test che richiedono l'autenticazione

  test('dovrebbe mostrare l\'elenco quiz', async ({ page }) => {
    // Il beforeEach ha già preparato lo stato di login

    // 1. Navigare alla pagina Quiz (cliccando sul link nella navbar)
    await page.getByRole('link', { name: 'Quiz' }).click();

    // 2. Verificare che la pagina Quiz sia caricata correttamente
    await expect(page).toHaveURL('/quizzes', { timeout: 10000 });
    // Verifichiamo la presenza di un'intestazione o di un elemento chiave della vista Quiz
    // (Assumendo che ci sia un h1 o h2 con testo simile a "Gestione Quiz")
    await expect(page.locator('h1:has-text("Gestione Quiz"), h2:has-text("Gestione Quiz")')).toBeVisible();

    // 3. Opzionale: Verificare la presenza della tabella dei quiz o di un quiz specifico
    // await expect(page.locator('table.quizzes-table')).toBeVisible();
    // await expect(page.locator('text=Nome Quiz Specifico')).toBeVisible(); // Se conosci un nome quiz
  });
});