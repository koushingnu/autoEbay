FROM node:22-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

# npm 経由だと停止時(SIGTERM)に npm が exit 1 を返すため、next を直接起動して
# シグナルを正しく伝播させる（停止が exit 0 になる）
CMD ["./node_modules/.bin/next", "dev"]
