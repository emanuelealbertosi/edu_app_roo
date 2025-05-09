<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'; // Aggiunto onMounted
import { useAuthStore } from '@/stores/auth';
import { useNotificationStore } from '@/stores/notification'; // Aggiunto NotificationStore
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router';
import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';
import NotificationContainer from '@/components/common/NotificationContainer.vue';
import ModalDialog from '@/components/common/ModalDialog.vue'; // Importa la modale
import AppFooter from '@/components/layout/AppFooter.vue'; // Importa il nuovo footer
import { marked } from 'marked'; // Importa marked
import {
  HomeIcon, ShoppingCartIcon, UserCircleIcon, CreditCardIcon, TrophyIcon,
  BookOpenIcon, ArrowLeftOnRectangleIcon, BellIcon, Bars3Icon, XMarkIcon
} from '@heroicons/vue/24/outline';

const authStore = useAuthStore();
const notificationStore = useNotificationStore(); // Istanziato NotificationStore
const route = useRoute();
const router = useRouter();
const isMobileMenuOpen = ref(false);
const isNotificationsOpen = ref(false); // Stato per il dropdown delle notifiche

// Stato per la modale
const isModalOpen = ref(false);
const modalTitle = ref('');
const modalContentHtml = ref('');

// Contenuti Markdown (incollati per semplicità, idealmente andrebbero caricati)
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
    *   **Finalità:** Consentirti di registrarti, accedere e utilizzare le funzionalità dell'Applicazione, inclusa la partecipazione a quiz, la gestione del profilo, l'accumulo di punti, l'acquisto di premi e l'interazione con gruppi (se applicabile).
    *   **Base Giuridica:** Esecuzione di un contratto di cui sei parte (i Termini di Servizio dell'Applicazione) (Art. 6.1.b GDPR).
    *   **Dati Trattati:** Nome, cognome, indirizzo email, password (hashata), dati relativi ai progressi educativi (quiz completati, punteggi), punti accumulati, premi acquistati, appartenenza a gruppi (se applicabile), timestamp di accettazione delle policy.
*   **b) Gestione del consenso e adempimenti legali:**
    *   **Finalità:** Registrare e gestire l'accettazione dei Termini di Servizio e della presente Informativa Privacy; gestire le richieste di esercizio dei tuoi diritti; adempiere a obblighi legali, contabili o fiscali.
    *   **Base Giuridica:** Adempimento di un obbligo legale (Art. 6.1.c GDPR); Esecuzione di un contratto (Art. 6.1.b GDPR) per la registrazione dell'accettazione.
    *   **Dati Trattati:** Timestamp di accettazione, dati necessari per gestire le richieste (es. email per identificazione).
*   **c) Sicurezza e prevenzione frodi:**
    *   **Finalità:** Garantire la sicurezza dell'Applicazione e dei dati, prevenire attività fraudolente o abusi.
    *   **Base Giuridica:** Legittimo interesse del Titolare (Art. 6.1.f GDPR) a proteggere i propri sistemi e utenti, a condizione che non prevalgano i tuoi interessi o diritti e libertà fondamentali.
    *   **Dati Trattati:** Indirizzi IP (anonimizzati prima del logging, se loggati), log di accesso (anonimizzati), dati di utilizzo aggregati.
*   **d) Gestione del consenso parentale (per utenti minori):**
    *   **Finalità:** Verificare l'età dell'utente e, se minore dell'età richiesta per il consenso digitale autonomo, ottenere e verificare il consenso del genitore o tutore legale.
    *   **Base Giuridica:** Adempimento di un obbligo legale (Art. 8 GDPR); Consenso (Art. 6.1.a GDPR) del titolare della responsabilità genitoriale.
    *   **Dati Trattati:** Data di nascita (per verifica età), dati di contatto del genitore/tutore (per ottenere consenso), prova del consenso.

## 4. Categorie di Dati Personali Trattati

Le categorie di dati personali che trattiamo includono:

