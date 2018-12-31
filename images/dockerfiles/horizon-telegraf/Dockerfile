FROM telegraf:1.8.3-alpine
RUN apk add --no-cache curl gettext
COPY ./telegraf.conf.tmpl /etc/telegraf/telegraf.conf.tmpl
COPY ./check-latency.sh.tmpl /tmp/check_latency.sh.tmpl
COPY ./get_load5.sh /tmp/get_load5.sh
EXPOSE 8086
CMD envsubst '$NODE_NAME $NETWORK_NAME' < /etc/telegraf/telegraf.conf.tmpl > /etc/telegraf/telegraf.conf && envsubst '$TARGET_URL' < /tmp/check_latency.sh.tmpl > /tmp/check_latency.sh && chmod +x /tmp/check_latency.sh && exec telegraf
