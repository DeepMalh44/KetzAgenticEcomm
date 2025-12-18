# Frontend Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Build arguments for Vite environment variables
ARG VITE_BACKEND_URL=http://localhost:8000
ARG VITE_WS_URL=ws://localhost:8000
ARG CACHEBUST=1

# Set as environment variables for build
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL
ENV VITE_WS_URL=$VITE_WS_URL

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Cache bust - this forces rebuild of everything below when CACHEBUST changes
RUN echo "Cache bust: $CACHEBUST"

# Copy source code
COPY . .

# Debug: Show content of key file to verify source is correct
RUN head -60 src/store/appStore.ts | grep -A 2 "SearchMode" || echo "SearchMode NOT FOUND"
RUN grep -n "searchMode" src/hooks/useRealtimeSession.ts || echo "searchMode NOT FOUND in useRealtimeSession"
RUN grep -n "setSearchMode" src/pages/HomePage.tsx || echo "setSearchMode NOT FOUND in HomePage"

# Build the application
RUN npm run build

# Production image
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
