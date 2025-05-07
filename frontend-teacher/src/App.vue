<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'; // Importa watch e onMounted
import { useAuthStore } from '@/stores/auth'; // Store specifico Teacher (per logout e checkAuth)
import { useSharedAuthStore } from '@/stores/sharedAuth'; // Importa store condiviso
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router';
import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';
import BaseModal from '@/components/common/BaseModal.vue'; // CORRETTO: Importa BaseModal
import AppFooter from '@/components/layout/AppFooter.vue'; // Importa il footer
import { marked } from 'marked'; // Importa marked
// import NotificationContainer from '@/components/common/NotificationContainer.vue'; // Se esiste
import {
  HomeIcon, // Dashboard
  UsersIcon, // Studenti
  UserGroupIcon, // Gruppi Studenti (NUOVO)
  ClipboardDocumentListIcon, // Quiz Templates
  MapIcon, // Template Percorsi (Pathways)
  ClipboardDocumentCheckIcon, // Quiz Assegnati
  MapPinIcon, // Percorsi Assegnati
  GiftIcon, // Ricompense
  PaperAirplaneIcon, // Assegna
  PencilSquareIcon, // Valutazioni (Grading)
  InboxArrowDownIcon, // Consegne (Delivery)
  ChartBarIcon, // Progressi
  UserCircleIcon, // Profilo
  BookOpenIcon, // Lezioni (Link esterno)
  ArrowLeftOnRectangleIcon, // Logout
  BellIcon, // Notifiche
  Bars3Icon, // Icona Hamburger per menu mobile
  XMarkIcon, // Icona per chiudere menu mobile
  MagnifyingGlassIcon // Icona per Sfoglia Gruppi
} from '@heroicons/vue/24/outline';

const authStore = useAuthStore(); // Mantenuto per azione logout specifica
const sharedAuth = useSharedAuthStore(); // Usa store condiviso per stato auth
const route = useRoute();
const router = useRouter();
const isMobileMenuOpen = ref(false); // Stato per menu mobile

// Stato per la modale Policy
const isModalOpen = ref(false);
const modalTitle = ref('');
const modalContentHtml = ref('');

