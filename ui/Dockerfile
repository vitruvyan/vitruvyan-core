# Fase 1: Build con Node
FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Fase 2: Serve con Nginx
FROM nginx:alpine

# Copia la build nella root di Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Rimuove il file di configurazione default
RUN rm /etc/nginx/conf.d/default.conf

# Aggiunge un nuovo file di configurazione
COPY nginx.conf /etc/nginx/conf.d

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
