# Stellar Core Telegraf

This is a docker image for a telegraf client that runs on horizon and curls into core's /info endpoint and then sends the metrics back home

## Usage
In docker-compose, add the following service next to the stellar-core one.

services:
---
version: "3"
services:
  network-latency-telegraf:
    environment:
      NODE_NAME: "<node-name-goes-here>"
      TARGET_URL: "http://<core-url-goes-here>:11626/info"
    image: kinecosystem/network-latency-telegraf
    restart: always
    logging:
      driver: json-file
      options:
        max-size: 100m
        max-file: "3"

## TODO
 
