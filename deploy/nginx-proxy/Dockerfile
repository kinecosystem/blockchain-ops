FROM nginx:1.15.1-alpine

COPY ./nginx.conf.tmpl /etc/nginx/

EXPOSE 80

CMD envsubst '$PROXY_READ_TIMEOUT $PROXY_PASS_URL' < /etc/nginx/nginx.conf.tmpl > /etc/nginx/nginx.conf && exec nginx
