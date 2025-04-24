# Stage 1: Build the Vue.js application
FROM node:18-alpine AS build-stage

WORKDIR /app

# Copia package.json e package-lock.json
COPY package*.json ./

# Installa le dipendenze
RUN npm install

# Copia il resto del codice sorgente
COPY . .

# Costruisci l'applicazione per la produzione
# Rimosso ARG/ENV VITE_API_BASE_URL. L'URL base verrà gestito da api.ts
# usando import.meta.env.VITE_API_BASE_URL (da .env.local) o il fallback '/api'.
RUN npm run build

# Stage 2: Serve l'applicazione con Nginx
FROM nginx:stable-alpine

# Copia i file statici costruiti dallo stage precedente
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copia la configurazione personalizzata di Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Esponi la porta 80 (porta standard di Nginx)
EXPOSE 80

# Comando per avviare Nginx
CMD ["nginx", "-g", "daemon off;"]