// Contenuti Markdown Policy (copiati da frontend-student/src/App.vue)
// Idealmente, questi dovrebbero essere caricati da file o API per coerenza
const privacyPolicyMarkdown = `
# Informativa sulla Privacy

**Ultimo aggiornamento:** 3 Maggio 2025

La presente Informativa sulla Privacy descrive come Emanuele Albertosi (di seguito "noi", "ci" o "nostro/a") raccoglie, utilizza e protegge i dati personali degli utenti (di seguito "tu" o "tuo/a") della nostra applicazione educativa (di seguito "Applicazione").

Ci impegniamo a proteggere la tua privacy in conformità con il Regolamento Generale sulla Protezione dei Dati (GDPR - Regolamento UE 2016/679) e le altre leggi applicabili sulla protezione dei dati.

## 1. Titolare del Trattamento

Il Titolare del Trattamento dei tuoi dati personali è:
Emanuele Albertosi
Via del cavatore 29B
Email: emanuele.albertosi@gmail.com

## 2. Responsabile della Protezione dei Dati (DPO)

Non è stato nominato un Responsabile della Protezione dei Dati (DPO) in quanto non richiesto dalla normativa applicabile alle nostre attività. Per qualsiasi domanda relativa al trattamento dei tuoi dati personali, puoi contattare direttamente il Titolare del Trattamento all'indirizzo email sopra indicato.

## 3. Finalità e Basi Giuridiche del Trattamento

Trattiamo i tuoi dati personali per le seguenti finalità e sulla base delle seguenti basi giuridiche:

*   **a) Fornitura dei servizi dell'Applicazione:**
    *   **Finalità:** Consentirti di registrarti, accedere e utilizzare le funzionalità dell'Applicazione, inclusa la gestione di studenti, gruppi, quiz, percorsi, ricompense, assegnazioni e valutazioni.
    *   **Base Giuridica:** Esecuzione di un contratto di cui sei parte (i Termini di Servizio dell'Applicazione per docenti) (Art. 6.1.b GDPR).
    *   **Dati Trattati:** Nome, cognome, indirizzo email, password (hashata), dati relativi all'attività didattica (quiz creati, assegnazioni, valutazioni), appartenenza a istituti/organizzazioni (se applicabile), timestamp di accettazione delle policy.
*   **b) Gestione del consenso e adempimenti legali:**
    *   **Finalità:** Registrare e gestire l'accettazione dei Termini di Servizio e della presente Informativa Privacy; gestire le richieste di esercizio dei tuoi diritti; adempiere a obblighi legali, contabili o fiscali.
    *   **Base Giuridica:** Adempimento di un obbligo legale (Art. 6.1.c GDPR); Esecuzione di un contratto (Art. 6.1.b GDPR) per la registrazione dell'accettazione.
    *   **Dati Trattati:** Timestamp di accettazione, dati necessari per gestire le richieste (es. email per identificazione).
*   **c) Sicurezza e prevenzione frodi:**
    *   **Finalità:** Garantire la sicurezza dell'Applicazione e dei dati, prevenire attività fraudolente o abusi.
    *   **Base Giuridica:** Legittimo interesse del Titolare (Art. 6.1.f GDPR) a proteggere i propri sistemi e utenti, a condizione che non prevalgano i tuoi interessi o diritti e libertà fondamentali.
    *   **Dati Trattati:** Indirizzi IP (anonimizzati prima del logging, se loggati), log di accesso (anonimizzati), dati di utilizzo aggregati.

## 4. Categorie di Dati Personali Trattati

Le categorie di dati personali che trattiamo includono:

*   **Dati identificativi:** Nome, cognome, indirizzo email.
*   **Dati di autenticazione:** Password (memorizzata in formato hashato e salato).
*   **Dati relativi all'utilizzo dell'Applicazione:** Quiz creati, assegnazioni effettuate, valutazioni inserite, gruppi gestiti, log di attività (anonimizzati dove possibile).
*   **Dati tecnici:** Indirizzi IP (anonimizzati prima del logging), tipo di browser, sistema operativo (raccolti in forma aggregata o anonima per analisi).
*   **Dati relativi al consenso:** Timestamp di accettazione della Privacy Policy e dei Termini di Servizio.
*   **Dati forniti volontariamente:** Qualsiasi altra informazione che scegli di fornire tramite form di contatto o altre interazioni.

Non trattiamo categorie particolari di dati personali (dati sensibili) ai sensi dell'Art. 9 GDPR.

## 5. Destinatari o Categorie di Destinatari dei Dati

I tuoi dati personali potranno essere comunicati a:

*   **Personale autorizzato:** Nostri collaboratori interni autorizzati al trattamento dei dati per le finalità sopra indicate.
*   **Fornitori di servizi (Responsabili del Trattamento):** Terze parti che trattano dati per nostro conto (es. fornitori di hosting, servizi cloud, piattaforme di gestione database), vincolati da specifici accordi (Art. 28 GDPR) che ne garantiscono la conformità.
*   **Autorità pubbliche:** Ove richiesto dalla legge o per ordine dell'autorità giudiziaria o amministrativa.

Non vendiamo né cediamo i tuoi dati personali a terzi per finalità di marketing.

## 6. Trasferimento Dati Extra-UE

I tuoi dati personali sono trattati principalmente all'interno dell'Unione Europea (UE) o dello Spazio Economico Europeo (SEE). Non vengono effettuati trasferimenti dei tuoi dati personali al di fuori dell'UE/SEE. Qualora in futuro dovesse rendersi necessario un trasferimento, adotteremo tutte le garanzie adeguate previste dal GDPR (es. decisioni di adeguatezza, clausole contrattuali standard).

## 7. Periodo di Conservazione dei Dati

Conserviamo i tuoi dati personali solo per il tempo strettamente necessario a conseguire le finalità per cui sono stati raccolti, nel rispetto degli obblighi legali e contrattuali. I criteri specifici includono:

*   **Dati dell'account docente:** Conservati finché l'account è attivo e per un periodo definito dopo la cancellazione richiesta o l'inattività, salvo obblighi legali.
*   **Dati relativi all'attività didattica:** Conservati per il periodo necessario a garantire la continuità didattica e per adempiere a eventuali obblighi di conservazione legati alla documentazione scolastica/formativa, se applicabile.
*   **Log di accesso e sicurezza (anonimizzati):** Conservati per un periodo limitato.
*   **Dati relativi al consenso:** Conservati per il periodo necessario a dimostrare l'avvenuto consenso.

Al termine del periodo di conservazione, i dati saranno cancellati o anonimizzati.

## 8. Diritti dell'Interessato

In qualità di interessato, hai i diritti previsti dagli Artt. 15-22 GDPR (Accesso, Rettifica, Cancellazione, Limitazione, Portabilità, Opposizione), che puoi esercitare contattando il Titolare. Puoi gestire parte dei tuoi dati (es. profilo) tramite l'Applicazione.

## 9. Modalità di Esercizio dei Diritti

Puoi esercitare i tuoi diritti tramite le funzionalità dell'Applicazione (se disponibili per il dato specifico) o contattando il Titolare via email a emanuele.albertosi@gmail.com. Risponderemo entro un mese, prorogabile di due mesi per complessità.

## 10. Diritto di Revocare il Consenso

Se il trattamento si basa sul consenso, puoi revocarlo in qualsiasi momento, senza pregiudicare la liceità del trattamento precedente. La revoca del consenso alle policy obbligatorie impedirà l'uso dell'Applicazione.

## 11. Diritto di Proporre Reclamo all'Autorità di Controllo

Hai il diritto di proporre reclamo all'Autorità Garante competente (www.gpdp.it) se ritieni che il trattamento violi il GDPR.

## 12. Natura Obbligatoria o Facoltativa del Conferimento dei Dati

Il conferimento dei dati per la registrazione e l'accettazione delle policy è necessario per usare l'Applicazione (Base Giuridica: Contratto). Il mancato conferimento impedisce l'accesso.

## 13. Esistenza di Processi Decisionali Automatizzati

Non utilizziamo processi decisionali interamente automatizzati (Art. 22 GDPR) che producano effetti giuridici o incidano significativamente su di te.

## 14. Modifiche alla Presente Informativa

Ci riserviamo il diritto di aggiornare questa Informativa. Le modifiche saranno pubblicate sull'Applicazione e notificate se sostanziali.
`;

