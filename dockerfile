# Using a light (Alpine) image for efficiency
FROM nginx:alpine

# Copy the HTML file to the default Nginx directory
COPY index.html /usr/share/nginx/html/index.html

# Expose 80 port
EXPOSE 80
