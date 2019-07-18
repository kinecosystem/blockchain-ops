Here be files related to the public blockchain dashboard, part of the kin.org site. 

the blockchain dashboard is composed of two main parts:

1. a Prometheus "cluster" that collects, stores and makes available data regarding our blockchain.
2. a telegraf client (running in frankfurt) that periodically samples the blockchain's entry points and reports health metrics to Prometheus.

