# Stage 1: Build the Vue.js application
FROM node:18-alpine AS build-stage

WORKDIR /app

# Copia package.json e package-lock.json (o yarn.lock se usi yarn)
COPY package*.json ./

# Installa le dipendenze
RUN npm install

# Copia il resto del codice sorgente
COPY . .

# Costruisci l'applicazione per la produzione
# Passa l'URL dell'API come argomento di build
# Il valore predefinito /api/ può essere usato se si configura un proxy Nginx
ARG VITE_API_BASE_URL=/api/
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN echo "Building frontend-student-v2 with API URL: ${VITE_API_BASE_URL}" && npm run build

# Stage 2: Serve l'applicazione con Nginx
FROM nginx:stable-alpine

# Copia i file statici costruiti dallo stage precedente
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copia la configurazione personalizzata di Nginx
# Assicurati di creare/copiare questo file 'nginx.conf' in frontend-student-v2
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Esponi la porta 80 (porta standard di Nginx)
EXPOSE 80

# Comando per avviare Nginx
CMD ["nginx", "-g", "daemon off;"]