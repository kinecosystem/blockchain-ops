"""Generate transaction XDR objects for spam test according to given spam rate.

NOTE each spam builder generates a single XDR, thus it should be used only once during a spam test.
This is to avoid sequence number collissions in case transactions do not get processed,
which is possible for unprioritized transactions and other unknown cases (which this test attempts to uncover).
"""
import argparse
import asyncio
import concurrent.futures
import json
import logging
import math
import time
from typing import List

from kin import Keypair, Environment
from kin.blockchain.builder import Builder

from helpers import (TX_SET_SIZE, NETWORK_NAME, MIN_FEE,
                     load_accounts, get_sequences_multiple_endpoints)


AVG_BLOCK_TIME = 5  # seconds


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def parse_args():
    """Generate and parse CLI arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument('--length', required=True, type=int, help='Test length in seconds')
    parser.add_argument('--txs-per-ledger', required=True, type=int, help='Transaction rate to submit (spam) in parallel for every ledger round')
    parser.add_argument('--prioritizer-seeds-file', required=True, type=str, help='File path to prioritizer seeds file')
    parser.add_argument('--spammer-seeds-file', required=True, type=str, help='File path to spammer seeds file')
    parser.add_argument('--out', default='spam-results-{}.json'.format(str(int(time.time()))), type=str, help='Spam results JSON output')

    parser.add_argument('--passphrase', type=str, help='Network passphrase')
    parser.add_argument('--horizon', action='append',
                        help='Horizon endpoint URL (use multiple --horizon flags for multiple addresses)')

    return parser.parse_args()


async def generate_spam_tx_xdrs(prioritizers, builders, length, tx_per_ledger):
    """Generate transaction XDR objects for each builder according to given spam rate.

    NOTE each spam builder generates a single XDR, thus it should be used only once during a spam test.
    This is to avoid sequence number collissions in case transactions do not get processed,
    which is possible for unprioritized transactions and other unknown cases (which this test attempts to uncover).
    """
    rounds_num = math.ceil(length // AVG_BLOCK_TIME)
    if len(builders) != tx_per_ledger * rounds_num:
        raise RuntimeError('Amount of spammer seeds should exactly match (transactions per ledger * spam round numbers)')

    with concurrent.futures.ProcessPoolExecutor() as process_pool:
        futurs = []
        remaining_builders = builders
        for rnd in range(rounds_num):
            # pop builders for this round and trim original builder list
            round_builders = remaining_builders[-tx_per_ledger:]
            remaining_builders = remaining_builders[:-tx_per_ledger]

            assert round_builders

            coro = generate_spam_round_tx_xdrs(process_pool,
                                               prioritizers,
                                               round_builders[:TX_SET_SIZE - 1],
                                               round_builders[TX_SET_SIZE-1:tx_per_ledger],
                                               rnd)

            futurs.append(asyncio.create_task(coro))

        spam_rounds = await asyncio.gather(*futurs)

    return spam_rounds


def build_and_sign(builder, dest_address, payment_amount, prioritizer_seed=None):
    """Build a transaction for given builder and return transaction hash and XDR."""
    builder.append_payment_op(dest_address, str(payment_amount))
    builder.sign(builder.keypair.seed().decode())

    # prioritize transaction by adding a prioritizer signature
    if prioritizer_seed:
        builder.sign(prioritizer_seed)

    return builder.hash_hex(), builder.gen_xdr().decode()


# all transactions are payments to the same address
#
# TODO can this potentially create deadlocks when applying them?
async def generate_spam_round_tx_xdrs(pool, prioritizers: List[Keypair], prioritized_builders, unprioritized_builders, rnd):
    """Generate transaction XDRs for a single spam round (ledger) according to given builders.

    Some of the generated transactions are prioritized using given prioritizer seeds,
    and some are unprioritized and not signed by a prioritizer account.

    All prioritized transactions are expected to be included in the next ledger.
    Only one out of all unprioritized transactions is expected to be included in the next ledger.

    Return a metadata dictionary with the generated XDRs along with additional information.
    """
    logging.info('generating transaction xdrs for round %d', rnd)

    payment_amount = 1
    payment_dest = prioritizers[0]  # all transactions are payments to the same address

    # generate unprioritized payment transactions
    # we generate them first, thus will submit them first,
    # because we want to test if prioritized transactions actually get priority over them
    loop = asyncio.get_running_loop()
    futurs = []
    for builder in unprioritized_builders:
        f = loop.run_in_executor(
            pool, build_and_sign,
            builder, payment_dest.public_address, payment_amount, None)
        futurs.append(f)

    if not futurs:
        raise RuntimeError('no futures to gather')

    tx_metadata = {}
    for tx_hash, tx_xdr in await asyncio.gather(*futurs):
        tx_metadata[tx_hash] = {'round': rnd, 'prioritized': False, 'xdr': tx_xdr}

    # generate prioritized transactions
    futurs = []
    for builder, prioritizer in zip(prioritized_builders, prioritizers):
        f = loop.run_in_executor(
            pool, build_and_sign,
            builder, payment_dest.public_address, payment_amount, prioritizer.secret_seed)
        futurs.append(f)

    if not futurs:
        raise RuntimeError('no futures to gather')

    for tx_hash, tx_xdr in await asyncio.gather(*futurs):
        tx_metadata[tx_hash] = {'round': rnd, 'prioritized': True, 'xdr': tx_xdr}

    return tx_metadata


async def main():
    args = parse_args()

    # setup network
    Environment(NETWORK_NAME, args.horizon[0], args.passphrase)

    logging.info('loading prioritizer accounts')
    prioritizer_kps = [kp for kp in load_accounts(args.prioritizer_seeds_file)]
    logging.info('%d prioritizer accounts loaded', len(prioritizer_kps))

    logging.info('loading spammer accounts')
    spam_kps = load_accounts(args.spammer_seeds_file)
    logging.info('%d spammer accounts loaded', len(spam_kps))

    logging.info('fetching sequence number for spammer accounts')
    spam_sequences = await get_sequences_multiple_endpoints(args.horizon, [kp.public_address for kp in spam_kps])

    logging.info('generating spammer builders')
    spam_builders = []

    # we're not submitting using the builder - just generating the xdr,
    # so each builder's horizon instance is irrelevant
    stub_horizon = args.horizon[0]
    for kp, seq in zip(spam_kps, spam_sequences):
        b = Builder(NETWORK_NAME, stub_horizon, MIN_FEE, kp.secret_seed)
        b.sequence = str(seq)
        spam_builders.append(b)

    logging.info('generating spam transaction xdrs')
    spam_rounds = await generate_spam_tx_xdrs(prioritizer_kps, spam_builders, args.length, args.txs_per_ledger)
    logging.info('done generating spam transaction xdrs')

    logging.info('writing transaction xdrs to file %s', args.out)
    with open(args.out, 'w') as f:
        for rnd in spam_rounds:
            f.write('{}\n'.format(json.dumps(rnd)))

    logging.info('done')


if __name__ == '__main__':
    asyncio.run(main())
