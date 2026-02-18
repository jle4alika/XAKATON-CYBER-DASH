# ----------------------------------------------------
# Frontend (Vite React) Docker image - Multi-stage build
# ----------------------------------------------------

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Копируем package файлы
COPY frontend/package*.json ./

# Устанавливаем зависимости
RUN npm ci

# Копируем исходники
COPY frontend/ ./

# Собираем production build
RUN npm run build

# Stage 2: Production server
FROM nginx:alpine

# Копируем собранные файлы из builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Копируем кастомную конфигурацию nginx (опционально)
# COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Открываем порт
EXPOSE 80

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"]
