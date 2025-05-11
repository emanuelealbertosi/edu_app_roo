<template>
  <div class="file-upload">
    <label :for"inputId" class="form-label">{{ label }}</label>
    <input
      :id"inputId"
      type="file"
      class="form-control"
      :accept"accept"
      @change="handleFileChange"
      :disabled"disabled"
    />
    <div v-if="selectedFile" class="mt-2">
      <small>File selezionato: {{ selectedFile.name }} ({{ formatFileSize(selectedFile.size) }})</small>
    </div>
    <div v-if"previewUrl" class="mt-2">
      <small>Anteprima allegato esistente:</small>
      <div v-if="isImage(previewUrl)">
        <img :src="previewUrl" alt="Anteprima allegato" style="max-width: 200px; max-height: 150px; margin-top: 5px;" />
      </div>
      <div v-else>
        <a :href="previewUrl" target="_blank" rel="noopener noreferrer">{{ previewUrl.split('/').pop() }}</a>
      </div>
    </div>
    <div v-if="error" class="text-danger mt-1">
      <small>{{ error }}</small>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';

const props = defineProps({
  label: {
    type: String,
    default: 'Carica file'
  },
  accept: {
    type: String,
    default: '*' // Accetta tutti i tipi di file di default
  },
  maxSizeMb: {
    type: Number,
    default: 5 // Dimensione massima predefinita in MB
  },
  disabled: {
    type: Boolean,
    default: false
  },
  existingFileUrl: { // URL di un file già esistente, per visualizzazione
    type: String,
    default: ''
  }
});

const emit = defineEmits(['file-selected', 'file-cleared', 'error']);

const inputId = computed(() => `file-upload-${Math.random().toString(36).substring(7)}`);
const selectedFile = ref<File | null>(null);
const error = ref<string | null>(null);
const previewUrl = ref<string>(props.existingFileUrl);

watch(() => props.existingFileUrl, (newUrl) => {
  previewUrl.value = newUrl;
  if (newUrl) { // Se viene fornito un URL esistente, resetta il file selezionato localmente
    selectedFile.value = null; 
    emit('file-cleared'); // Notifica che il file locale è stato "cancellato" in favore di quello esistente
  }
});

const handleFileChange = (event: Event) => {
  error.value = null;
  previewUrl.value = ''; // Rimuove l'anteprima del file esistente se si seleziona un nuovo file
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    const file = target.files[0];
    if (file.size > props.maxSizeMb * 1024 * 1024) {
      error.value = `Il file supera la dimensione massima di ${props.maxSizeMb}MB.`;
      selectedFile.value = null;
      target.value = ''; // Resetta l'input file
      emit('error', error.value);
      emit('file-cleared');
      return;
    }
    selectedFile.value = file;
    emit('file-selected', file);
  } else {
    selectedFile.value = null;
    emit('file-cleared');
  }
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const isImage = (url: string): boolean => {
  if (!url) return false;
  return /\.(jpeg|jpg|gif|png|svg)$/i.test(url);
};

// Funzione per resettare lo stato del componente (utile se gestito da un genitore)
const reset = () => {
  selectedFile.value = null;
  error.value = null;
  previewUrl.value = props.existingFileUrl; // Ripristina l'URL esistente se presente
  // Resetta l'input file DOM se necessario (più complesso, potrebbe richiedere un ref all'input)
  const inputElement = document.getElementById(inputId.value) as HTMLInputElement;
  if (inputElement) {
    inputElement.value = '';
  }
  emit('file-cleared');
};

defineExpose({ reset });

</script>

<style scoped>
.file-upload .form-label {
  font-weight: 500;
}
/* Aggiungi stili personalizzati se necessario */
</style>