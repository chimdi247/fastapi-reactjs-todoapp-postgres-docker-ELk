# syntax=docker/dockerfile:1.7

# ---------- build ----------
FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json* ./
# package.json gained OpenTelemetry deps; run `npm install` once locally to
# refresh package-lock.json, then switch this line to `npm ci` for reproducible
# builds.
RUN npm install --no-audit --no-fund

COPY . .

# Build-time (public) configuration - baked into the static bundle.
ARG VITE_API_BASE_URL=/api
ARG VITE_OTEL_ENABLED=true
ARG VITE_OTEL_TRACES_URL=/otlp/v1/traces
ARG VITE_ENVIRONMENT=local
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_OTEL_ENABLED=$VITE_OTEL_ENABLED \
    VITE_OTEL_TRACES_URL=$VITE_OTEL_TRACES_URL \
    VITE_ENVIRONMENT=$VITE_ENVIRONMENT

RUN npm run build


# ---------- serve ----------
FROM nginx:1.27-alpine AS runtime

# Static assets. The server config (SPA fallback, /api and /otlp reverse
# proxies, security headers) is mounted by docker-compose from
# docker/nginx/default.conf.
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD wget -q -O /dev/null http://127.0.0.1/nginx-health || exit 1
