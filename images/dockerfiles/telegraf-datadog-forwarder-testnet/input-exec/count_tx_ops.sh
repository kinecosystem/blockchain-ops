#!/usr/bin/env bash

url="https://horizon-testnet.kin.org/ledgers?limit=1&order=desc"
data=$(curl -s "$url")
tx_count=$(echo "$data" | jq -r "._embedded.records[0].transaction_count")
ops_count=$(echo "$data" | jq -r "._embedded.records[0].operation_count")
printf '%s\n' "ledger,stellar_network=testnet tx_count=$tx_count,ops_count=$ops_count"
