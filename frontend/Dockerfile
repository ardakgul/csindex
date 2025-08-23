# Frontend Dockerfile for Cloudy&Shiny
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
COPY .env.example ./.env
RUN npm install --no-audit --no-fund
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/dist ./dist
# Serve with a tiny static server
RUN npm install -g serve
EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]
