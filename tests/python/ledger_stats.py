"""Print interesting ledger information for given ledger range."""
import argparse
import json
import logging
import urllib.parse as urlparse
from collections import defaultdict

from kin.blockchain.horizon import Horizon
from kin.config import SDK_USER_AGENT


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def parse_args():
    """Generate and parse CLI arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument('--start-ledger', required=True, type=int, help='First ledger number to fetch transactions from')
    parser.add_argument('--end-ledger', required=True, type=int, help='Last ledger number to fetch transactions from')
    parser.add_argument('--horizon', required=True, type=str, help='Horizon endpoint URL')

    return parser.parse_args()


def ledger_transactions(ledger, horizon):
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

    params = {'limit': MAX_RESULTS, 'order': 'asc'}
    res = horizon.ledger_transactions(ledger, params=params)
    txs = [tx for tx in res['_embedded']['records']]

    # continue paginating only if there are any records returned
    while res['_embedded']['records']:
        res = horizon.ledger_transactions(ledger, params={**{'cursor': next_cursor(res)}, **params})
        txs.extend([tx for tx in res['_embedded']['records']])

    logging.debug('%d transactions found in ledger %d', len(txs), ledger)

    return txs


def main():
    args = parse_args()

    logging.info('fetching transactions for ledger range %d - %d', args.start_ledger, args.end_ledger)

    horizon = Horizon(horizon_uri=args.horizon, user_agent=SDK_USER_AGENT)

    # create {ledger num: [ledger txs]} dictionary
    ledgers = (ledger_transactions(n, horizon)
               for n in range(args.start_ledger, args.end_ledger + 1))

    for ledger_num, ledger_txs in enumerate(ledgers, start=args.start_ledger):
        sig_count = defaultdict(lambda: 0)
        for tx in ledger_txs:
            num_sigs = len(tx['signatures'])
            sig_count[str(num_sigs)] += 1

        ledger_info = {
            'ledger_number': ledger_num,
            'max_tx_set_size': int(horizon.ledger(ledger_num)['max_tx_set_size']),
            'num_txs': len(ledger_txs),
            'tx_signature_count': sig_count,
        }

        print(json.dumps(ledger_info))


if __name__ == '__main__':
    main()
