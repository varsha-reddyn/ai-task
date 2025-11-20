## Build stage
## Use a Debian-based Node image to ensure `npm` and build tooling are available
FROM node:18-bullseye-slim AS builder
WORKDIR /app

COPY frontend/package*.json ./
# Use npm install with legacy-peer-deps to avoid ERESOLVE failures inside the builder
RUN npm install --legacy-peer-deps --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

## Production stage - serve built files with nginx
FROM nginx:stable-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
