<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60 backdrop-blur-sm"
        @click.self="closeModal"
      >
        <!-- Contenitore Modale -->
        <div class="bg-white rounded-lg shadow-xl max-w-lg w-full m-4 overflow-hidden transform transition-all sm:max-w-xl md:max-w-2xl">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-brand-gray">
            <h3 v-if="title" class="text-xl font-bold text-kahoot-purple">{{ title }}</h3>
            <div v-else></div> <!-- Placeholder per allineamento -->
            <button
              @click="closeModal"
              class="text-brand-gray hover:text-brand-gray-dark transition-colors p-1 rounded-full hover:bg-brand-gray-light"
              aria-label="Chiudi modale"
            >
              <!-- Icona X -->
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="p-6 max-h-[70vh] overflow-y-auto custom-scrollbar">
            <slot></slot> <!-- Contenuto iniettato qui -->
          </div>

          <!-- Footer (Opzionale) -->
          <div v-if="$slots.footer" class="px-6 py-4 bg-brand-gray-light border-t border-brand-gray flex justify-end space-x-3">
            <slot name="footer"></slot> <!-- Bottoni/Azioni qui -->
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { watch, onUnmounted } from 'vue';

interface Props {
  show: boolean; // Prop per controllare la visibilità
  title?: string; // Titolo opzionale
}

const props = defineProps<Props>();
const emit = defineEmits(['close']); // Evento emesso per chiudere

const closeModal = () => {
  emit('close');
};

// Gestione overflow body per evitare scroll pagina sottostante
watch(() => props.show, (newValue) => {
  if (typeof document !== 'undefined') { // Verifica per SSR/Build
    if (newValue) {
      document.body.style.overflow = 'hidden';
    } else {
      // Ritarda il ripristino per permettere all'animazione di finire
      setTimeout(() => {
        // Controlla se un'altra modale è ancora aperta prima di ripristinare
        const openModals = document.querySelectorAll('.fixed.inset-0.z-50').length;
        if (openModals === 0) {
           document.body.style.overflow = '';
        }
      }, 300); // Deve corrispondere alla durata della transizione CSS
    }
  }
}, { immediate: false });

// Cleanup: Assicurati di rimuovere lo stile se il componente viene smontato mentre è aperto
onUnmounted(() => {
  if (typeof document !== 'undefined') {
     // Controlla se un'altra modale è ancora aperta prima di ripristinare
     const openModals = document.querySelectorAll('.fixed.inset-0.z-50').length;
     // Se questa è l'ultima modale che si sta smontando
     if (props.show && openModals <= 1) {
        document.body.style.overflow = '';
     }
  }
});

</script>

<style scoped>
/* Animazione Fade */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

/* Stile Scrollbar Custom (Opzionale ma carino) */
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1; /* Grigio molto chiaro */
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #d1d5db; /* brand-gray */
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #9ca3af; /* gray-400 */
}
/* Per Firefox (meno opzioni di styling) */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #d1d5db #f1f1f1;
}
</style>