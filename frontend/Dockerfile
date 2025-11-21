# Build stage
FROM node:18-slim AS build

WORKDIR /app

# Copy only package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy full frontend source
COPY . .

# Build the frontend app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files to NGINX html folder
COPY --from=build /app/dist /usr/share/nginx/html

# Copy NGINX config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
