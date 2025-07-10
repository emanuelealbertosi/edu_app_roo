<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'; // Importa watch, onMounted, onBeforeUnmount
import { useAuthStore } from '@/stores/auth'; // Store specifico Teacher (per logout e checkAuth)
import { useSharedAuthStore } from '@/stores/sharedAuth'; // Importa store condiviso
import { useAnnouncementStore } from '@/stores/announcement'; // Importa lo store degli avvisi
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router';
import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';
import BaseModal from '@/components/common/BaseModal.vue'; // CORRETTO: Importa BaseModal
import AnnouncementModal from '@/components/common/AnnouncementModal.vue'; // Importa la modale degli avvisi
import AppFooter from '@/components/layout/AppFooter.vue'; // Importa il footer
import { marked } from 'marked'; // Importa marked
import UniformNotificationDisplay from '@/components/common/UniformNotificationDisplay.vue'; // Importa il nuovo componente notifiche
import { navigateTo } from '@/utils/navigation';
import Breadcrumb from '@/components/common/Breadcrumb.vue';
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
  BookOpenIcon, // Icona generica, usata come fallback o per altre sezioni
  ArrowLeftOnRectangleIcon, // Logout
  BellIcon, // Notifiche
  Bars3Icon, // Icona Hamburger per menu mobile
  XMarkIcon, // Icona per chiudere menu mobile
  MagnifyingGlassIcon, // Icona per Sfoglia Gruppi
  TagIcon, // Per Materie
  LightBulbIcon, // Per Argomenti
  AcademicCapIcon, // Per Lezioni (già importata, ma la confermo qui per chiarezza)
  FolderIcon, // Per Corsi
  PuzzlePieceIcon, // Per UDA
  ChevronDoubleLeftIcon,
  ChevronDoubleRightIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  WrenchScrewdriverIcon
} from '@heroicons/vue/24/outline';

const authStore = useAuthStore(); // Mantenuto per azione logout specifica
const sharedAuth = useSharedAuthStore(); // Usa store condiviso per stato auth
const announcementStore = useAnnouncementStore(); // Istanzia lo store degli avvisi
const route = useRoute();
const router = useRouter();
const isMobileMenuOpen = ref(false); // Stato per menu mobile
const isSidebarExpandedState = ref(false); // Sidebar desktop espansa permanentemente
const sidebarAsideRef = ref<HTMLElement | null>(null);
const mobileMenuButtonRef = ref<HTMLElement | null>(null); // Ref per il bottone del menu mobile

// Stati per sezioni menu contraibili
const isManageQuizExpanded = ref(false);
const isGestioneDidatticaExpanded = ref(false);

const portalName = 'Portale Docente';

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

const navigateAndCloseMobileMenu = (routeName: string) => {
  navigateTo(router, routeName);
  if (isMobileMenuOpen.value) {
    toggleMobileMenu();
  }
};

// LOGGING per debug menu
watch(route, (to) => {
  console.log(`[App.vue Watch Route] Navigated to: ${to.path}, Route Name: ${String(to.name)}, IsAuthenticated: ${sharedAuth.isAuthenticated}`);
}, { immediate: true, deep: true }); // immediate per log iniziale, deep non strettamente necessario ma sicuro

// Hook onMounted per recuperare dati iniziali
// Gestione della cronologia cross-iframe

onMounted(() => {
  if (sharedAuth.isAuthenticated) {
    announcementStore.fetchAnnouncements();
  }
  // Ripristina lo stato dei menu a tendina dal sessionStorage
  const manageQuizExpanded = sessionStorage.getItem('isManageQuizExpanded');
  if (manageQuizExpanded === 'true') {
    isManageQuizExpanded.value = true;
  }
  const gestioneDidatticaExpanded = sessionStorage.getItem('isGestioneDidatticaExpanded');
  if (gestioneDidatticaExpanded === 'true') {
    isGestioneDidatticaExpanded.value = true;
  }
  // Ripristina lo stato di espansione della sidebar
  const sidebarExpanded = sessionStorage.getItem('isSidebarExpanded');
  if (sidebarExpanded === 'true') {
    isSidebarExpandedState.value = true;
  }

  // Aggiungi il listener per i messaggi dall'iframe
});

