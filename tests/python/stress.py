"""Send prioritized and unprioritized transactions and verify prioritized transactions get priority when added to ledgers."""
import argparse
import asyncio
import json
import logging
import time

from helpers import send_txs_multiple_endpoints


AVG_BLOCK_TIME = 5  # seconds


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def parse_args():
    """Generate and parse CLI arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument('--xdrs-file', type=str, help='Transaction XDR list file, in JSON lines format')
    parser.add_argument('--out', default='spam-results-{}.json'.format(str(int(time.time()))), type=str, help='Spam results JSON output')
    parser.add_argument('--endpoint', required=True, action='append',
                        help='Endpoint URLs for submitting transactions (use multiple --endpoint flags for multiple addresses)')
    parser.add_argument('--submit-to-core', action='store_true', help='Submit to Core instead of Horizon')

    return parser.parse_args()


def load_spam_rounds(path):
    """Load spam round transaction XDRs."""
    spam_rounds = []
    with open(path) as f:
        for rnd in f:
            spam_rounds.append(json.loads(rnd))
    return spam_rounds


async def spam(endpoints, submit_to_horizon, spam_rounds):
    """Receive transaction XDR objects and submit them when their expected ledger arrives."""
    futurs = []
    for rnd, tx_metadata in enumerate(spam_rounds):
        f = spam_round(tx_metadata, endpoints, submit_to_horizon, rnd)

        futurs.append(f)

    results = await asyncio.gather(*futurs)
    return results


async def spam_round(tx_metadata, endpoints, submit_to_horizon, rnd):
    """Receive transaction XDR objects for a specific future ledger and submit them when that ledger time arrives."""
    xdrs = [tx['xdr'] for tx in tx_metadata.values()]

    # start the spam round only when the expected ledger time arrives
    await asyncio.sleep(rnd * AVG_BLOCK_TIME)

    # submit transactions
    #
    # NOTE some transactions can fail with HTTP 500 Server Error or HTTP 504 Server Timeout,
    # so don't raise an exception if this happens
    logging.info('spam round %d', rnd)

    submission_time = time.time()
    tx_results = await send_txs_multiple_endpoints(
        endpoints,
        xdrs,
        submit_to_horizon,
        [200, 500, 504] if submit_to_horizon else [200])

    logging.debug('done submitting %d transactions for round %d', len(xdrs), rnd)

    # create tx result object for each tx for reviewing later on
    results = []
    for (tx_hash, tx), tx_res in zip(tx_metadata.items(), tx_results):
        try:
            ledger = tx_res['ledger']
        except KeyError:  # probably 504
            ledger = None

        results.append({'hash': tx_hash,
                        'round': tx['round'],
                        'prioritized': tx['prioritized'],
                        'ledger': ledger,
                        'submission_time': submission_time})

    return results


async def main():
    """Load spam transaction XDR objects for all spam rounds and submitting to the network in a timely manner."""
    args = parse_args()

    logging.info('load spam transaction xdr objects for spam rounds')
    spam_rounds = load_spam_rounds(args.xdrs_file)

    logging.info('starting spam')
    results = await spam(
        args.endpoint,
        submit_to_horizon=(not args.submit_to_core),
        spam_rounds=spam_rounds)
    logging.info('done spamming')

    logging.info('writing transaction results to file')
    with open(args.out, 'w') as f:
        for spam_round in results:
            for tx in spam_round:
                f.write('{}\n'.format(json.dumps(tx)))

    logging.info('done')


if __name__ == '__main__':
    asyncio.run(main())
