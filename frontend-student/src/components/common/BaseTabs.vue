<template>
  <div>
    <!-- Tab Headers -->
    <div class="border-b border-brand-gray-light">
      <nav class="-mb-px flex space-x-6" aria-label="Tabs">
        <button
          v-for="(tab, index) in tabs"
          :key="tab.name"
          @click="selectTab(index)"
          :class="[
            selectedIndex === index
              ? 'border-kahoot-purple text-kahoot-purple'
              : 'border-transparent text-brand-gray hover:text-brand-gray-dark hover:border-brand-gray',
            'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 focus:outline-none'
          ]"
          :aria-current="selectedIndex === index ? 'page' : undefined"
        >
          {{ tab.name }}
        </button>
      </nav>
    </div>

    <!-- Tab Panels -->
    <div class="mt-6">
      <div v-for="(tab, index) in tabs" :key="tab.name" v-show="selectedIndex === index">
        <slot :name="tab.slotName || `tab-${index}`"></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, defineProps, defineEmits, withDefaults } from 'vue';

interface Tab {
  name: string;
  slotName?: string; // Opzionale, per nomi slot personalizzati
}

interface Props {
  tabs: Tab[];
  initialIndex?: number;
}

const props = withDefaults(defineProps<Props>(), {
  initialIndex: 0,
});

const emit = defineEmits(['tab-selected']);

const selectedIndex = ref(props.initialIndex);

const selectTab = (index: number) => {
  selectedIndex.value = index;
  emit('tab-selected', index);
};
</script>

<style scoped>
/* Eventuali stili aggiuntivi per i tab */
</style>