Blockchain Dashboard

Here be files related to the public blockchain dashboard, part of the kin.org site. 

the blockchain dashboard is composed of two main parts:

1. a Prometheus "cluster" that collects, stores and makes available data regarding our blockchain.
2. a telegraf client (running in frankfurt) that periodically samples the blockchain's entry points and reports health metrics to Prometheus.

The blockchain dashboard is a web page that retrieves data from prometheus (as well as other places).
we monitor both Prometheus and the healthcheck client using DD. see: https://app.datadoghq.com/dashboard/yz7-2ek-5fy/blockchain---prometheus?from_ts=1563425813517&to_ts=1563426533517&live=false&tile_size=m