*   **Dati identificativi:** Nome, cognome, indirizzo email.
*   **Dati di autenticazione:** Password (memorizzata in formato hashato e salato).
*   **Dati relativi all'utilizzo dell'Applicazione:** Progressi nei quiz, punteggi, punti fedeltà, acquisti nello shop virtuale, appartenenza a gruppi, log di attività (anonimizzati dove possibile).
*   **Dati tecnici:** Indirizzi IP (anonimizzati prima del logging), tipo di browser, sistema operativo (raccolti in forma aggregata o anonima per analisi).
*   **Dati relativi al consenso:** Timestamp di accettazione della Privacy Policy e dei Termini di Servizio, dati relativi al consenso parentale (se applicabile).
*   **Dati forniti volontariamente:** Qualsiasi altra informazione che scegli di fornire tramite form di contatto o altre interazioni.

Non trattiamo categorie particolari di dati personali (dati sensibili) ai sensi dell'Art. 9 GDPR, a meno che non sia strettamente necessario per specifiche funzionalità e previo tuo consenso esplicito o altra base giuridica idonea.

## 5. Destinatari o Categorie di Destinatari dei Dati

I tuoi dati personali potranno essere comunicati a:

*   **Personale autorizzato:** Nostri collaboratori interni autorizzati al trattamento dei dati per le finalità sopra indicate.
*   **Fornitori di servizi (Responsabili del Trattamento):** Terze parti che trattano dati per nostro conto (es. fornitori di hosting, servizi cloud, piattaforme di gestione database), vincolati da specifici accordi (Art. 28 GDPR) che ne garantiscono la conformità.
*   **Autorità pubbliche:** Ove richiesto dalla legge o per ordine dell'autorità giudiziaria o amministrativa.

Non vendiamo né cediamo i tuoi dati personali a terzi per finalità di marketing.

## 6. Trasferimento Dati Extra-UE

I tuoi dati personali sono trattati principalmente all'interno dell'Unione Europea (UE) o dello Spazio Economico Europeo (SEE). Non vengono effettuati trasferimenti dei tuoi dati personali al di fuori dell'UE/SEE. Qualora in futuro dovesse rendersi necessario un trasferimento, adotteremo tutte le garanzie adeguate previste dal GDPR (es. decisioni di adeguatezza, clausole contrattuali standard).

## 7. Periodo di Conservazione dei Dati

Conserviamo i tuoi dati personali solo per il tempo strettamente necessario a conseguire le finalità per cui sono stati raccolti, nel rispetto degli obblighi legali e contrattuali. I criteri specifici per determinare i periodi di conservazione sono definiti nella nostra Policy di Conservazione dei Dati interna (come delineato nel punto 3.6 del Piano di Conformità GDPR) e includono:

*   **Dati dell'account utente:** Conservati finché l'account è attivo e per un periodo definito dopo la cancellazione richiesta o l'inattività, salvo obblighi legali che richiedano una conservazione più lunga.
*   **Dati relativi all'esecuzione del contratto (es. acquisti):** Conservati per il periodo necessario ad adempiere agli obblighi contrattuali e legali (es. fiscali, contabili).
*   **Log di accesso e sicurezza (anonimizzati):** Conservati per un periodo limitato necessario a garantire la sicurezza e prevenire frodi.
*   **Dati relativi al consenso:** Conservati per il periodo necessario a dimostrare l'avvenuto consenso.

Al termine del periodo di conservazione applicabile, i dati saranno cancellati in modo sicuro o resi irreversibilmente anonimi.

## 8. Diritti dell'Interessato

In qualità di interessato, hai i seguenti diritti ai sensi del GDPR, che puoi esercitare contattando il Titolare del Trattamento all'indirizzo email fornito nella Sezione 1:

