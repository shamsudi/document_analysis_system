FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
COPY static/ /usr/share/nginx/html/static/
COPY nginx.conf /etc/nginx/nginx.conf
COPY empty_default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]