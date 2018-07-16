"""
Health check for Horizon.

Healthy: Corresponding stellar-core is 'Synced'
Unhealthy: Corresponding stellar-core is not 'Synced'
"""
import json
import time
import os

import requests
from flask import Flask
from flask_cors import CORS


APP = Flask(__name__)
CORS(APP)
START_TIMESTAMP = time.time()

# Load configuration from env variables
CORE_INFO_URL = os.environ['CORE_INFO_URL']
BUILD_VERSION = os.environ['BUILD_VERSION']
REQUEST_TIMEOUT = float(os.environ['REQUEST_TIMEOUT'])


def make_reply(msg, code):
    """Create a JSON reply for /status."""
    reply = {
        'status': 'Healthy' if code == 200 else 'Unhealthy',
        'description': msg,
        'start_timestamp': START_TIMESTAMP,
        'build': BUILD_VERSION
    }

    return json.dumps(reply), code


@APP.route("/status")
def status():
    """Check if the stellar core is synced."""
    try:
        response = requests.get(CORE_INFO_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        health = (response.json()['info']['state'] == 'Synced!')
        if health:
            return make_reply('Core is synced', 200)
        return make_reply('Core is not synced', 503)
    except Exception as e:
        return make_reply('Could not check core: {}'.format(str(e)), 503)
