# Use lightweight Nginx web server image
FROM nginx:alpine

# Copy custom Nginx configuration if needed, or copy frontend static files directly
COPY . /usr/share/nginx/html

# Expose Nginx default HTTP port
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]