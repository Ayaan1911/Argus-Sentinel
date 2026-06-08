FROM node:18-alpine
WORKDIR /app
COPY package.json vite.config.js ./
RUN npm install
COPY . .
CMD ["npm", "run", "dev", "--", "--host"]
