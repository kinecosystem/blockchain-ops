"""
Custom datadog-agent check that gets a json response from a given URL,
and extract a specific metric from it based on a given json path.
"""

import requests
from hashlib import md5
import time

from datadog_checks.checks import AgentCheck
from datadog_checks.errors import CheckException
from jsonpath_rw import parse


class JsonCheck(AgentCheck):
    """This class holds the json_check check and all the relevant events."""

    def check(self, instance):
        """Get a specific value from a json."""
        # datadog-agent agent collects values from the corresponding .yaml file
        url = instance['url']
        metrics = instance['metrics']
        default_timeout = self.init_config.get('default_timeout', 5)

        # Use a hash of the URL as an aggregation key
        aggregation_key = md5(url).hexdigest()

        # Make a get request
        try:
            r = requests.get(url, timeout=default_timeout)
        except requests.exceptions.Timeout:
            self.timeout_event(url, default_timeout, aggregation_key)
            return

        if not r.ok:
            # If the request was not successful
            self.status_code_event(url, r, aggregation_key)
            return

        data = r.json()
        for metric in metrics:
            for name, obj in metric.items():
                path, typ = obj['path'], obj['type'].lower()
                try:
                    # Get the value from the path in the json file
                    expression = parse(path)
                    match = expression.find(data)[0].value

                    if typ == 'gauge':
                        self.gauge(name, float(match))
                    elif typ == 'count':
                        self.count(name, float(match))
                    elif typ == 'rate':
                        self.rate(name, float(match))
                    else:
                        raise CheckException('Configuration error: Unknown metric type "{}" for metric "{}"'.format(typ, name))

                except IndexError:
                    # If there is no matching value
                    self.no_match_event(url, path, aggregation_key)
                except ValueError:
                    # If the matching value is not a number
                    self.unexpected_match_event(url, path, match, aggregation_key)

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
