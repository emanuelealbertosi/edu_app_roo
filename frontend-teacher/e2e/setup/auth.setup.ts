import { test as setup, expect } from '@playwright/test';
import fs from 'fs'; // Importa il modulo fs per scrivere file
import path from 'path'; // Importa il modulo path per gestire i percorsi

// File dove salvare lo stato di autenticazione (cookie, ecc.)
const authStateFile = 'playwright/.auth/teacher.json';
// File dove salvare solo il token di accesso
const tokenFile = 'playwright/.auth/teacher_token.txt';

setup('authenticate as teacher', async ({ page }) => {
  // Assicurati che la directory esista
  const authDir = path.dirname(authStateFile);
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }
  // **IMPORTANTE:** Assicurati che queste credenziali siano valide!
  const username = 'teacher_test'; // Sostituisci con username reale
  const password = 'password123'; // Sostituisci con password reale

  // Esegui il login
  await page.goto('/login');
  await page.locator('#username').waitFor();
  await page.locator('#username').fill(username);
  await page.locator('#password').fill(password);
  await page.getByRole('button', { name: 'Login' }).click();

  // Attendi il reindirizzamento alla pagina principale (o dashboard)
  // Aumenta il timeout se necessario
  await expect(page).toHaveURL('/', { timeout: 15000 });

  // Opzionale: Aggiungi un'attesa per un elemento specifico della dashboard
  // per assicurarti che il caricamento sia completo prima di salvare lo stato.
  // Esempio: await expect(page.locator('nav')).toBeVisible();

  // Salva lo stato di autenticazione (cookie, ecc.) nel file specificato.
  await page.context().storageState({ path: authStateFile });
  console.log(`Authentication state saved to ${authStateFile}`);

  // Estrai il token di accesso da localStorage
  const accessToken = await page.evaluate(() => localStorage.getItem('teacher_access_token'));

  if (!accessToken) {
    throw new Error('Access token not found in localStorage after login during setup.');
  }

  // Salva il token di accesso in un file separato
  fs.writeFileSync(tokenFile, accessToken);
  console.log(`Access token saved to ${tokenFile}`);
});