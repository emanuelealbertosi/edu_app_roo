/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'kahoot-purple': {
          DEFAULT: '#46178F', // Viola scuro principale
          dark: '#301063',
        },
        'kahoot-blue': {
          DEFAULT: '#2689F2', // Blu acceso
          light: '#5CADF9',
        },
        'kahoot-red': {
          DEFAULT: '#E21B3C', // Rosso
          light: '#F05A72',
        },
        'kahoot-green': {
          DEFAULT: '#00A95C', // Verde
          light: '#33BC81',
        },
        'kahoot-yellow': {
          DEFAULT: '#FFA500', // Giallo/Arancio
          light: '#FFC14D',
          dark: '#E69500', // Aggiunto giallo scuro per testo su sfondo chiaro
        },
        'kahoot-pink': '#FF69B4', // Rosa accento
        'kahoot-cyan': '#00BCD4', // Ciano/Azzurro accento
        'brand-gray': { // Rinominiamo i grigi per coerenza
          light: '#F3F4F6', // Grigio chiaro sfondo
          DEFAULT: '#D1D5DB', // Grigio medio bordi/divisori
          dark: '#4B5563',  // Grigio scuro testo
        }
      },
      fontFamily: {
        sans: ['Nunito', 'sans-serif'], // Imposta Nunito come font sans-serif di default
      },
      // Aggiungeremo qui eventuali altre personalizzazioni (animazioni, etc.)
    },
  },
  plugins: [],
}