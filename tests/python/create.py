"""Create accounts."""
import asyncio
import argparse
import logging

from kin import KinClient, Environment
from kin.blockchain.builder import Builder

from helpers import (NETWORK_NAME, MIN_FEE,
                     root_account_seed, create_accounts)


STARTING_BALANCE = 1e5


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def parse_args():
    """Generate and parse CLI arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument('--accounts', required=True, type=int, help='Amount of accounts to create')
    parser.add_argument('--passphrase', required=True, type=str, help='Network passphrase')
    parser.add_argument('--horizon', action='append',
                        help='Horizon endpoint URL (use multiple --horizon flags for multiple addresses)')

    return parser.parse_args()


async def main():
    """Create accounts and print their seeds to stdout."""
    args = parse_args()
    env = Environment(NETWORK_NAME, (args.horizon)[0], args.passphrase)
    builder = Builder(NETWORK_NAME, KinClient(env).horizon, MIN_FEE, root_account_seed(args.passphrase))
    builder.sequence = builder.get_sequence()
    kps = await create_accounts(builder, args.horizon, args.accounts, STARTING_BALANCE)

    for kp in kps:
        print(kp.secret_seed)


if __name__ == '__main__':
    asyncio.run(main())
