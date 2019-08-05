
# Prometheus

Prometheus is an open-source system for monitoring. its a time-series database and a graphing engine.
[link to the Prometheus project](https://prometheus.io)

We are using it to collect and store horizon and health metrics that are graphed on our kin.org website.
At the moment, prometheus stores 2 kinds of metrics:
 - blockchain health metrics - whether the horizons are up and healthy.
 - reponse time and request counts for POST and GET requests
 
 All metrics should be kept for at least 180 days.
 
Blockchain health is a metric that's gathered from a telegraf client that sits in Frankfurt, Tokyo and Oregon and performs periodic HTTP requests into our horizons url and calculates the average response time.

## Configuration
Prometheus is running on docker-compose, installed on 2 instances (not as a synced cluster, but rather as two independent instances for high availability)

Configuration files for Prometheus are stored in this repo.

### Installation

 - VPC: Default Subnets: 2 private subnets, 2 public subnets 
 - Instances: 2 instances, each instance run on a different private subnet 
 - LoadBalancer: ALB with a target group that has 1 of the 2 prometheus (you cant add them both at the same time as it cauases 'jumps' in the graph. so only one prometheus can be in the tg at any given time, but both are collecting metrics at all times, for HA).
 - Domain: Route53 record on kin.org from  [https://prometheus-dashboard.kin.org/graph](https://prometheus-dashboard.kin.org/graph) to the ALB.

## Monitoring Prometheus:
the Prometheus "cluster" itself is monitored in datadog. Each prometheus instnace runs a local Telegraf which forwards the metrics into DD via the metric-forwarder machine.

## Alerts
Alerts exists on DataDog:

 - Disk space on the prometheus instances
 - Load (5 minutes avg)
 - Access to the domain (Synthetics): [https://prometheus-dashboard.kin.org/graph](https://prometheus-dashboard.kin.org/graph)
