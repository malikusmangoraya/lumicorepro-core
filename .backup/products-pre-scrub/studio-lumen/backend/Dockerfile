# Multi-stage build for production
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first for better caching
COPY package*.json ./
RUN npm ci --only=production && \
    npm cache clean --force

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads logs

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install dependencies (production only)
COPY package*.json ./
RUN npm ci --only=production && \
    npm cache clean --force

# Copy built app from builder
COPY --from=builder /app .

# Create necessary directories and set permissions
RUN mkdir -p uploads logs && \
    chmod -R 755 uploads logs

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:5000/api/health', (r) => { process.exit(r.statusCode === 200 ? 0 : 1) })"

# Start server
CMD ["node", "server.js"]