const cookiePolicyMarkdown = `
# Informativa sui Cookie

**Ultimo aggiornamento:** 3 Maggio 2025

Questa applicazione educativa (di seguito "Applicazione") utilizza esclusivamente **cookie tecnici** strettamente necessari per il suo corretto funzionamento e per garantire la sicurezza della sessione utente.

## Cosa sono i cookie tecnici?

I cookie tecnici sono quelli utilizzati al solo fine di "effettuare la trasmissione di una comunicazione su una rete di comunicazione elettronica, o nella misura strettamente necessaria al fornitore di un servizio della società dell'informazione esplicitamente richiesto dal contraente o dall'utente a erogare tale servizio" (cfr. art. 122, comma 1, del Codice Privacy italiano). Non vengono utilizzati per scopi ulteriori e la loro installazione non richiede il consenso preventivo degli utenti.

## Quali cookie tecnici utilizziamo?

L'Applicazione utilizza i seguenti cookie tecnici:

*   **Cookie di sessione (basato su JWT - JSON Web Token):** Questo cookie è essenziale per identificare e autenticare l'utente durante la sua sessione di navigazione dopo aver effettuato l'accesso. Contiene un token sicuro che permette all'utente di navigare tra le pagine senza dover effettuare nuovamente il login. Questo cookie viene automaticamente cancellato alla chiusura del browser o al momento del logout dall'Applicazione.

**Non utilizziamo altri tipi di cookie**, né tecnici persistenti, né cookie di profilazione, né cookie di terze parti.

## Consenso

Poiché utilizziamo **esclusivamente cookie tecnici** necessari al funzionamento dell'Applicazione, **non è richiesto il consenso preventivo** dell'utente per la loro installazione, come previsto dalla normativa vigente (GDPR e direttiva ePrivacy, come recepita dalla normativa italiana). La presente informativa è fornita per garantire la massima trasparenza.

## Come gestire i cookie tramite le impostazioni del browser?

Sebbene non sia necessario per l'utilizzo dell'Applicazione (dato che usiamo solo cookie tecnici essenziali), puoi comunque decidere di gestire o disabilitare i cookie direttamente dalle impostazioni del tuo browser.

**Attenzione:** La disabilitazione del cookie tecnico di sessione impedirà il corretto funzionamento dell'Applicazione, rendendo impossibile l'accesso all'area riservata e l'utilizzo dei servizi.

Di seguito trovi i link alle istruzioni per gestire i cookie sui browser più diffusi:

*   **Google Chrome:** [https://support.google.com/chrome/answer/95647](https://support.google.com/chrome/answer/95647)
*   **Mozilla Firefox:** [https://support.mozilla.org/it/kb/Gestione%20dei%20cookie](https://support.mozilla.org/it/kb/Gestione%20dei%20cookie)
*   **Microsoft Edge:** [https://support.microsoft.com/it-it/windows/eliminare-e-gestire-i-cookie-168dab11-0753-043d-7c16-ede5947fc64d](https://support.microsoft.com/it-it/windows/eliminare-e-gestire-i-cookie-168dab11-0753-043d-7c16-ede5947fc64d)
*   **Apple Safari:** [https://support.apple.com/it-it/guide/safari/sfri11471/mac](https://support.apple.com/it-it/guide/safari/sfri11471/mac)
*   **Opera:** [https://help.opera.com/en/latest/web-preferences/#cookies](https://help.opera.com/en/latest/web-preferences/#cookies)

Per maggiori informazioni sui cookie e su come gestirli, puoi anche visitare il sito [www.aboutcookies.org](http://www.aboutcookies.org/) o [www.allaboutcookies.org](http://www.allaboutcookies.org/).

## Modifiche alla Presente Informativa

Ci riserviamo il diritto di aggiornare la presente Informativa sui Cookie. Qualsiasi modifica sarà pubblicata sull'Applicazione.
`;

