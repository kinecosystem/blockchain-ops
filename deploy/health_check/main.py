import requests
import yaml
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# For 'health', true is healthy
health = True
CORE_URL = ''


def check_core(core_url):
    # Check if the stellar core is synced
    global health
    try:
        r = requests.get(core_url+'/info')
        r.raise_for_status()

        health = (r.json()['info']['state'] == 'Synced!')
    except:
        health = False


def check_horizon():
    # Check if the ratio of success/failed requests is < 0.1
    global health
    try:
        r = requests.get('http://horizon-kik.kininfrastructure.com/metrics')
        r.raise_for_status()

        total_requests = r.json()['requests.total']['1m.rate']
        failed_requests = r.json()['requests.failed']['1m.rate']
        ratio = failed_requests / total_requests

        health = (ratio < 0.1)
    except:
        health = False


@app.route("/status")
def status():
    # If healthy, check horizon, if unhealthy, check core
    global health
    global CORE_URL
    if health:
        check_horizon()
    else:
        check_core(CORE_URL)

    if health:
        return 'Healthy', 200
    return 'Unhealthy', 503


def get_core_url():
    # Get the stellar-core url from the configuration file that is already on the machine
    with open('/home/ubuntu/docker-compose.yml', 'r') as stream:
            data = yaml.safe_load(stream)
    return data['services']['horizon']['environment']['STELLAR_CORE_URL']


def main():
    global CORE_URL
    CORE_URL = get_core_url()
    app.run('0.0.0.0', 4000)


if __name__ == '__main__':
    main()