onBeforeUnmount(() => {
  // Rimuovi il listener per evitare memory leak
});

// Watch per reagire al login/logout
watch(() => sharedAuth.isAuthenticated, (isAuth) => {
  if (isAuth) {
    announcementStore.fetchAnnouncements();
  }
});

const isEffectivelyExpanded = computed(() => isSidebarExpandedState.value);

const sidebarHeaderTitle = computed(() => {
  if (isSidebarExpandedState.value) {
    return 'Contrai menu';
  } else {
    return `Espandi menu ${portalName}`;
  }
});

const toggleSidebarExpansion = () => {
  isSidebarExpandedState.value = !isSidebarExpandedState.value;
  sessionStorage.setItem('isSidebarExpanded', String(isSidebarExpandedState.value));
};

// Logica per contrarre la sidebar quando si interagisce con il contenuto principale
const handleContentInteraction = () => {
  if (isSidebarExpandedState.value) {
    isSidebarExpandedState.value = false;
  }
};

const toggleManageQuiz = () => {
  isManageQuizExpanded.value = !isManageQuizExpanded.value;
  sessionStorage.setItem('isManageQuizExpanded', String(isManageQuizExpanded.value));
};

const toggleGestioneDidattica = () => {
  isGestioneDidatticaExpanded.value = !isGestioneDidatticaExpanded.value;
  sessionStorage.setItem('isGestioneDidatticaExpanded', String(isGestioneDidatticaExpanded.value));
};

const showBreadcrumb = computed(() => {
  return !route.meta.hideHostBreadcrumb;
});
</script>

<template>
  <GlobalLoadingIndicator />
