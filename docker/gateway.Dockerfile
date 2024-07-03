FROM nginx:alpine

COPY entrypoint-nginx.sh /

RUN set -ex && apk add --no-cache bash && chmod +x /entrypoint-nginx.sh

WORKDIR /etc/nginx/conf.d
COPY config/* ./


ENTRYPOINT ["/entrypoint-nginx.sh"]
