"""
a status that exposes the blockchain's status via a set a cores

Healthy: Corresponding stellar-core is 'Synced'
Unhealthy: Corresponding stellar-core is not 'Synced'
"""

import logging
import json
import time
import os

import requests
from flask import Flask
from flask_cors import CORS

from collections import namedtuple
import time
import asyncio
from concurrent.futures import FIRST_COMPLETED
import aiohttp


CORE_URLS = (os.environ.get('CORE_URLS')).split(',') # accept coma-delimited list of ips
BUILD_VERSION = os.environ.get('BUILD_VERSION')
REQUEST_TIMEOUT = float(os.environ.get('REQUEST_TIMEOUT', 2))
logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

app = Flask(__name__)
CORS(app)

@app.route("/status")
def status():
    """Check if the stellar core is synced."""
    try:
        return (asyncio.run(make_requests()))
    except Exception as e:
        return make_reply(f'Could not perform health check: {str(e)}', 400) # cant be 5xx since fargate will terminate the app if that happens

async def make_requests():
    futures = [fetch_ip(url) for url in CORE_URLS]
    done, pending = await asyncio.wait(
        futures, return_when=FIRST_COMPLETED)
    return (done.pop().result())


async def fetch_ip(url):
    start = time.time()
    print('Fetching from {}'.format(url))
    json_response = await aiohttp_get_json(url)
    logging.info('{} finished. took: {:.2f} seconds'.format(url, time.time() - start))
    is_core_synced = not None and json_response['info']['state'] == 'Synced!'
    core_db_ledger = int(json_response['info']['ledger']['num'])
    core_db_age = int(json_response['info']['ledger']['age'])
    msg={'synced': is_core_synced,
         'ledger': core_db_ledger,
         'age': core_db_age}
    if is_core_synced:
        return make_reply(msg, 200)
    return make_reply(msg, 400) # cant be 5xx since fargate will terminate the app if that happens


async def aiohttp_get_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

def make_reply(msg, code):
    """Create a JSON reply for /status."""
    reply = {
        'status': 'Healthy' if code == 200 else 'Unhealthy',
        'data': msg
    }
    return json.dumps(reply), code

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
