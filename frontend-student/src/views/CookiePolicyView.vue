<template>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-6">Informativa sui Cookie</h1>
    <!-- Utilizza v-html per renderizzare l'HTML generato da marked -->
    <div class="prose max-w-none" v-html="cookiePolicyHtml"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { marked } from 'marked'; // Importa la libreria marked

// Contenuto del file cookie_policy.md
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

// Ref per contenere l'HTML convertito
const cookiePolicyHtml = ref('');

onMounted(async () => {
  // Converte il Markdown in HTML quando il componente è montato
  cookiePolicyHtml.value = await Promise.resolve(marked(cookiePolicyMarkdown));
});
</script>

<style scoped>
/* Stili per migliorare la leggibilità del contenuto Markdown convertito */
.prose :deep(h1),
.prose :deep(h2),
.prose :deep(h3) {
  margin-bottom: 0.5em;
  margin-top: 1em;
}

.prose :deep(ul) {
  list-style-type: disc;
  margin-left: 1.5em;
}

.prose :deep(p) {
    margin-bottom: 0.75em;
}

.prose :deep(a) {
    color: #2563eb; /* Blu Tailwind */
    text-decoration: underline;
}

.prose :deep(a:hover) {
    color: #1d4ed8; /* Blu Tailwind più scuro */
}
</style>