*   **Diritto di Accesso (Art. 15 GDPR):** Ottenere conferma che sia o meno in corso un trattamento di dati personali che ti riguardano e, in tal caso, ottenere l'accesso ai dati e a specifiche informazioni sul trattamento. Puoi accedere ai tuoi dati principali tramite la sezione "Profilo" -> "I miei Dati" dell'Applicazione.
*   **Diritto di Rettifica (Art. 16 GDPR):** Ottenere la rettifica dei dati personali inesatti che ti riguardano senza ingiustificato ritardo. Puoi modificare alcuni dei tuoi dati (es. nome, cognome) direttamente nella sezione "Profilo" dell'Applicazione.
*   **Diritto alla Cancellazione ("Diritto all'Oblio") (Art. 17 GDPR):** Ottenere la cancellazione dei dati personali che ti riguardano senza ingiustificato ritardo, nei casi previsti dalla legge (es. i dati non sono più necessari rispetto alle finalità, revoca del consenso, trattamento illecito). Puoi richiedere la cancellazione del tuo account tramite la sezione "Profilo" dell'Applicazione. La richiesta verrà processata secondo le nostre procedure interne.
*   **Diritto di Limitazione del Trattamento (Art. 18 GDPR):** Ottenere la limitazione del trattamento quando ricorrono determinate ipotesi (es. contestazione dell'esattezza dei dati, trattamento illecito, opposizione al trattamento).
*   **Diritto alla Portabilità dei Dati (Art. 20 GDPR):** Ricevere in un formato strutturato, di uso comune e leggibile da dispositivo automatico i dati personali che ti riguardano forniti al Titolare e avere il diritto di trasmettere tali dati a un altro titolare, nei casi previsti dalla legge. Puoi scaricare i tuoi dati principali in formato JSON tramite la sezione "Profilo" -> "I miei Dati" dell'Applicazione.
*   **Diritto di Opposizione (Art. 21 GDPR):** Opporti in qualsiasi momento, per motivi connessi alla tua situazione particolare, al trattamento dei dati personali che ti riguardano basato sul legittimo interesse (Art. 6.1.f GDPR).

## 9. Modalità di Esercizio dei Diritti

Puoi esercitare i tuoi diritti:

*   **Tramite l'Applicazione:** Per Accesso, Rettifica (parziale), Cancellazione (richiesta) e Portabilità, utilizza le funzionalità dedicate nella sezione "Profilo".
*   **Via Email:** Per tutti i diritti, inclusi Limitazione e Opposizione, o per richieste più specifiche, contatta il Titolare all'indirizzo email: emanuele.albertosi@gmail.com.

Risponderemo alla tua richiesta nel più breve tempo possibile e, comunque, entro un mese dal ricevimento. Tale termine può essere prorogato di due mesi, se necessario, tenuto conto della complessità e del numero delle richieste.

## 10. Diritto di Revocare il Consenso

Qualora il trattamento sia basato sul consenso (Art. 6.1.a o Art. 9.2.a GDPR), hai il diritto di revocare il tuo consenso in qualsiasi momento, senza pregiudicare la liceità del trattamento basata sul consenso prestato prima della revoca. La revoca del consenso all'accettazione della Privacy Policy e dei Termini di Servizio comporterà l'impossibilità di continuare a utilizzare l'Applicazione.

## 11. Diritto di Proporre Reclamo all'Autorità di Controllo

Se ritieni che il trattamento dei tuoi dati personali avvenga in violazione del GDPR, hai il diritto di proporre reclamo all'Autorità Garante per la protezione dei dati personali competente (per l'Italia, il Garante per la Protezione dei Dati Personali, www.gpdp.it) o all'autorità di controllo dello Stato membro in cui risiedi abitualmente, lavori oppure del luogo ove si è verificata la presunta violazione (Art. 77 GDPR).

## 12. Natura Obbligatoria o Facoltativa del Conferimento dei Dati

Il conferimento dei dati richiesti per la registrazione (nome, cognome, email, password) e l'accettazione della presente Informativa e dei Termini di Servizio è necessario per poter utilizzare l'Applicazione (Base Giuridica: Esecuzione Contratto). Il mancato conferimento comporta l'impossibilità di creare un account e accedere ai servizi. Il conferimento di altri dati potrebbe essere facoltativo e necessario solo per usufruire di specifiche funzionalità aggiuntive.

## 13. Esistenza di Processi Decisionali Automatizzati

Non utilizziamo processi decisionali interamente automatizzati, inclusa la profilazione, che producano effetti giuridici che ti riguardano o che incidano in modo analogo significativamente sulla tua persona (Art. 22 GDPR).

## 14. Modifiche alla Presente Informativa

Ci riserviamo il diritto di aggiornare la presente Informativa sulla Privacy. Qualsiasi modifica sarà pubblicata sull'Applicazione e, se sostanziale, ti sarà notificata. Ti invitiamo a consultare regolarmente questa pagina per rimanere informato sulle nostre pratiche di privacy.
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

