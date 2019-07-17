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
CORE_INFO_URL = os.environ.get('CORE_INFO_URL')
HORIZON_INFO_URL = os.environ.get('HORIZON_INFO_URL')
BUILD_VERSION = os.environ.get('BUILD_VERSION')
REQUEST_TIMEOUT = float(os.environ.get('REQUEST_TIMEOUT', 2))
MAX_HEALTHY_DIFF = 10


@APP.route("/status")
def status():
    """Check if the stellar core is synced."""
    try:
        core_info = get_data(CORE_INFO_URL)
        horizon_info = get_data(HORIZON_INFO_URL)

        is_core_synced = core_info['info']['state'] == 'Synced!'
        is_horizon_synced = get_horizon_sync_status(core_info, horizon_info)
        msg = generate_status_msg(is_core_synced, is_horizon_synced)
        if is_core_synced and is_horizon_synced:
            return make_reply(msg, 200)
        return make_reply(msg, 503)
    except Exception as e:
        return make_reply(f'Could not perform health check: {str(e)}', 503)


def make_reply(msg, code):
    """Create a JSON reply for /status."""
    reply = {
        'status': 'Healthy' if code == 200 else 'Unhealthy',
        'description': msg,
        'start_timestamp': START_TIMESTAMP,
        'build': BUILD_VERSION
    }
    return json.dumps(reply), code


def get_data(url):
    """Get JSON data from resource"""
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def generate_status_msg(is_core_synced, is_horizon_synced):
    """Create sync status message"""
    horizon_status = 'synced' if is_horizon_synced else 'not synced'
    core_status = 'synced' if is_core_synced else 'not synced'
    msg = f'Core, Horizon status is: ({core_status}, {horizon_status})'
    return msg


def get_horizon_sync_status(core_info, horizon_info):
    """Check if Horizon ledger count is aligned with Core current ledger"""
    core_db_ledger = int(core_info['info']['ledger']['num'])
    horizon_core_ledger = int(horizon_info['core_latest_ledger'])
    horizon_db_ledger = int(horizon_info['history_latest_ledger'])

    horizon_db_sync = abs(horizon_core_ledger - horizon_db_ledger) < MAX_HEALTHY_DIFF
    horizon_core_sync = abs(core_db_ledger - horizon_db_ledger) < MAX_HEALTHY_DIFF
    return horizon_db_sync and horizon_core_sync
