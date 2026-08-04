# syntax=docker/dockerfile:1

FROM node:22-bullseye-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM python:3.10-slim-bullseye
WORKDIR /app

# Install Node.js
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs nginx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || true

# Copy all files
COPY --from=builder /app /app

EXPOSE 3000
EXPOSE 80

ENV NODE_ENV=production
ENV PORT=3000
ENV HOST=0.0.0.0

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
