# === Build (Node) ===
FROM node:20-alpine AS build
WORKDIR /app

# 1) Copia SOLO los manifiestos que están dentro de app/
COPY app/package.json app/package-lock.json ./

# 2) Instala deps con lockfile (rápido y reproducible)
RUN npm ci --no-audit --no-fund

# 3) Copia el código FUENTE (src, public, etc.) desde app/
COPY app/. .

# 4) Compila el frontend (Vite/React) -> /app/dist
RUN npm run build

# === Runtime (Nginx) ===
FROM nginx:1.27-alpine
# Sirve el build estático
COPY --from=build /app/dist /usr/share/nginx/html

# (opcional) SPA routing + config.json personalizado:
# RUN rm /etc/nginx/conf.d/default.conf
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]


