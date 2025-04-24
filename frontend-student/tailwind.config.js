/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    fontFamily: {
      sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', '"Noto Sans"', 'sans-serif', '"Apple Color Emoji"', '"Segoe UI Emoji"', '"Segoe UI Symbol"', '"Noto Color Emoji"'],
    },
    extend: {
      colors: {
        primary: { // Viola principale
          light: '#A78BFA', // violet-400
          DEFAULT: '#8B5CF6', // violet-500
          dark: '#7C3AED',  // violet-600
        },
        secondary: { // Viola scuro per sidebar/elementi scuri
          light: '#3730A3', // indigo-800 (leggermente più chiaro per hover?)
          DEFAULT: '#312E81', // indigo-900
          dark: '#262366', // Tonalità ancora più scura
        },
        accent: { // Viola per header progetto
          light: '#8B5CF6', // violet-500
          DEFAULT: '#6D28D9', // violet-700
          dark: '#5B21B6', // violet-800
        },
        neutral: { // Scala di grigi
          lightest: '#F9FAFB', // gray-50 (sfondo card)
          light: '#F3F4F6',    // gray-100
          DEFAULT: '#E5E7EB', // gray-200 (bordi)
          medium: '#D1D5DB',   // gray-300
          dark: '#6B7280',     // gray-500 (testo secondario)
          darker: '#374151',   // gray-700
          darkest: '#111827',  // gray-900 (testo principale)
        },
        // Potremmo aggiungere colori per stati (success, error, warning) se necessario
        success: {
          DEFAULT: '#10B981', // green-500
          dark: '#047857',    // green-700 (aggiunto per text-success-dark)
        },
        error: '#EF4444',   // red-500
        warning: {
          DEFAULT: '#F59E0B', // amber-500
          dark: '#B45309',    // amber-700 (aggiunto per text-warning-dark)
        },
      },
      // Qui eventuali altre estensioni (es. spacing, borderRadius)
    },
  },
  plugins: [],
}