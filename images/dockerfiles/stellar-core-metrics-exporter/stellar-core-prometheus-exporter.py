import argparse
import requests
import os
import re
import time

# Prometheus client library
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, SummaryMetricFamily, REGISTRY, \
    HistogramMetricFamily

NON_METRICS_KEYS = ['_links']
app_name = os.environ.get('app', 'test')
urls = {
    'test': "http://localhost:8000/metrics",
    'horizon': "http://horizon:8000/metrics",
    'stellar-core': "http://stellar-core:11626/metrics"
}
parser = argparse.ArgumentParser(description='simple stellar-core Prometheus exporter/scraper')
parser.add_argument('--uri', type=str,
                    help=f'{app_name} metrics uri, default: {urls[app_name]}',
                    default=f'{urls[app_name]}')
parser.add_argument('--port', type=int,
                    help='HTTP bind port, default: 9473',
                    default=os.environ.get('port', 9473))
args = parser.parse_args()


class MetricsCollector(object):
    def collect(self):
        response = requests.get(args.uri)
        metrics = response.json()
        if app_name == 'stellar-core':
            metrics = metrics['metrics']
        # iterate over all metrics
        for k in metrics:
            if k in NON_METRICS_KEYS:
                continue

            filtered_metric_name = re.sub('\.|-|\s', '_', k).lower()
            base_metric_name = f"{app_name}_{filtered_metric_name}"
            if metrics[k]['type'] == 'timer':
                # we have a timer, expose as a Prometheus Summary
                metric_type_name = base_metric_name + '_' + metrics[k]['duration_unit']
                summary = SummaryMetricFamily(metric_type_name, 'libmedida metric type: ' + metrics[k]['type'],
                                              count_value=metrics[k]['count'],
                                              sum_value=(metrics[k]['mean'] * metrics[k]['count']))
                # add stellar-core calculated quantiles to our summary
                summary.add_sample(metric_type_name, labels={'quantile': '0.75'}, value=metrics[k]['75%'])
                summary.add_sample(metric_type_name, labels={'quantile': '0.95'}, value=metrics[k]['95%'])
                summary.add_sample(metric_type_name, labels={'quantile': '0.99'}, value=metrics[k]['99%'])
                yield summary
            elif metrics[k]['type'] == 'counter':
                # we have a counter, this is a Prometheus Gauge
                yield GaugeMetricFamily(base_metric_name, 'libmedida metric type: ' + metrics[k]['type'],
                                        value=metrics[k]['count'])
            elif metrics[k]['type'] == 'gauge':
                # we have a counter, this is a Prometheus Gauge
                yield GaugeMetricFamily(base_metric_name, 'Horizon metadata metric type: ' + metrics[k]['type'],
                                        value=metrics[k]['value'])
            elif metrics[k]['type'] == 'meter':
                # we have a meter, this is a Prometheus Counter
                yield CounterMetricFamily(base_metric_name, 'libmedida metric type: ' + metrics[k]['type'],
                                          value=metrics[k]['count'])


if __name__ == "__main__":
    REGISTRY.register(MetricsCollector())
    start_http_server(args.port)
    while True: time.sleep(1)
