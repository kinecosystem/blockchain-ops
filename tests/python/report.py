import argparse
import csv
import json
import logging
import time
import urllib.parse as urlparse
from datetime import datetime

from kin.blockchain.horizon import Horizon
from kin.config import SDK_USER_AGENT


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def parse_args():
    """Generate and parse CLI arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument('--start-ledger', required=True, type=int, help='First ledger number to fetch transactions from')
    parser.add_argument('--end-ledger', required=True, type=int, help='Last ledger number to fetch transactions from')

    parser.add_argument('--input', required=True, type=str, help='Spam results JSON output')
    parser.add_argument('--output', default='spam-results-{}.csv'.format(str(int(time.time()))), type=str, help='Spam results CSV output')

    parser.add_argument('--horizon', required=True, type=str, help='Horizon endpoint URL')

    return parser.parse_args()


def ledger_transactions_created_at(ledger, horizon):
    """Paginate and return a {hash: created_at} dictionary for all transactions in given ledger number."""
    MAX_RESULTS = 200  # horizon hardcoded limit

    logging.debug('fetching transactions for ledger %d', ledger)

    def next_cursor(res):
        url = res['_links']['next']['href']
        p = urlparse.urlparse(url)
        try:
            return urlparse.parse_qs(p.query)['cursor'][0]
        except KeyError:
            # it looks like an empty cursor value points to 'the first page'
            return ''

    def tx_dict_from_results(res):
        txs_created_at = {}
        for tx in res['_embedded']['records']:
            txs_created_at[tx['hash']] = tx['created_at']
        return txs_created_at

    params = {'limit': MAX_RESULTS, 'order': 'asc'}
    res = horizon.ledger_transactions(ledger, params=params)

    txs_created_at = {}
    txs_created_at.update(tx_dict_from_results(res))

    # continue paginating only if there are any records returned
    while res['_embedded']['records']:
        res = horizon.ledger_transactions(ledger, params={**{'cursor': next_cursor(res)}, **params})
        txs_created_at.update(tx_dict_from_results(res))

    logging.debug('%d transactions found in ledger %d', len(txs_created_at), ledger)

    return txs_created_at


def main():
    args = parse_args()

    logging.info('fetching transactions for ledgers %d to %d', args.start_ledger, args.end_ledger)

    horizon = Horizon(horizon_uri=args.horizon, user_agent=SDK_USER_AGENT)
    txs_created_at = {}
    for ledger in range(args.start_ledger, args.end_ledger + 1):
        txs_created_at.update(ledger_transactions_created_at(ledger, horizon))

    logging.info('reading spam results')
    results = []
    with open(args.input) as f:
        for l in f:
            results.append(json.loads(l))

    logging.info('generating report csv and saving to %s', args.output)
    with open(args.output, 'w') as csvfile:
        w = csv.DictWriter(csvfile, fieldnames=list(results[0].keys()) + ['ledger_time'])
        w.writeheader()
        for i, tx in enumerate(results):
            if i % 10000 == 0:
                logging.info('processed %d transactions', i)

            hsh = tx['hash']
            try:
                tx['ledger_time'] = datetime.strptime(txs_created_at[hsh], '%Y-%m-%dT%H:%M:%SZ').timestamp()
            except KeyError:  # meaning tx wasn't in any ledger that was fetched
                tx['ledger_time'] = ''

            w.writerow(tx)

    logging.info('done')


if __name__ == '__main__':
    main()
