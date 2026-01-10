# =============================================================================
# Frontend Dockerfile - Optimized for AWS ECS Deployment
# =============================================================================
# Multi-stage build with standalone output for minimal image size

# -----------------------------------------------------------------------------
# Stage 1: Dependencies
# -----------------------------------------------------------------------------
FROM node:20-alpine AS deps
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY apps/frontend/package*.json ./
RUN npm ci --only=production=false

# -----------------------------------------------------------------------------
# Stage 2: Builder
# -----------------------------------------------------------------------------
FROM node:20-alpine AS builder
WORKDIR /app

# Install sharp for image optimization
RUN npm install -g sharp

COPY --from=deps /app/node_modules ./node_modules
COPY apps/frontend .

# Disable telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

# Build arguments for PUBLIC environment variables only (safe to bake into build)
ARG NEXT_PUBLIC_API_URL=https://goziphouse.com
ARG NEXT_PUBLIC_RAG_URL=https://goziphouse.com/rag
ARG NEXT_PUBLIC_KAKAO_MAP_KEY=29d460d952fdd2737e2be0432924660c

# Set PUBLIC environment variables for build
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_RAG_URL=$NEXT_PUBLIC_RAG_URL \
    NEXT_PUBLIC_KAKAO_MAP_KEY=$NEXT_PUBLIC_KAKAO_MAP_KEY

RUN npm run build

# -----------------------------------------------------------------------------
# Stage 3: Runner - Production image
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Stage 3: Runner - Production image
# -----------------------------------------------------------------------------
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# Security: Create non-root user
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

# Copy essential files
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

# Copy built artifacts (Standard Build)
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules

# Install curl for health checks
RUN apk add --no-cache curl

USER nextjs

EXPOSE 3000

ENV PORT=3000 \
    HOSTNAME="0.0.0.0"

# Health check for ALB/ECS
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Use standard Next.js start command
CMD ["npm", "run", "start"]