// Funzioni per aprire la modale Policy
const openPrivacyModal = async () => {
  modalTitle.value = 'Informativa sulla Privacy';
  modalContentHtml.value = await Promise.resolve(marked(privacyPolicyMarkdown));
  isModalOpen.value = true;
};

const openCookieModal = async () => {
  modalTitle.value = 'Informativa sui Cookie';
  modalContentHtml.value = await Promise.resolve(marked(cookiePolicyMarkdown));
  isModalOpen.value = true;
};

const closeModal = () => {
  isModalOpen.value = false;
};

// URL per l'app Lezioni
const lessonsAppUrl = computed(() => (import.meta.env.VITE_LESSONS_APP_URL as string | undefined) || '/lezioni/'); // Usa env var o fallback

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value;
};

const handleLogout = () => {
  authStore.logout();
};

const goToProfile = () => {
  router.push({ name: 'profile' });
};

// LOGGING per debug menu
watch(route, (to) => {
  console.log(`[App.vue Watch Route] Navigated to: ${to.path}, Route Name: ${String(to.name)}, IsAuthenticated: ${sharedAuth.isAuthenticated}`);
}, { immediate: true, deep: true }); // immediate per log iniziale, deep non strettamente necessario ma sicuro

// Hook onMounted per controllare l'autenticazione all'avvio
onMounted(async () => {
  console.log('[App.vue onMounted] Component mounted. Checking authentication status...');
  // Chiama l'azione dallo store authTeacher per verificare e recuperare il profilo
  // se è presente un token valido nello store condiviso (caricato da localStorage).
  await authStore.checkAuthAndFetchProfile();
  console.log('[App.vue onMounted] Authentication check complete.');
});

