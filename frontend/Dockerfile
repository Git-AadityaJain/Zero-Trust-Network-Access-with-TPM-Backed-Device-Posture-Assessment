#frontend/Dockerfile

FROM node:20

WORKDIR /app

COPY package.json ./
# Copy package-lock.json if it exists, otherwise npm install will create it
COPY package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 3000
CMD ["npm", "start"]
