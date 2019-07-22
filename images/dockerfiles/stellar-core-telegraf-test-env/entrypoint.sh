#!/bin/bash
# process telegraf configuration template and start telegraf

service ntp start

set -e
envsubst '$NODE_NAME $NETWORK_NAME $FORWARDER_URL' < /etc/telegraf/telegraf.conf.tmpl > /etc/telegraf/telegraf.conf
exec telegraf
