# Frontend Dockerfile (Next.js standalone)
FROM node:20-slim AS builder

WORKDIR /app

# 依存関係インストール
COPY package*.json ./
RUN npm ci

# ビルド
COPY . .
RUN npm run build

# 本番イメージ
FROM node:20-slim AS runner

WORKDIR /app

ENV NODE_ENV=production

# standalone出力をコピー
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
