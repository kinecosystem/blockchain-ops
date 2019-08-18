#!/bin/bash
# this script checks the hosts sysctl configuration and alerts on difference

set -e

declare -A sysctl_stats

sysctl_stats=(
["fs.file-max"]="5000000"
["net.core.somaxconn"]="65535"
["net.core.netdev_max_backlog"]="400000"
["net.ipv4.tcp_max_syn_backlog"]="65536"
["net.ipv4.tcp_max_orphans"]="262144"
["net.core.rmem_max"]="16777216"
["net.core.wmem_max"]="16777216"
["net.core.rmem_default"]="10000000"
["net.core.wmem_default"]="10000000"
["net.ipv4.tcp_mem"]="30000000 30000000 30000000"
["net.ipv4.tcp_rmem"]="30000000 30000000 30000000"
["net.ipv4.tcp_wmem"]="30000000 30000000 30000000"
["net.ipv4.tcp_fastopen"]="3"
["net.ipv4.tcp_fin_timeout"]="10"
["net.ipv4.tcp_tw_reuse"]="1"
["net.ipv4.tcp_slow_start_after_idle"]="0"
["net.ipv4.tcp_syncookies"]="1"
["net.ipv4.tcp_timestamps"]="1"
["net.ipv4.tcp_keepalive_time"]="60"
["net.ipv4.tcp_keepalive_intvl"]="10"
["net.ipv4.tcp_keepalive_probes"]="6"
["net.ipv4.tcp_mtu_probing"]="1"
["net.ipv4.conf.all.rp_filter"]="1"
["net.ipv4.conf.default.rp_filter"]="1"
["net.ipv4.tcp_max_tw_buckets"]="2000000"
["net.netfilter.nf_conntrack_max"]="131072"
)

for stat in "${!sysctl_stats[@]}"; do
	    curr=`sysctl $stat | awk '{print $3}'`
	        if [ "$curr" != "${sysctl_stats[$stat]}" ]; then
			          #echo "current conf for $stat: $curr , Expected: ${sysctl_stats[$stat]}";
				  echo "false"
				  exit 1
                fi
done
echo "true"
exit 0
