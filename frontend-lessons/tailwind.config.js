// frontend-lessons/tailwind.config.js
const defaultTheme = require('tailwindcss/defaultTheme')

module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}", // Assicura che Tailwind analizzi i tuoi file sorgente
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Titillium Web"', ...defaultTheme.fontFamily.sans],
      },
    },
  },
  plugins: [],
}