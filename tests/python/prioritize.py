"""Receive seeds and add them as prioritizers to whitelist account."""
import argparse
import logging

from kin import KinClient, Environment as KinEnvironment
from kin.blockchain.builder import Builder

from helpers import (NETWORK_NAME, MIN_FEE,
                     add_prioritizers, load_accounts)


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def parse_args():
    """Generate and parse CLI arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument('--whitelist-seed', required=True, type=str, help='Whitelist account seed')
    parser.add_argument('--prioritizer-seeds-file', required=True, type=str, help='File path to prioritizer seeds file')
    parser.add_argument('--passphrase', required=True, type=str, help='Network passphrase')
    parser.add_argument('--horizon', required=True, type=str, help='Horizon endpoint URL')

    return parser.parse_args()


def main():
    """Receive seeds and add them as prioritizers to whitelist account."""
    args = parse_args()
    env = KinEnvironment(NETWORK_NAME, args.horizon, args.passphrase)
    prioritizer_kps = load_accounts(args.prioritizer_seeds_file)
    whitelist_builder = Builder(env.name, KinClient(env).horizon, MIN_FEE, args.whitelist_seed)
    add_prioritizers(whitelist_builder, prioritizer_kps)


if __name__ == '__main__':
    main()
