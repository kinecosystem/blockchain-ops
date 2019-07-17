FROM telegraf:1.9.5-alpine

EXPOSE 8086

# envsubst requirement
RUN apk add -qU --no-cache gettext jq curl coreutils bc

COPY ./entrypoint.sh /
COPY ./telegraf.conf.tmpl /etc/telegraf
COPY ./input-exec/*.sh /usr/bin/

ENTRYPOINT []
CMD /entrypoint.sh