// Funzioni per aprire la modale
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
const lessonsAppUrl = computed(() => (import.meta.env.VITE_LESSONS_APP_URL as string | undefined) || '/lezioni/');

const toggleMobileMenu = () => { isMobileMenuOpen.value = !isMobileMenuOpen.value; };

const publicRouteNames = ['login', 'StudentRegistration', 'root'];

const showLayout = computed(() => {
  const currentRouteName = route.name;
  return currentRouteName !== null && currentRouteName !== undefined && !publicRouteNames.includes(currentRouteName.toString());
});

const handleLogout = () => {
  authStore.logout();
};

const goToProfile = () => {
  router.push({ name: 'Profile' });
};

const toggleNotificationsDropdown = () => {
  isNotificationsOpen.value = !isNotificationsOpen.value;
  if (isNotificationsOpen.value && authStore.isAuthenticated) {
    // Ricarica le notifiche quando il dropdown viene aperto,
    // per assicurarsi che siano aggiornate.
    notificationStore.fetchServerNotifications();
  }
};

const handleNotificationClick = async (notification: any, routerInstance: any) => {
  if (!notification.is_read) {
    await notificationStore.markServerNotificationAsRead(notification.id);
  }
  if (notification.link) {
    routerInstance.push(notification.link);
  }
  isNotificationsOpen.value = false; // Chiudi il dropdown dopo il click
};

// Chiamata per caricare le notifiche al mount del componente
onMounted(() => {
  if (authStore.isAuthenticated) {
    notificationStore.fetchServerNotifications();
  }
});

// TODO: Aggiungere watch su authStore.isAuthenticated per caricare le notifiche dopo il login, se App.vue è già montato

