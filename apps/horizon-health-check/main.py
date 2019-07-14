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
HORIZON_INFO_URL = os.environ['HORIZON_INFO_URL']
BUILD_VERSION = os.environ['BUILD_VERSION']
REQUEST_TIMEOUT = float(os.environ['REQUEST_TIMEOUT'])
MAX_HEALTHY_DIFF = 10


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
        core_response = requests.get(CORE_INFO_URL, timeout=REQUEST_TIMEOUT)
        core_response.raise_for_status()
        core_info = core_response.json()['info']
        is_core_synced = core_info['state'] == 'Synced!'

        horizon_response = requests.get(HORIZON_INFO_URL, timeout=REQUEST_TIMEOUT)
        horizon_response.raise_for_status()

        horizon_info = horizon_response.json()
        core_latest_ledger = int(horizon_info['core_latest_ledger'])
        history_latest_ledger = int(horizon_info['history_latest_ledger'])
        is_horizon_synced = get_horizon_status(core_info, core_latest_ledger, history_latest_ledger)

        msg = generate_status_msg(is_core_synced, is_horizon_synced)
        if is_core_synced and is_horizon_synced:
            return make_reply(msg, 200)
        return make_reply(msg, 503)
    except Exception as e:
        return make_reply(f'Could not perform health check: {str(e)}', 503)


def generate_status_msg(is_core_synced, is_horizon_synced):
    horizon_status = 'synced' if is_horizon_synced else 'not synced'
    core_status = 'synced' if is_core_synced else 'not synced'
    msg = f'Core, Horizon status is: ({core_status}, {horizon_status})'
    return msg


def get_horizon_status(core_info, core_latest_ledger, history_latest_ledger):
    horizon_db_sync = (core_latest_ledger - history_latest_ledger) < MAX_HEALTHY_DIFF
    # Check if core_latest_ledger from Horizon is in sync with the Ladger num
    horizon_core_sync = (abs(core_info['ledger']['num'] - core_latest_ledger) < MAX_HEALTHY_DIFF)
    return horizon_db_sync and horizon_core_sync
