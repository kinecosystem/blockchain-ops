#!/bin/sh
result=$(uptime | grep -ohe 'load average[s:][: ].*' | awk '{ print $4 }'|awk '{gsub(/,$/,""); print}')
echo 'load_5 load='$result
