FROM telegraf:1.8.3-alpine
RUN apk add --no-cache curl gettext jq
COPY ./telegraf.conf.tmpl /etc/telegraf/telegraf.conf.tmpl
COPY ./get-load5.sh.tmpl /tmp/get_load5.sh.tmpl
COPY ./get-core-state.sh.tmpl /tmp/get_core_state.sh.tmpl
EXPOSE 8086
CMD envsubst '$NODE_NAME' < /etc/telegraf/telegraf.conf.tmpl > /etc/telegraf/telegraf.conf && envsubst  '$NODE_NAME' < /tmp/get_core_state.sh.tmpl > /tmp/get_core_state.sh && chmod +x /tmp/get_core_state.sh && envsubst  '$NODE_NAME' < /tmp/get_load5.sh.tmpl > /tmp/get_load5.sh && chmod +x /tmp/get_load5.sh && exec telegraf