<UniformNotificationDisplay />
  <AnnouncementModal /> <!-- Aggiungi la modale degli avvisi -->
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

  <div class="flex h-screen overflow-hidden bg-neutral-lightest font-sans text-neutral-darkest">
    <!-- Sidebar Desktop (visibile da md in su) -->
    <!-- Mostra sidebar solo se autenticato E non sulla landing page -->
    <aside
      v-if="sharedAuth.isAuthenticated && route.name !== 'landing'"
      ref="sidebarAsideRef"
      :class="[
        'bg-secondary text-neutral-lightest hidden md:flex flex-col transition-all duration-300 ease-in-out',
        isSidebarExpandedState ? 'w-64' : 'w-20'
      ]"
      aria-label="Sidebar"
    >
      <!-- Logo/Titolo App -->
       <div
        @click="toggleSidebarExpansion"
        class="h-16 flex items-center justify-center flex-shrink-0 px-4 cursor-pointer"
        :title="sidebarHeaderTitle"
        >
        <span
          v-if="isEffectivelyExpanded"
          class="text-xl font-semibold whitespace-nowrap mr-2 transition-opacity duration-200 ease-in-out"
          :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }"
        >
          {{ portalName }}
        </span>
        <ChevronDoubleLeftIcon v-if="isSidebarExpandedState" class="h-6 w-6 flex-shrink-0" />
        <ChevronDoubleRightIcon v-else class="h-6 w-6 flex-shrink-0" />
       </div>

      <!-- Navigazione Desktop -->
      <nav class="flex-grow p-4 overflow-y-auto overflow-x-hidden">
        <ul>
          <!-- Dashboard -->
          <li class="mb-2">
            <a @click="navigateTo(router, 'dashboard')" class="flex items-center p-2 rounded hover:bg-secondary-light cursor-pointer" :class="{ 'bg-primary text-white': route.name === 'dashboard' }" title="Dashboard">
              <HomeIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Dashboard</span>
            </a>
          </li>
          <!-- Studenti -->
          <li class="mb-2">
            <a @click="navigateTo(router, 'students')" class="flex items-center p-2 rounded hover:bg-secondary-light cursor-pointer" :class="{ 'bg-primary text-white': route.name === 'students' }" title="Studenti">
              <UsersIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Studenti</span>
            </a>
          </li>
          <!-- Gruppi Studenti (NUOVO) -->
          <li class="mb-2">
            <a @click="navigateTo(router, 'GroupsList')" class="flex items-center p-2 rounded hover:bg-secondary-light cursor-pointer" :class="{ 'bg-primary text-white': route.name === 'GroupsList' }" title="Gruppi">
              <UserGroupIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Gruppi</span>
            </a>
          </li>
          <!-- Sfoglia Gruppi Pubblici -->
          <li class="mb-2">
            <a @click="navigateTo(router, 'BrowseGroups')" class="flex items-center p-2 rounded hover:bg-secondary-light cursor-pointer" :class="{ 'bg-primary text-white': route.name === 'BrowseGroups' }" title="Sfoglia Gruppi">
              <MagnifyingGlassIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Sfoglia Gruppi</span>
            </a>
          </li>
          <!-- Gestione Quiz (Contraibile) -->
          <li class="mb-2">
            <button @click="toggleManageQuiz" class="flex items-center justify-between w-full p-2 rounded hover:bg-secondary-light" title="Gestione Quiz" :aria-expanded="isManageQuizExpanded">
              <div class="flex items-center">
                <WrenchScrewdriverIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Gestione Quiz</span>
              </div>
              <ChevronDownIcon v-if="!isManageQuizExpanded" class="h-4 w-4 flex-shrink-0 transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }" />
              <ChevronUpIcon v-else class="h-4 w-4 flex-shrink-0 transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }" />
            </button>
            <ul v-if="isManageQuizExpanded" class="pl-4 mt-1">
              <!-- Quiz Templates -->
              <li class="mb-2">
                <a @click="navigateTo(router, 'quiz-templates')" class="flex items-center p-2 rounded hover:bg-secondary-light cursor-pointer" :class="{ 'bg-primary text-white': route.name === 'quiz-templates' }" title="Quiz Templates">
                  <ClipboardDocumentListIcon class="h-5 w-5 flex-shrink-0" />
                  <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Quiz Templates</span>
                </a>
              </li>
              <!-- Quiz Assegnati -->
              <li class="mb-2">
                <a @click="navigateTo(router, 'assigned-quizzes')" class="flex items-center p-2 rounded hover:bg-secondary-light cursor-pointer" :class="{ 'bg-primary text-white': route.name === 'assigned-quizzes' }" title="Quiz Assegnati">
                  <ClipboardDocumentCheckIcon class="h-5 w-5 flex-shrink-0" />
                  <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Quiz Assegnati</span>
                </a>
              </li>
              <!-- Ricompense -->
              <li class="mb-2">
                <a @click="navigateTo(router, 'rewards')" class="flex items-center p-2 rounded hover:bg-secondary-light cursor-pointer" :class="{ 'bg-primary text-white': route.name === 'rewards' }" title="Ricompense">
                  <GiftIcon class="h-5 w-5 flex-shrink-0" />
                  <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Ricompense</span>
                </a>
              </li>
              <!-- Valutazioni -->
              <li class="mb-2">
                <a @click="navigateTo(router, 'GradingDashboard')" class="flex items-center p-2 rounded hover:bg-secondary-light cursor-pointer" :class="{ 'bg-primary text-white': route.name === 'GradingDashboard' }" title="Valutazioni">
                  <PencilSquareIcon class="h-5 w-5 flex-shrink-0" />
                  <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Valutazioni</span>
                </a>
              </li>
              <!-- Consegne -->
              <li class="mb-2">
                <a @click="navigateTo(router, 'delivery')" class="flex items-center p-2 rounded hover:bg-secondary-light cursor-pointer" :class="{ 'bg-primary text-white': route.name === 'delivery' }" title="Consegne">
                  <InboxArrowDownIcon class="h-5 w-5 flex-shrink-0" />
                  <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Consegne</span>
                </a>
              </li>
              <!-- Progressi -->
              <li class="mb-2">
                <a @click="navigateTo(router, 'student-progress')" class="flex items-center p-2 rounded hover:bg-secondary-light cursor-pointer" :class="{ 'bg-primary text-white': route.name === 'student-progress' }" title="Progressi">
                  <ChartBarIcon class="h-5 w-5 flex-shrink-0" />
                  <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Progressi</span>
                </a>
              </li>
            </ul>
          </li>
          <!-- Template Percorsi - Temporarily Hidden -->
          <!--
          <li class="mb-2">
            <router-link :to="{ name: 'pathway-templates' }" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Template Percorsi">
              <MapIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Template Percorsi</span>
            </router-link>
          </li>
          -->
          <!-- Percorsi Assegnati - Temporarily Hidden -->
          <!--
          <li class="mb-2">
            <router-link :to="{ name: 'assigned-pathways' }" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Percorsi Assegnati">
              <MapPinIcon class="h-5 w-5 flex-shrink-0" />
              <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Percorsi Assegnati</span>
            </router-link>
          </li>
          -->
          <!-- Sezione Gestione Didattica (Contraibile) -->
          <li class="mt-4 mb-1">
            <button @click="toggleGestioneDidattica" class="flex items-center justify-between w-full p-2 rounded hover:bg-secondary-light" title="Gestione Didattica" :aria-expanded="isGestioneDidatticaExpanded">
              <div class="flex items-center">
                <BookOpenIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Gestione Didattica</span>
              </div>
              <ChevronDownIcon v-if="!isGestioneDidatticaExpanded" class="h-4 w-4 flex-shrink-0 text-neutral-400 transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }" />
              <ChevronUpIcon v-else class="h-4 w-4 flex-shrink-0 text-neutral-400 transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }" />
            </button>
            <ul v-if="isGestioneDidatticaExpanded" class="pl-4 mt-1">
              <li class="mb-2">
                <a @click="navigateTo(router, 'EmbeddedTeacherSubjects')" class="flex items-center p-2 rounded hover:bg-secondary-light cursor-pointer" :class="{ 'bg-primary text-white': route.name === 'EmbeddedTeacherSubjects' }" title="Materie">
                  <TagIcon class="h-5 w-5 flex-shrink-0" />
                  <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Materie</span>
                </a>
              </li>
              <li class="mb-2">
                <a @click="navigateTo(router, 'EmbeddedTeacherLessonsList')" class="flex items-center p-2 rounded hover:bg-secondary-light cursor-pointer" :class="{ 'bg-primary text-white': route.name === 'EmbeddedTeacherLessonsList' }" title="Lezioni">
                  <AcademicCapIcon class="h-5 w-5 flex-shrink-0" />
                  <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Lezioni</span>
                </a>
              </li>
              <li class="mb-2">
                <a @click="navigateTo(router, 'EmbeddedTeacherCourses')" class="flex items-center p-2 rounded hover:bg-secondary-light cursor-pointer" :class="{ 'bg-primary text-white': route.name === 'EmbeddedTeacherCourses' }" title="Corsi">
                  <FolderIcon class="h-5 w-5 flex-shrink-0" />
                  <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Corsi</span>
                </a>
              </li>
              <li class="mb-2">
                <a @click="navigateTo(router, 'EmbeddedTeacherUdas')" class="flex items-center p-2 rounded hover:bg-secondary-light cursor-pointer" :class="{ 'bg-primary text-white': route.name === 'EmbeddedTeacherUdas' }" title="UDA">
                  <PuzzlePieceIcon class="h-5 w-5 flex-shrink-0" />
                  <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">UDA</span>
                </a>
              </li>
            </ul>
          </li>
        </ul>
      </nav>

      <!-- Logout Desktop -->
       <div class="p-4 mt-auto border-t border-secondary-light flex-shrink-0">
         <button @click="handleLogout" class="w-full flex items-center p-2 rounded hover:bg-error" title="Logout">
           <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
           <span class="ml-3 whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Logout</span>
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
          <span class="text-xl font-semibold">{{ portalName }}</span>
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
              <router-link :to="{ name: 'dashboard' }" @click="forceNavigateAndCloseMobileMenu({ name: 'dashboard' })" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Dashboard">
                <HomeIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Dashboard</span>
              </router-link>
            </li>
            <!-- Studenti -->
            <li class="mb-2">
              <router-link :to="{ name: 'students' }" @click="forceNavigateAndCloseMobileMenu({ name: 'students' })" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Studenti">
                <UsersIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Studenti</span>
              </router-link>
            </li>
            <!-- Gruppi Studenti (NUOVO) -->
            <li class="mb-2">
              <router-link :to="{ name: 'GroupsList' }" @click="forceNavigateAndCloseMobileMenu({ name: 'GroupsList' })" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Gruppi">
                <UserGroupIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Gruppi</span>
              </router-link>
            </li>
            <!-- Sfoglia Gruppi Pubblici -->
            <li class="mb-2">
              <router-link :to="{ name: 'BrowseGroups' }" @click="forceNavigateAndCloseMobileMenu({ name: 'BrowseGroups' })" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Sfoglia Gruppi">
                <MagnifyingGlassIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Sfoglia Gruppi</span>
              </router-link>
            </li>
            <!-- Gestione Quiz (Contraibile) -->
            <li class="mb-2">
              <button @click="toggleManageQuiz" class="flex items-center justify-between w-full p-2 rounded hover:bg-secondary-light" title="Gestione Quiz" :aria-expanded="isManageQuizExpanded">
                <div class="flex items-center">
                  <WrenchScrewdriverIcon class="h-5 w-5 flex-shrink-0" />
                  <span class="ml-3 text-sm">Gestione Quiz</span>
                </div>
                <ChevronDownIcon v-if="!isManageQuizExpanded" class="h-4 w-4 flex-shrink-0" />
                <ChevronUpIcon v-else class="h-4 w-4 flex-shrink-0" />
              </button>
              <ul v-if="isManageQuizExpanded" class="pl-4 mt-1">
                <!-- Quiz Templates -->
                <li class="mb-2">
                  <router-link :to="{ name: 'quiz-templates' }" @click="forceNavigateAndCloseMobileMenu({ name: 'quiz-templates' })" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Quiz Templates">
                    <ClipboardDocumentListIcon class="h-5 w-5 flex-shrink-0" />
                    <span class="ml-3 text-sm">Quiz Templates</span>
                  </router-link>
                </li>
                <!-- Quiz Assegnati -->
                <li class="mb-2">
                  <router-link :to="{ name: 'assigned-quizzes' }" @click="forceNavigateAndCloseMobileMenu({ name: 'assigned-quizzes' })" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Quiz Assegnati">
                    <ClipboardDocumentCheckIcon class="h-5 w-5 flex-shrink-0" />
                    <span class="ml-3 text-sm">Quiz Assegnati</span>
                  </router-link>
                </li>
                <!-- Ricompense -->
                <li class="mb-2">
                  <router-link :to="{ name: 'rewards' }" @click="forceNavigateAndCloseMobileMenu({ name: 'rewards' })" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Ricompense">
                    <GiftIcon class="h-5 w-5 flex-shrink-0" />
                    <span class="ml-3 text-sm">Ricompense</span>
                  </router-link>
                </li>
                <!-- Valutazioni -->
                <li class="mb-2">
                  <router-link :to="{ name: 'GradingDashboard' }" @click="forceNavigateAndCloseMobileMenu({ name: 'GradingDashboard' })" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Valutazioni">
                    <PencilSquareIcon class="h-5 w-5 flex-shrink-0" />
                    <span class="ml-3 text-sm">Valutazioni</span>
                  </router-link>
                </li>
                <!-- Consegne -->
                <li class="mb-2">
                  <router-link :to="{ name: 'delivery' }" @click="forceNavigateAndCloseMobileMenu({ name: 'delivery' })" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Consegne">
                    <InboxArrowDownIcon class="h-5 w-5 flex-shrink-0" />
                    <span class="ml-3 text-sm">Consegne</span>
                  </router-link>
                </li>
                <!-- Progressi -->
                <li class="mb-2">
                  <router-link :to="{ name: 'student-progress' }" @click="forceNavigateAndCloseMobileMenu({ name: 'student-progress' })" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Progressi">
                    <ChartBarIcon class="h-5 w-5 flex-shrink-0" />
                    <span class="ml-3 text-sm">Progressi</span>
                  </router-link>
                </li>
              </ul>
            </li>
            <!-- Template Percorsi - Temporarily Hidden -->
            <!--
            <li class="mb-2">
              <router-link :to="{ name: 'pathway-templates' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Template Percorsi">
                <MapIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Template Percorsi</span>
              </router-link>
            </li>
            -->
            <!-- Percorsi Assegnati - Temporarily Hidden -->
            <!--
            <li class="mb-2">
              <router-link :to="{ name: 'assigned-pathways' }" @click="toggleMobileMenu" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Percorsi Assegnati">
                <MapPinIcon class="h-5 w-5 flex-shrink-0" />
                <span class="ml-3 text-sm">Percorsi Assegnati</span>
              </router-link>
            </li>
            -->
            <!-- Sezione Gestione Didattica (Contraibile) -->
            <li class="mt-4 mb-1">
              <button @click="toggleGestioneDidattica" class="flex items-center justify-between w-full p-2 rounded hover:bg-secondary-light" title="Gestione Didattica" :aria-expanded="isGestioneDidatticaExpanded">
                <div class="flex items-center">
                  <BookOpenIcon class="h-5 w-5 flex-shrink-0" />
                  <span class="ml-3 text-sm">Gestione Didattica</span>
                </div>
                <ChevronDownIcon v-if="!isGestioneDidatticaExpanded" class="h-4 w-4 flex-shrink-0 text-neutral-400" />
                <ChevronUpIcon v-else class="h-4 w-4 flex-shrink-0 text-neutral-400" />
              </button>
              <ul v-if="isGestioneDidatticaExpanded" class="pl-4 mt-1">
                <li class="mb-2">
                  <router-link :to="{ name: 'EmbeddedTeacherSubjects' }" @click="forceNavigateAndCloseMobileMenu({ name: 'EmbeddedTeacherSubjects' })" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Materie">
                    <TagIcon class="h-5 w-5 flex-shrink-0" />
                    <span class="ml-3 text-sm">Materie</span>
                  </router-link>
                </li>
                <li class="mb-2">
                  <router-link :to="{ name: 'EmbeddedTeacherLessonsList' }" @click="forceNavigateAndCloseMobileMenu({ name: 'EmbeddedTeacherLessonsList' })" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Lezioni">
                    <AcademicCapIcon class="h-5 w-5 flex-shrink-0" />
                    <span class="ml-3 text-sm">Lezioni</span>
                  </router-link>
                </li>
                <li class="mb-2">
                  <router-link :to="{ name: 'EmbeddedTeacherCourses' }" @click="forceNavigateAndCloseMobileMenu({ name: 'EmbeddedTeacherCourses' })" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Corsi">
                    <FolderIcon class="h-5 w-5 flex-shrink-0" />
                    <span class="ml-3 text-sm">Corsi</span>
                  </router-link>
                </li>
                <li class="mb-2">
                  <router-link :to="{ name: 'EmbeddedTeacherUdas' }" @click="forceNavigateAndCloseMobileMenu({ name: 'EmbeddedTeacherUdas' })" class="flex items-center p-2 rounded hover:bg-secondary-light" title="UDA">
                    <PuzzlePieceIcon class="h-5 w-5 flex-shrink-0" />
                    <span class="ml-3 text-sm">UDA</span>
                  </router-link>
                </li>
              </ul>
            </li>
          </ul>
        </nav>

        <!-- Logout Mobile -->
        <div class="p-4 mt-auto border-t border-secondary-light flex-shrink-0">
          <button @click="handleLogout(); toggleMobileMenu();" class="w-full flex items-center p-2 rounded hover:bg-error" title="Logout">
            <ArrowLeftOnRectangleIcon class="h-6 w-6 flex-shrink-0" />
            <span class="ml-3">Logout</span>
          </button>
        </div>
      </aside>
    </div>

    <div class="flex flex-col flex-1">
      <!-- Header -->
      <header v-if="sharedAuth.isAuthenticated && route.name !== 'landing'" class="bg-white shadow p-4 h-16 flex items-center justify-between flex-shrink-0">
           <!-- Pulsante Hamburger (visibile solo su mobile) -->
           <button
              ref="mobileMenuButtonRef"
              @click="toggleMobileMenu"
              class="md:hidden p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-inset focus:ring-purple-500"
            >
             <span class="sr-only">Apri menu principale</span>
             <Bars3Icon class="h-6 w-6" />
           </button>

           <!-- Placeholder per Titolo Pagina o Spazio (su desktop occupa spazio, su mobile no) -->
           <div class="flex-1 md:ml-4">
              <!-- <h1 v-if="route.meta.title" class="text-xl font-semibold text-gray-800">{{ route.meta.title }}</h1> -->
           </div>

           <!-- Pulsanti Header (Profilo, Logout) -->
           <div class="flex items-center space-x-3">
              <button @click="goToProfile" class="flex items-center p-2 rounded text-gray-600 hover:bg-gray-100 hover:text-gray-800" title="Profilo">
                  <UserCircleIcon class="h-6 w-6" />
                  <span class="ml-2 text-sm hidden sm:inline">{{ sharedAuth.user?.email }}</span>
              </button>
              <!-- Logout Button - Hidden on Desktop Sidebar, shown here for consistency if needed or for smaller screens before mobile menu kicks in -->
              <!-- <button @click="handleLogout" class="hidden sm:flex items-center p-2 rounded text-gray-600 hover:bg-red-100 hover:text-red-700" title="Logout">
                  <ArrowLeftOnRectangleIcon class="h-6 w-6" />
                  <span class="ml-2 text-sm hidden md:inline">Logout</span>
              </button> -->
           </div>
      </header>
      <!-- Se non autenticato o sulla landing page, mostra solo il contenuto senza header -->
      <header v-else class="h-0"></header> <!-- Placeholder per mantenere struttura flex -->

      <!-- Area Contenuto -->
      <main class="flex-1 p-4 md:p-8 overflow-y-auto">
        <Breadcrumb v-if="showBreadcrumb" />
        <RouterView />
      </main>

      <!-- Footer Component -->
      <AppFooter @openPrivacy="openPrivacyModal" @openCookie="openCookieModal" class="flex-shrink-0" />
    </div>

  </div>
</template>

<style scoped>
/* Stili per link attivi e hover nella sidebar */
.router-link-exact-active {
  @apply bg-secondary-light; /* Usa il colore light della sidebar per l'attivo */
}

/* Stili aggiuntivi per la transizione dell'opacità e del testo */
.group:hover .opacity-0 {
  opacity: 1;
}
</style>
]]>