FROM telegraf:1.8.3-alpine
RUN apk add --no-cache curl gettext
COPY ./telegraf.conf.tmpl /etc/telegraf/telegraf.conf.tmpl
COPY ./check-latency.sh.tmpl /tmp/check-latency.sh.tmpl
EXPOSE 8086
CMD envsubst '$NODE_NAME' < /etc/telegraf/telegraf.conf.tmpl > /etc/telegraf/telegraf.conf && envsubst  '$NODE_NAME $TARGET_URL' < /tmp/check_latency.sh.tmpl > /tmp/check_latency.sh && chmod +x /tmp/check_latency.sh && exec telegraf
