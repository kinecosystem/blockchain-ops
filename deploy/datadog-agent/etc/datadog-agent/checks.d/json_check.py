import requests
import json
from hashlib import md5
import time

from datadog_checks.checks import AgentCheck
from jsonpath_rw import parse


class JsonCheck(AgentCheck):
    def check(self, instance):
        # datadog-agent agent collects values from the corresponding .yaml file
        url = instance['url']
        metrics = instance['metrics']
        default_timeout = self.init_config.get('default_timeout', 5)

        # Use a hash of the URL as an aggregation key
        aggregation_key = md5(url).hexdigest()

        # Make a get request
        try:
            r = requests.get(url, timeout=default_timeout)

            if r.status_code == 200:
                data = json.loads(r.text)
                for metric in metrics:
                    for name, path in metric.items():
                        try:
                            # Get the value from the path in the json file
                            expression = parse(path)
                            match = expression.find(data)[0].value
                            self.gauge(name, float(match))
                        except IndexError:
                            # If there is no matching value
                            self.no_match_event(url, path, aggregation_key)
                        except ValueError:
                            # If the matching value is not a number
                            self.unexpected_match_event(url, path, match, aggregation_key)
            else:
                # If the request was not successful
                self.status_code_event(url, r, aggregation_key)
        except requests.exceptions.Timeout:
            # If there's a timeout
            self.timeout_event(url, default_timeout, aggregation_key)

    def timeout_event(self, url, timeout, aggregation_key):
        self.event({
            'timestamp': int(time.time()),
            'event_type': 'json_check',
            'msg_title': 'request timeout',
            'msg_text': 'Request to {} timed out after {} seconds.'.format(url, timeout),
            'aggregation_key': aggregation_key
        })

    def status_code_event(self, url, r, aggregation_key):
        self.event({
            'timestamp': int(time.time()),
            'event_type': 'json_check',
            'msg_title': 'Invalid status code for {}'.format(url),
            'msg_text': '{} returned a status code of {}.'.format(url, r.status_code),
            'aggregation_key': aggregation_key
        })

    def no_match_event(self, url, path, aggregation_key):
        self.event({
            'timestamp': int(time.time()),
            'event_type': 'json_check',
            'msg_title': 'no matching value',
            'msg_text': 'No matching value was found for {} from {}'.format(path, url),
            'aggregation_key': aggregation_key
        })

    def unexpected_match_event(self, url, path, match, aggregation_key):
        self.event({
            'timestamp': int(time.time()),
            'event_type': 'json_check',
            'msg_title': 'unexpected match',
            'msg_text': 'for {} in {} , expected to get a numeric match, got "{}"'.format(path, url, match),
            'aggregation_key': aggregation_key
        })