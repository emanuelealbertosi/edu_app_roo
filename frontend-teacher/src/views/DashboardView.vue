<script setup lang="ts">
 import { ref, onMounted, computed } from 'vue';
 import { fetchTeacherDashboardData, type TeacherDashboardData } from '@/api/dashboard';
 import { useAuthStore } from '@/stores/auth'; // Per salutare l'utente
 import QrcodeVue from 'qrcode.vue'; // Importa il componente QR code
 import { fetchGroups, type StudentGroup } from '@/api/groups'; // Importa API gruppi
 import {
   fetchRegistrationTokens,
   createRegistrationToken,
   deactivateRegistrationToken,
   deleteRegistrationToken,
   type RegistrationToken
 } from '@/api/registrationTokens'; // Importa API token

 const authStore = useAuthStore();
 const dashboardData = ref<TeacherDashboardData | null>(null);
 const isLoading = ref(false); // Loading per statistiche dashboard
 const error = ref<string | null>(null); // Errore statistiche dashboard

 // Stato per gestione token
 const tokens = ref<RegistrationToken[]>([]);
 const isLoadingTokens = ref(false);
 const tokensError = ref<string | null>(null);
 const showTokenForm = ref(false);
 const newTokenGroupId = ref<number | null>(null); // Gruppo selezionato per nuovo token
 const isCreatingToken = ref(false);
 const createTokenError = ref<string | null>(null);

 // Stato per gruppi (necessari per il form creazione token)
 const groups = ref<StudentGroup[]>([]);
 const isLoadingGroups = ref(false); // Loading separato per gruppi
 const groupsError = ref<string | null>(null); // Errore gruppi

 onMounted(() => {
   loadDashboardData();
   loadGroups(); // Carica anche i gruppi per il form
   loadRegistrationTokens();
 });

 const loadDashboardData = async () => {
    isLoading.value = true;
    error.value = null;
   try {
     dashboardData.value = await fetchTeacherDashboardData();
   } catch (err: any) {
     console.error("Errore nel caricamento dei dati dashboard:", err);
     error.value = err.message || 'Si è verificato un errore sconosciuto.';
   } finally {
     isLoading.value = false;
   }
 };

 const loadGroups = async () => {
    isLoadingGroups.value = true;
    groupsError.value = null;
    try {
      groups.value = await fetchGroups();
    } catch (err: any) {
      console.error("Errore nel recupero dei gruppi:", err);
      groupsError.value = err.message || 'Si è verificato un errore sconosciuto.';
    } finally {
      isLoadingGroups.value = false;
    }
 };

 const loadRegistrationTokens = async () => {
    isLoadingTokens.value = true;
    tokensError.value = null;
    try {
      // Filtriamo per mostrare solo quelli attivi e validi? Per ora tutti.
      tokens.value = await fetchRegistrationTokens();
    } catch (err: any) {
      console.error("Errore nel recupero dei token:", err);
      tokensError.value = err.message || 'Si è verificato un errore sconosciuto.';
    } finally {
      isLoadingTokens.value = false;
    }
 };

 // --- Gestione Token ---

 const openTokenForm = () => {
    newTokenGroupId.value = null;
    createTokenError.value = null;
    showTokenForm.value = true;
 };

 const closeTokenForm = () => {
    showTokenForm.value = false;
 };

 const handleCreateToken = async () => {
    isCreatingToken.value = true;
    createTokenError.value = null;
    try {
        const payload = { group_id: newTokenGroupId.value };
        await createRegistrationToken(payload);
        // Ricarica la lista dei token dal server invece di aggiungere manualmente
        await loadRegistrationTokens();
        closeTokenForm();
    } catch (err: any) {
        console.error("Errore creazione token:", err);
        createTokenError.value = err.response?.data?.detail || err.message || "Errore sconosciuto.";
    } finally {
        isCreatingToken.value = false;
    }
 };

 const handleDeactivateToken = async (token: RegistrationToken) => {
    if (!confirm(`Sei sicuro di voler disattivare questo token? Non potrà più essere usato per le registrazioni.`)) {
        return;
    }
    try {
        await deactivateRegistrationToken(token.token);
        // Aggiorna lo stato locale
        const index = tokens.value.findIndex(t => t.token === token.token);
        if (index !== -1) {
            tokens.value[index].is_active = false;
            tokens.value[index].is_valid = false; // Aggiorna anche is_valid
        }
        alert("Token disattivato.");
    } catch (err: any) {
        console.error(`Errore disattivazione token ${token.token}:`, err);
        alert(`Errore durante la disattivazione: ${err.response?.data?.detail || err.message}`);
    }
 };

 const handleDeleteToken = async (token: RegistrationToken) => {
     if (!confirm(`Sei sicuro di voler eliminare definitivamente questo token?`)) {
         return;
     }
     try {
         await deleteRegistrationToken(token.token);
         // Rimuovi dalla lista locale
         tokens.value = tokens.value.filter(t => t.token !== token.token);
         alert("Token eliminato.");
     } catch (err: any) {
         console.error(`Errore eliminazione token ${token.token}:`, err);
         alert(`Errore durante l'eliminazione: ${err.response?.data?.detail || err.message}`);
     }
 };

 // URL base del frontend studenti per il QR code - Ora costruito dinamicamente

 const getRegistrationUrl = (token: string) => {
   // Usa l'origine corrente (es. http://217.154.2.9)
   const origin = window.location.origin;
   // Aggiungi il percorso base del frontend studenti e la rotta di registrazione
   // Assicurati che '/studenti' sia il percorso corretto definito in Nginx
   const registrationPath = `/studenti/register/${token}`;
   return `${origin}${registrationPath}`;
 };

 const selectInputText = (event: FocusEvent) => {
   const target = event.target as HTMLInputElement | null;
   if (target) {
     target.select();
   }
 };

 // Filtra solo i token attivi e validi per la visualizzazione principale
 const activeTokens = computed(() => {
     return tokens.value.filter(t => t.is_valid);
 });

 </script>

 <template>
   <div class="dashboard-view p-6">
     <h2 class="text-2xl font-semibold mb-4">Dashboard Docente</h2>
     <p class="mb-6">Benvenuto/a, {{ authStore.user?.username || 'Docente' }}!</p>

     <!-- Sezione Statistiche Rapide -->
     <div v-if="isLoading" class="loading">Caricamento statistiche...</div>
     <div v-else-if="error" class="error-message">Errore caricamento dati: {{ error }}</div>
     <div v-else-if="dashboardData" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
       <!-- Card Studenti -->
       <div class="bg-blue-100 border border-blue-300 rounded-lg p-4 shadow">
         <h3 class="text-lg font-semibold text-blue-800">Studenti</h3>
         <p class="text-3xl font-bold">{{ dashboardData.student_count }}</p>
         <router-link to="/students" class="text-blue-600 hover:underline text-sm mt-2 inline-block">Gestisci Studenti</router-link>
       </div>
       <!-- Card Template Quiz -->
       <div class="bg-green-100 border border-green-300 rounded-lg p-4 shadow">
         <h3 class="text-lg font-semibold text-green-800">Template Quiz</h3>
         <p class="text-3xl font-bold">{{ dashboardData.quiz_template_count }}</p>
         <router-link to="/quiz-templates" class="text-green-600 hover:underline text-sm mt-2 inline-block">Gestisci Template Quiz</router-link>
       </div>
       <!-- Card Template Percorsi -->
       <div class="bg-purple-100 border border-purple-300 rounded-lg p-4 shadow">
         <h3 class="text-lg font-semibold text-purple-800">Template Percorsi</h3>
         <p class="text-3xl font-bold">{{ dashboardData.pathway_template_count }}</p>
         <router-link to="/pathway-templates" class="text-purple-600 hover:underline text-sm mt-2 inline-block">Gestisci Template Percorsi</router-link>
       </div>
       <!-- Card Valutazioni Pendenti -->
       <div class="bg-yellow-100 border border-yellow-300 rounded-lg p-4 shadow">
         <h3 class="text-lg font-semibold text-yellow-800">Da Valutare</h3>
         <p class="text-3xl font-bold">{{ dashboardData.pending_manual_answers_count }}</p>
         <router-link v-if="dashboardData.pending_manual_answers_count > 0" to="/grading" class="text-yellow-600 hover:underline text-sm mt-2 inline-block">Vai a Valutazioni</router-link>
          <p v-else class="text-sm text-gray-500 mt-2">Nessuna risposta da valutare.</p>
       </div>
     </div>

     <!-- Sezione Link Rapidi -->
     <div class="quick-links mb-8">
       <h3 class="text-xl font-semibold mb-3">Azioni Rapide</h3>
       <div class="flex flex-wrap gap-4">
         <router-link to="/assign" class="btn btn-primary">Assegna Contenuti</router-link>
         <router-link to="/students" class="btn btn-secondary">Gestisci Studenti</router-link>
         <router-link to="/quiz-templates" class="btn btn-secondary">Gestisci Template Quiz</router-link>
         <router-link to="/pathway-templates" class="btn btn-secondary">Gestisci Template Percorsi</router-link>
         <router-link to="/grading" class="btn btn-secondary">Valutazioni Manuali</router-link>
         <router-link to="/rewards" class="btn btn-secondary">Gestisci Ricompense</router-link>
       </div>
     </div>

     <!-- Sezione Inviti Registrazione Studenti -->
     <section class="mb-8 p-4 border rounded shadow-sm bg-white">
         <h2 class="text-xl font-semibold mb-3">Inviti Registrazione Studenti (QR Code)</h2>
         <p class="text-sm text-gray-600 mb-3">
             Genera link unici (validi per un periodo limitato) per permettere agli studenti di registrarsi autonomamente.
             Puoi associare un invito a un gruppo specifico.
         </p>
         <button @click="openTokenForm" class="btn btn-success btn-sm mb-4">Genera Nuovo Invito</button>

         <!-- Form Creazione Token -->
         <div v-if="showTokenForm" class="mt-4 p-3 border rounded bg-gray-100 mb-4">
             <h3 class="text-lg font-medium mb-2">Nuovo Invito Registrazione</h3>
             <div class="form-group mb-3">
                 <label for="token-group">Associa a Gruppo (opzionale):</label>
                 <select id="token-group" v-model="newTokenGroupId" class="w-full p-2 border rounded">
                     <option :value="null">Nessun Gruppo (solo al docente)</option>
                     <option v-for="group in groups" :key="group.id" :value="group.id">
                         {{ group.name }}
                     </option>
                 </select>
                 <div v-if="isLoadingGroups" class="text-sm text-gray-500 italic">Caricamento gruppi...</div>
                 <div v-if="groupsError" class="error-message text-sm">{{ groupsError }}</div>
             </div>
             <div v-if="createTokenError" class="error-message my-2">{{ createTokenError }}</div>
             <div class="form-actions mt-3">
                 <button @click="handleCreateToken" :disabled="isCreatingToken" class="btn btn-primary mr-2">
                     {{ isCreatingToken ? 'Generazione...' : 'Genera Invito' }}
                 </button>
                 <button @click="closeTokenForm" class="btn btn-secondary">Annulla</button>
             </div>
         </div>

         <!-- Elenco Token Attivi -->
         <h3 class="text-lg font-semibold mb-2">Inviti Attivi</h3>
         <div v-if="isLoadingTokens" class="loading">Caricamento inviti...</div>
         <div v-else-if="tokensError" class="error-message">Errore caricamento inviti: {{ tokensError }}</div>
         <div v-else-if="activeTokens.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
             <div v-for="token in activeTokens" :key="token.token" class="border rounded p-3 flex flex-col items-center shadow-sm">
                 <p class="text-sm font-medium mb-1">Invito per: {{ token.group_name || 'Docente' }}</p>
                 <p class="text-xs text-gray-500 mb-2">Scade: {{ new Date(token.expires_at).toLocaleString() }}</p>
                 <qrcode-vue :value="getRegistrationUrl(token.token)" :size="150" level="H" class="mb-2" />
                 <!-- Mostra URL testuale -->
                 <p class="text-xs text-center mb-1">Link Registrazione:</p>
                 <input
                    type="text"
                    :value="getRegistrationUrl(token.token)"
                    readonly
                    class="w-full text-xs p-1 border rounded bg-gray-100 text-center mb-3"
                    @focus="selectInputText"
                 />
                 <p class="text-xs text-center mb-3">Mostra il QR o copia il link per lo studente.</p>
                 <div class="flex gap-2 mt-auto">
                     <button @click="handleDeactivateToken(token)" class="btn btn-warning btn-xs">Disattiva</button>
                     <button @click="handleDeleteToken(token)" class="btn btn-danger btn-xs">Elimina</button>
                 </div>
             </div>
         </div>
         <p v-else class="text-gray-500 italic">Nessun invito attivo trovato.</p>
     </section>

   </div>
 </template>

 <style scoped>
 .dashboard-view {
   /* padding: 1rem; */ /* Rimosso padding base, Tailwind gestisce spazi */
   max-width: 1200px; /* Limita larghezza massima per leggibilità */
   margin: 0 auto; /* Centra */
 }
 .loading, .error-message {
   margin-top: 1rem;
   font-style: italic;
   color: #666;
 }
 .error-message {
   color: red;
   font-weight: bold;
 }
 /* Stili aggiuntivi per le card e i link se necessario,
    ma Tailwind dovrebbe coprire la maggior parte */
 .btn-xs { /* Aggiunto stile per bottoni piccoli */
     padding: 0.25rem 0.5rem;
     font-size: 0.75rem;
     line-height: 1;
     border-radius: 0.2rem;
 }
 </style>