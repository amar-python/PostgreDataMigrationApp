# ---- Build stage ----
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies first for better layer caching.
COPY package*.json ./
RUN npm ci

# Build the production bundle.
COPY . .
RUN npm run build

# ---- Serve stage ----
FROM nginx:alpine AS serve

# SPA + API-proxy nginx config.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Static assets from the build stage.
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