</script>
<template>
  <GlobalLoadingIndicator />
  <NotificationContainer />

  <!-- Modale per le Policy -->
  <ModalDialog
    :show="isModalOpen"
    :title="modalTitle"
    :content-html="modalContentHtml"
    @close="closeModal"
  />

  <div class="flex min-h-screen bg-neutral-lightest font-sans text-neutral-darkest"> <!-- Changed h-screen to min-h-screen -->
    <!-- Sidebar Desktop (visibile da md in su) -->
    <aside
      v-if="authStore.isAuthenticated"
      class="bg-secondary text-neutral-lightest hidden md:flex flex-col w-20 group hover:w-64 transition-all duration-300 ease-in-out overflow-hidden"
      aria-label="Sidebar"
    >
      <!-- Logo/Titolo App -->
       <div class="h-16 flex items-center justify-center flex-shrink-0 px-4">
         <span class="text-xl font-semibold opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Student Portal</span>
       </div>

      <!-- Navigazione Desktop -->
      <nav class="flex-grow p-4 overflow-y-auto overflow-x-hidden">
        <ul>
          <!-- Dashboard -->
          <li class="mb-3">
            <router-link :to="{ name: 'dashboard' }" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
              <HomeIcon class="h-6 w-6 flex-shrink-0" />
              <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Dashboard</span>
            </router-link>
          </li>
          <!-- Shop -->
          <li class="mb-3">
            <router-link :to="{ name: 'shop' }" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
              <ShoppingCartIcon class="h-6 w-6 flex-shrink-0" />
              <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Shop</span>
            </router-link>
          </li>
          <!-- Acquisti -->
          <li class="mb-3">
            <router-link :to="{ name: 'purchases' }" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
              <CreditCardIcon class="h-6 w-6 flex-shrink-0" />
              <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Acquisti</span>
            </router-link>
          </li>
          <!-- Traguardi -->
          <li class="mb-3">
            <router-link :to="{ name: 'Badges' }" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
              <TrophyIcon class="h-6 w-6 flex-shrink-0" />
              <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Traguardi</span>
            </router-link>
          </li>
          <!-- Lezioni (Link Esterno) -->
          <li class="mb-3">
            <a :href="lessonsAppUrl" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
              <BookOpenIcon class="h-6 w-6 flex-shrink-0" />
              <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Lezioni</span>
            </a>
          </li>
        </ul>
      </nav>

      <!-- Logout Desktop -->
       <div class="p-4 mt-auto border-t border-purple-700 flex-shrink-0">
         <button @click="handleLogout" class="w-full flex items-center p-2 rounded text-neutral-lightest hover:bg-red-700">
           <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
           <span class="ml-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ease-in-out whitespace-nowrap">Logout</span>
         </button>
       </div>
    </aside>

    <!-- Sidebar Mobile (Overlay) -->
    <div v-if="isMobileMenuOpen && authStore.isAuthenticated" class="md:hidden" role="dialog" aria-modal="true">
      <!-- Overlay Sfondo -->
      <div class="fixed inset-0 bg-gray-600 bg-opacity-75 z-30" @click="toggleMobileMenu"></div>

      <!-- Contenuto Sidebar Mobile -->
      <aside class="fixed inset-y-0 left-0 z-40 w-64 bg-secondary text-neutral-lightest flex flex-col transition-transform duration-300 ease-in-out transform"
             :class="isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'">
        <!-- Logo/Titolo App e Bottone Chiusura -->
        <div class="h-16 flex items-center justify-between flex-shrink-0 px-4">
          <span class="text-xl font-semibold">Student Portal</span>
          <button @click="toggleMobileMenu" class="p-1 text-neutral-lightest hover:bg-purple-700 rounded">
            <span class="sr-only">Chiudi menu</span>
            <XMarkIcon class="h-6 w-6" />
          </button>
        </div>

        <!-- Navigazione Mobile -->
        <nav class="flex-grow p-4 overflow-y-auto">
          <ul>
            <!-- Dashboard -->
            <li class="mb-3">
              <router-link :to="{ name: 'dashboard' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
                <HomeIcon class="h-6 w-6 flex-shrink-0" />
                <span class="ml-3">Dashboard</span>
              </router-link>
            </li>
            <!-- Shop -->
            <li class="mb-3">
              <router-link :to="{ name: 'shop' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
                <ShoppingCartIcon class="h-6 w-6 flex-shrink-0" />
                <span class="ml-3">Shop</span>
              </router-link>
            </li>
            <!-- Acquisti -->
            <li class="mb-3">
              <router-link :to="{ name: 'purchases' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
                <CreditCardIcon class="h-6 w-6 flex-shrink-0" />
                <span class="ml-3">Acquisti</span>
              </router-link>
            </li>
            <!-- Traguardi -->
            <li class="mb-3">
              <router-link :to="{ name: 'Badges' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
                <TrophyIcon class="h-6 w-6 flex-shrink-0" />
                <span class="ml-3">Traguardi</span>
              </router-link>
            </li>
            <!-- Lezioni (Link Esterno) -->
            <li class="mb-3">
              <a :href="lessonsAppUrl" @click="toggleMobileMenu" class="flex items-center p-2 rounded text-neutral-lightest hover:bg-purple-700">
                <BookOpenIcon class="h-6 w-6 flex-shrink-0" />
                <span class="ml-3">Lezioni</span>
              </a>
            </li>
          </ul>
        </nav>

        <!-- Logout Mobile -->
        <div class="p-4 mt-auto border-t border-purple-700 flex-shrink-0">
          <button @click="handleLogout(); toggleMobileMenu();" class="w-full flex items-center p-2 rounded text-neutral-lightest hover:bg-red-700">
            <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
            <span class="ml-3">Logout</span>
          </button>
        </div>
      </aside>
    </div>

    <!-- Contenuto Principale -->
    <div class="flex flex-col flex-grow">
        <!-- Header -->
        <header v-if="authStore.isAuthenticated" class="bg-white shadow p-4 h-16 flex items-center justify-between flex-shrink-0">
             <!-- Pulsante Hamburger (visibile solo su mobile) -->
             <button @click="toggleMobileMenu" class="md:hidden p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-inset focus:ring-purple-500">
               <span class="sr-only">Apri menu principale</span>
               <Bars3Icon class="h-6 w-6" />
             </button>

             <!-- Placeholder per Titolo Pagina o Spazio (su desktop occupa spazio, su mobile no) -->
             <div class="flex-1 md:ml-4"></div>

             <!-- Pulsanti Header (Notifiche, Profilo) -->
             <div class="flex items-center space-x-4">
                 <!-- Pulsante Notifiche -->
                 <div class="relative">
                   <button @click="toggleNotificationsDropdown" class="p-2 rounded-full text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:bg-gray-100 focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
                       <span class="sr-only">View notifications</span>
                       <BellIcon class="h-6 w-6" />
                       <span v-if="notificationStore.unreadServerNotificationCount > 0" class="absolute top-0 right-0 block h-2 w-2 transform translate-x-1/2 -translate-y-1/2 rounded-full bg-red-500 ring-2 ring-white"></span>
                   </button>
                   <!-- Dropdown Notifiche -->
                   <div v-if="isNotificationsOpen" class="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg overflow-hidden z-20">
                     <div class="py-2 px-4 text-sm text-gray-700 font-semibold border-b">Notifiche</div>
                      <div v-if="notificationStore.isLoadingServerNotifications" class="p-4 text-sm text-gray-500 text-center">
                        Caricamento...
                      </div>
                      <div v-else-if="notificationStore.serverNotificationsError" class="p-4 text-sm text-red-500">
                        Errore: {{ notificationStore.serverNotificationsError }}
                      </div>
                      <div v-else-if="notificationStore.serverNotifications.length === 0" class="p-4 text-sm text-gray-500">
                        Nessuna notifica.
                      </div>
                      <ul v-else class="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                        <li v-for="notification in notificationStore.serverNotifications" :key="notification.id"
                            class="p-3 hover:bg-gray-50 cursor-pointer"
                            @click="handleNotificationClick(notification, router)">
                          <div class="flex justify-between items-center">
                            <p class="text-sm text-gray-600" :class="{'font-semibold': !notification.is_read}">{{ notification.message }}</p>
                            <span v-if="!notification.is_read" class="ml-2 h-2 w-2 bg-primary rounded-full"></span>
                          </div>
                          <p class="text-xs text-gray-400 mt-1">{{ new Date(notification.created_at).toLocaleString() }}</p>
                        </li>
                      </ul>
                      <div v-if="notificationStore.serverNotifications.length > 0 && !notificationStore.isLoadingServerNotifications && !notificationStore.serverNotificationsError" class="py-2 px-4 border-t">
                        <button
                          @click="notificationStore.markAllServerNotificationsAsRead()"
                          class="w-full text-sm text-primary hover:underline disabled:text-gray-400 disabled:no-underline"
                          :disabled="notificationStore.unreadServerNotificationCount === 0">
                          Segna tutte come lette
                        </button>
                      </div>
                   </div>
                 </div>

                 <!-- Pulsante Profilo (Link diretto) -->
                 <button @click="goToProfile" class="p-1 rounded-full text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
                     <span class="sr-only">Vai al profilo</span>
                     <UserCircleIcon class="h-7 w-7" />
                 </button>
             </div>
        </header>
        <!-- Se non autenticato, mostra solo il contenuto senza header -->
        <header v-else class="h-0"></header> <!-- Placeholder per mantenere struttura flex -->


        <!-- Area Contenuto -->
        <!-- Aggiunto padding-top se header è visibile -->
        <main class="flex-grow p-4 md:p-8 overflow-auto" :class="{ 'pt-20': authStore.isAuthenticated }">
          <RouterView />
        </main> <!-- Moved footer outside main -->

        <!-- Footer Component -->
        <AppFooter @openPrivacy="openPrivacyModal" @openCookie="openCookieModal" />
    </div>

  </div>
</template>

<style scoped>
/* Stili per link attivi e hover nella sidebar */
.router-link-exact-active {
  @apply bg-secondary-light; /* Usa il colore light della sidebar per l'attivo */
}
nav a:hover, nav button:hover {
  @apply bg-purple-700; /* Usa un viola più chiaro per hover per maggior contrasto */
}
/* Stile specifico per il bottone logout hover */
div > button.hover\:bg-red-700:hover { /* Selettore più specifico per override */
   @apply bg-error; /* Usa il colore error definito in tailwind.config */
}

/* Stili per i pulsanti dell'header */
header button {
  @apply text-neutral-dark hover:text-neutral-darker hover:bg-neutral-light focus:outline-none focus:bg-neutral-light focus:ring-2 focus:ring-offset-2 focus:ring-primary;
}
/* Stili del footer rimossi perché ora sono in AppFooter.vue */
</style>
