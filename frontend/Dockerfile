FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies with legacy peer deps and correct esbuild version
RUN rm -rf node_modules package-lock.json && \
    npm install --legacy-peer-deps

# Copy application code
COPY . .

# Expose port
EXPOSE 5173

# Development command (will be overridden by docker-compose for hot reload)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
