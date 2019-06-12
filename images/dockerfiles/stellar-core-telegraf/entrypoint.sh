#!/bin/bash
# process telegraf configuration template and start telegraf

set -e
if [ -z ${FORWARDER_URL+x} ]; then export FORWARDER_URL="http://metrics.kininfrastructure.com:8086"; fi
envsubst '$NODE_NAME $NETWORK_NAME $FORWARDER_URL' < /etc/telegraf/telegraf.conf.tmpl > /etc/telegraf/telegraf.conf
exec telegraf