</script>

<template>
  <GlobalLoadingIndicator />
  <!-- <NotificationContainer /> --> <!-- Se esiste -->

  <!-- Modale per le Policy -->
  <BaseModal
    :show="isModalOpen"
    :title="modalTitle"
    @close="closeModal"
  >
    <!-- Inserisci il contenuto HTML nello slot predefinito -->
    <div class="p-6 prose max-w-none" v-html="modalContentHtml"></div>
  </BaseModal>

  <div class="flex min-h-screen bg-neutral-lightest font-sans text-neutral-darkest"> <!-- Changed h-screen to min-h-screen -->
    <!-- Sidebar Desktop (visibile da md in su) -->
    <!-- Mostra sidebar solo se autenticato E non sulla landing page -->
    <aside
      v-if="sharedAuth.isAuthenticated && route.name !== 'landing'"
      class="bg-secondary text-neutral-lightest hidden md:flex flex-col w-20 group hover:w-64 transition-all duration-300 ease-in-out overflow-hidden"
      aria-label="Sidebar"
    >
      <!-- Logo/Titolo App -->
       <div class="h-16 flex items-center justify-center flex-shrink-0 px-4">
         <span class="text-xl font-semibold opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Teacher Portal</span>
       </div>

      <!-- Navigazione Desktop -->
      <nav class="flex-grow p-4 overflow-y-auto overflow-x-hidden">
        <ul>
          <!-- Dashboard -->
          <li class="mb-2">
            <router-link :to="{ name: 'dashboard' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <HomeIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Dashboard</span>
            </router-link>
          </li>
          <!-- Studenti -->
          <li class="mb-2">
            <router-link :to="{ name: 'students' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <UsersIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Studenti</span>
            </router-link>
          </li>
          <!-- Gruppi Studenti (NUOVO) -->
          <li class="mb-2">
            <router-link :to="{ name: 'GroupsList' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <UserGroupIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Gruppi</span>
            </router-link>
          </li>
          <!-- Sfoglia Gruppi Pubblici -->
          <li class="mb-2">
            <router-link :to="{ name: 'BrowseGroups' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <MagnifyingGlassIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Sfoglia Gruppi</span>
            </router-link>
          </li>
           <!-- Quiz Templates -->
          <li class="mb-2">
            <router-link :to="{ name: 'quiz-templates' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <ClipboardDocumentListIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Quiz Templates</span>
            </router-link>
          </li>
          <!-- Template Percorsi - Temporarily Hidden -->
          <!--
          <li class="mb-2">
            <router-link :to="{ name: 'pathway-templates' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <MapIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Template Percorsi</span>
            </router-link>
          </li>
          -->
          <!-- Quiz Assegnati -->
          <li class="mb-2">
            <router-link :to="{ name: 'assigned-quizzes' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <ClipboardDocumentCheckIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Quiz Assegnati</span>
            </router-link>
          </li>
          <!-- Percorsi Assegnati - Temporarily Hidden -->
          <!--
          <li class="mb-2">
            <router-link :to="{ name: 'assigned-pathways' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <MapPinIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Percorsi Assegnati</span>
            </router-link>
          </li>
          -->
          <!-- Ricompense -->
          <li class="mb-2">
            <router-link :to="{ name: 'rewards' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <GiftIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Ricompense</span>
            </router-link>
          </li>
          <!-- Assegna -->
          <li class="mb-2">
            <router-link :to="{ name: 'assign' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <PaperAirplaneIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Assegna</span>
            </router-link>
          </li>
          <!-- Valutazioni -->
          <li class="mb-2">
            <router-link :to="{ name: 'grading' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <PencilSquareIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Valutazioni</span>
            </router-link>
          </li>
          <!-- Consegne -->
          <li class="mb-2">
            <router-link :to="{ name: 'delivery' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <InboxArrowDownIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Consegne</span>
            </router-link>
          </li>
          <!-- Progressi -->
          <li class="mb-2">
            <router-link :to="{ name: 'student-progress' }" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <ChartBarIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Progressi</span>
            </router-link>
          </li>
          <!-- Lezioni (Link Esterno) -->
          <li class="mb-2">
            <a :href="lessonsAppUrl" class="flex items-center p-2 rounded hover:bg-secondary-light">
              <BookOpenIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Lezioni</span>
            </a>
          </li>
        </ul>
      </nav>

      <!-- Logout Desktop -->
       <div class="p-4 mt-auto border-t border-secondary-light flex-shrink-0">
         <button @click="handleLogout" class="w-full flex items-center p-2 rounded hover:bg-error">
           <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
           <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Logout</span>
         </button>
       </div>
    </aside>

    <!-- Sidebar Mobile (Overlay) - Mostra solo se autenticato E non sulla landing page -->
    <div v-if="isMobileMenuOpen && sharedAuth.isAuthenticated && route.name !== 'landing'" class="md:hidden" role="dialog" aria-modal="true">
      <!-- Overlay Sfondo -->
      <div class="fixed inset-0 bg-gray-600 bg-opacity-75 z-30" @click="toggleMobileMenu"></div>

      <!-- Contenuto Sidebar Mobile -->
      <aside class="fixed inset-y-0 left-0 z-40 w-64 bg-secondary text-neutral-lightest flex flex-col transition-transform duration-300 ease-in-out transform"
             :class="isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'">
        <!-- Logo/Titolo App e Bottone Chiusura -->
        <div class="h-16 flex items-center justify-between flex-shrink-0 px-4">
          <span class="text-xl font-semibold">Teacher Portal</span>
          <button @click="toggleMobileMenu" class="p-1 text-neutral-lightest hover:bg-secondary-light rounded">
            <span class="sr-only">Chiudi menu</span>
            <XMarkIcon class="h-6 w-6" />
          </button>
        </div>

        <!-- Navigazione Mobile -->
        <nav class="flex-grow p-4 overflow-y-auto">
          <ul>
            <!-- Dashboard -->
            <li class="mb-2">
              <router-link :to="{ name: 'dashboard' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <HomeIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Dashboard</span>
              </router-link>
            </li>
            <!-- Studenti -->
            <li class="mb-2">
              <router-link :to="{ name: 'students' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <UsersIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Studenti</span>
              </router-link>
            </li>
            <!-- Gruppi Studenti (NUOVO) -->
            <li class="mb-2">
              <router-link :to="{ name: 'GroupsList' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <UserGroupIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Gruppi</span>
              </router-link>
            </li>
            <!-- Sfoglia Gruppi Pubblici -->
            <li class="mb-2">
              <router-link :to="{ name: 'BrowseGroups' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <MagnifyingGlassIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Sfoglia Gruppi</span>
              </router-link>
            </li>
             <!-- Quiz Templates -->
            <li class="mb-2">
              <router-link :to="{ name: 'quiz-templates' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <ClipboardDocumentListIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Quiz Templates</span>
              </router-link>
            </li>
            <!-- Template Percorsi - Temporarily Hidden -->
            <!--
            <li class="mb-2">
              <router-link :to="{ name: 'pathway-templates' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <MapIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Template Percorsi</span>
              </router-link>
            </li>
            -->
            <!-- Quiz Assegnati -->
            <li class="mb-2">
              <router-link :to="{ name: 'assigned-quizzes' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <ClipboardDocumentCheckIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Quiz Assegnati</span>
              </router-link>
            </li>
            <!-- Percorsi Assegnati - Temporarily Hidden -->
            <!--
            <li class="mb-2">
              <router-link :to="{ name: 'assigned-pathways' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <MapPinIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Percorsi Assegnati</span>
              </router-link>
            </li>
            -->
            <!-- Ricompense -->
            <li class="mb-2">
              <router-link :to="{ name: 'rewards' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <GiftIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Ricompense</span>
              </router-link>
            </li>
            <!-- Assegna -->
            <li class="mb-2">
              <router-link :to="{ name: 'assign' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <PaperAirplaneIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Assegna</span>
              </router-link>
            </li>
            <!-- Valutazioni -->
            <li class="mb-2">
              <router-link :to="{ name: 'grading' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <PencilSquareIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Valutazioni</span>
              </router-link>
            </li>
            <!-- Consegne -->
            <li class="mb-2">
              <router-link :to="{ name: 'delivery' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <InboxArrowDownIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Consegne</span>
              </router-link>
            </li>
            <!-- Progressi -->
            <li class="mb-2">
              <router-link :to="{ name: 'student-progress' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <ChartBarIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Progressi</span>
              </router-link>
            </li>
            <!-- Lezioni (Link Esterno) -->
            <li class="mb-2">
              <a :href="lessonsAppUrl" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light">
                <BookOpenIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Lezioni</span>
              </a>
            </li>
          </ul>
        </nav>

        <!-- Logout Mobile -->
        <div class="p-4 mt-auto border-t border-secondary-light flex-shrink-0">
          <button @click="handleLogout(); toggleMobileMenu();" class="w-full flex items-center p-2 rounded hover:bg-error">
            <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
            <span class="ml-3">Logout</span>
          </button>
        </div>
      </aside>
    </div>

    <!-- Contenuto Principale -->
    <div class="flex flex-col flex-grow">
        <!-- Header - Mostra solo se autenticato E non sulla landing page -->
        <header v-if="sharedAuth.isAuthenticated && route.name !== 'landing'" class="bg-white shadow p-4 h-16 flex items-center justify-between flex-shrink-0">
             <!-- Pulsante Hamburger (visibile solo su mobile) -->
             <button @click="toggleMobileMenu" class="md:hidden p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-inset focus:ring-purple-500">
               <span class="sr-only">Apri menu principale</span>
               <Bars3Icon class="h-6 w-6" />
             </button>

             <!-- Placeholder per Titolo Pagina o Spazio -->
             <div class="flex-1 md:ml-4"></div>

             <!-- Pulsanti Header -->
             <div class="flex items-center space-x-4">
                 <!-- Pulsante Notifiche -->
                 <button class="p-2 rounded-full text-neutral-dark hover:text-neutral-darker hover:bg-neutral-light focus:outline-none focus:bg-neutral-light focus:ring-2 focus:ring-offset-2 focus:ring-primary">
                     <span class="sr-only">View notifications</span>
                     <BellIcon class="h-6 w-6" />
                 </button>

                 <!-- Pulsante Profilo (Link diretto) -->
                 <button @click="goToProfile" class="p-1 rounded-full text-neutral-dark hover:text-neutral-darker focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary">
                     <span class="sr-only">Vai al profilo</span>
                     <UserCircleIcon class="h-7 w-7" />
                 </button>
             </div>
        </header>
        <!-- Se non autenticato, mostra solo il contenuto senza header -->
        <header v-else class="h-0"></header> <!-- Placeholder per mantenere struttura flex -->

        <!-- Area Contenuto -->
        <!-- Aggiunto padding-top solo se header è visibile (autenticato e non su landing) -->
        <!-- Applica padding-top sempre se autenticato, per evitare che il contenuto vada sotto eventuali barre fisse -->
        <main class="flex-grow p-4 md:p-8 overflow-auto" :class="{ 'pt-20': sharedAuth.isAuthenticated }">
          <RouterView />
        </main>

        <!-- Footer Component -->
        <AppFooter @openPrivacy="openPrivacyModal" @openCookie="openCookieModal" />
    </div>

  </div>
</template>

<style scoped>
/* Stili aggiuntivi se necessari */
.router-link-exact-active {
  @apply bg-secondary-light; /* Stile per link attivo nella sidebar aggiornato */
}
/* Stile specifico per il bottone logout hover (già gestito inline) */
/* div > button.hover\:bg-red-700:hover {
   @apply bg-error;
} */
</style>