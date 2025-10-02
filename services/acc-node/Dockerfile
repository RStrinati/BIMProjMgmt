# ACC Node.js Service Dockerfile
FROM node:18
WORKDIR /app
COPY . .
RUN npm install
EXPOSE 4000
CMD ["node", "index.js"]