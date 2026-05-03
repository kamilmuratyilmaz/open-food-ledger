# Dev-grade frontend image: Node 20 + Vite dev server with HMR.
# This is intentionally NOT a production setup — production deployment
# (static hosting, CDN, edge cache) is left to whichever provider your
# CI/CD pipeline targets (Vercel, Cloudflare Pages, S3+CloudFront, ...).

FROM node:20-alpine

WORKDIR /app

# Make /app writable by the built-in non-root `node` user (uid 1000).
RUN chown node:node /app

USER node

# Install deps first so source changes don't bust the npm install layer.
COPY --chown=node:node package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

# Source. In compose this is overlaid by a bind mount for HMR; for a
# standalone `docker run` the baked source is what runs.
COPY --chown=node:node . .

# Vite dev server default port.
EXPOSE 5173

# `--host 0.0.0.0` so the port is reachable from outside the container
# (Vite binds 127.0.0.1 by default).
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
