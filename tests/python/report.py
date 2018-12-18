import argparse
import csv
import json
import logging
import time
from datetime import datetime

from kin.blockchain.horizon import Horizon
from kin.config import SDK_USER_AGENT


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')


def parse_args():
    """Generate and parse CLI arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument('--input', type=str, help='Spam results JSON output')
    parser.add_argument('--output', default='spam-results-{}.csv'.format(str(int(time.time()))), type=str, help='Spam results CSV output')
    parser.add_argument('--horizon', type=str, help='Horizon endpoint URL')

    return parser.parse_args()


LEDGERS = {}


def ledger_time(ledger, horizon):
    """Return ledger close time."""
    # failed txs have ledger = None
    # so we return an empty timestamp instead
    if not ledger:
        return ''

    global LEDGERS
    if ledger not in LEDGERS:
        logging.debug('fetching ledger %d', ledger)
        date_str = horizon.ledger(ledger)['closed_at']
        LEDGERS[ledger] = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ').timestamp()
    return LEDGERS[ledger]


def main():
    args = parse_args()

    logging.info('reading spam results')
    results = []
    with open(args.input) as f:
        for l in f:
            results.append(json.loads(l))

    logging.info('generating report csv')
    horizon = Horizon(horizon_uri=args.horizon, user_agent=SDK_USER_AGENT)
    with open(args.output, 'w') as csvfile:
        w = csv.DictWriter(csvfile, fieldnames=list(results[0].keys()) + ['ledger_time'])
        w.writeheader()
        for tx in results:
            w.writerow({**tx, **{'ledger_time': ledger_time(tx['ledger'], horizon)}})

    logging.info('done')


if __name__ == '__main__':
    main()
