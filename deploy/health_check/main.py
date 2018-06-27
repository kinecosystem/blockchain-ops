"""
Health check for Horizon.

Healthy: Corresponding stellar-core is 'Synced'
Unhealthy: Failed/Total requests is > 0.1
"""
import json
import time

import requests
from flask import Flask
from flask_cors import CORS

import config


app = Flask(__name__)
CORS(app)
start_timestamp = time.time()

# For 'health', true is healthy
health = True


def check_core():
    # Check if the stellar core is synced
    global health
    try:
        r = requests.get(config.CORE_INFO_URL)
        r.raise_for_status()

        health = (r.json()['info']['state'] == 'Synced!')
        if health:
            return make_reply('Core is synced', 200)
        return make_reply('Core is not synced', 503)
    except Exception as e:
        health = False
        return make_reply('Could not check core: {}'.format(str(e)), 503)


def check_horizon():
    # Check if the ratio of failed/total requests is < 0.1
    global health
    try:
        r = requests.get(config.HORIZON_METRICS_URL)
        r.raise_for_status()

        data = r.json()
        total_requests = data['requests.total']['1m.rate']
        failed_requests = data['requests.failed']['1m.rate']
        ratio = failed_requests / total_requests

        health = (ratio < config.MAX_REQUEST_RATIO)
        if health:
            return make_reply('Horizon failed requests ratio is {} < {}'
                              .format(ratio, config.MAX_REQUEST_RATIO), 200)
        return make_reply('Horizon failed requests ratio is {} > {}'
                          .format(ratio, config.MAX_REQUEST_RATIO), 503)
    except Exception as e:
        health = False
        return make_reply('Could not check horizon: {}'.format(str(e)), 503)


def make_reply(msg, code):
    # Create a json reply for /status
    reply = {
        'status': 'Healthy' if code == 200 else 'Unhealthy',
        'description': msg,
        'start_timestamp': start_timestamp,
        'build': config.BUILD_VER
    }

    return json.dumps(reply), code


@app.route("/status")
def status():
    # If healthy, check horizon, if unhealthy, check core
    global health
    if health:
        return check_horizon()
    else:
        return check_core()
