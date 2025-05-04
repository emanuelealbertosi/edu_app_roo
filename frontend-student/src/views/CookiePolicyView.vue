<template>
  <div class="container mx-auto px-4 py-8">
    <div class="prose max-w-none bg-white p-6 rounded shadow-md" v-html="cookiePolicyHtml"></div>
    <div class="mt-6 text-center">
      <router-link :to="{ name: 'root' }" class="text-indigo-600 hover:text-indigo-800">
        Torna alla Home
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { marked } from 'marked';

// Contenuto Markdown della Cookie Policy (copiato da App.vue per semplicità)
// Idealmente, questo potrebbe essere caricato da un file .md o da un API
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

const cookiePolicyHtml = ref('');

onMounted(async () => {
  // Usa Promise.resolve per simulare un caricamento asincrono se necessario in futuro
  cookiePolicyHtml.value = await Promise.resolve(marked(cookiePolicyMarkdown));
});
</script>

<style scoped>
/* Stili per Tailwind Typography plugin (prose) - Copiati da PrivacyPolicyView */
.prose :where(h1):not(:where([class~="not-prose"] *)) {
  @apply text-3xl font-bold mb-4 text-gray-800;
}
.prose :where(h2):not(:where([class~="not-prose"] *)) {
  @apply text-2xl font-semibold mt-6 mb-3 text-gray-700 border-b pb-1;
}
.prose :where(h3):not(:where([class~="not-prose"] *)) {
  @apply text-xl font-semibold mt-5 mb-2 text-gray-700;
}
.prose :where(p):not(:where([class~="not-prose"] *)) {
  @apply mb-4 leading-relaxed;
}
.prose :where(ul):not(:where([class~="not-prose"] *)) {
  @apply list-disc pl-5 mb-4;
}
.prose :where(li):not(:where([class~="not-prose"] *)) {
  @apply mb-2;
}
.prose :where(strong):not(:where([class~="not-prose"] *)) {
  @apply font-semibold;
}
.prose :where(a):not(:where([class~="not-prose"] *)) {
  @apply text-indigo-600 hover:text-indigo-800;
}
/* Aggiungi altri stili prose se necessario */
</style>