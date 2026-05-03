# Dev-grade frontend image: Node 20 + Vite dev server with HMR.
# Production deployment (static hosting, CDN, edge cache) is intentionally
# out of scope — left to CI/CD or cloud provider (Vercel, Cloudflare Pages,
# S3+CloudFront, etc.).

# ---- Stage 1: install npm deps ----
# Separated so that source changes don't bust the install layer.
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

# ---- Stage 2: dev runtime ----
FROM node:20-alpine
WORKDIR /app

# Make /app writable by the built-in non-root `node` user (uid 1000).
RUN chown node:node /app
USER node

# Bring in deps from stage 1 (owned by node).
COPY --from=deps --chown=node:node /app/node_modules ./node_modules

# Source. In compose this is overlaid by a bind mount for HMR; for a
# standalone `docker run` the baked source is what runs.
COPY --chown=node:node . .

# Vite dev server default port.
EXPOSE 5173

# `--host 0.0.0.0` so the port is reachable from outside the container.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
