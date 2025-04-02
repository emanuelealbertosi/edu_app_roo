/// <reference types="vite/client" />

// Aggiunta dichiarazione per i moduli .vue
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}