# Nginx that runs without root. It fills in the *.template files at startup.
FROM nginxinc/nginx-unprivileged:1.28-alpine

# Address the *browser* uses to reach the API.
ENV API_URL=http://localhost:8000

COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY public/ /usr/share/nginx/html/

EXPOSE 8080
