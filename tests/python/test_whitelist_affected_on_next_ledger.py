"""Test that whitelist changes take effect on the subsequent ledger"""

import sys
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from kin import KinClient, Environment, Keypair
from kin.blockchain.builder import Builder
from helpers import derive_root_account

import requests

import time


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')


PASSPHRASE = sys.argv[1]
WHITELIST_MANAGER_KEYPAIR = Keypair(sys.argv[2])


async def send_txs(txs):
    with ThreadPoolExecutor(max_workers=2) as executor:
        loop = asyncio.get_running_loop()
        promises = [loop.run_in_executor(executor, tx.submit) for tx in txs]

        for _ in await asyncio.gather(*promises):
            pass


def get_latest_ledger(client):
    params = {'order': 'desc', 'limit': 1}
    return client.horizon.ledgers(params=params)['_embedded']['records'][0]


async def main():
    # Create the environment
    local_env = Environment('LOCAL', 'http://localhost:8000', PASSPHRASE, 'http://localhost:8001')

    # Create a client
    client = KinClient(local_env)
    print('Client created')

    initial_ledger_size = get_latest_ledger(client)['max_tx_set_size']

    # Set ledger tx size to 1
    requests.get('http://localhost:11626/upgrades?mode=set&maxtxsize=1&upgradetime=2018-10-15T18:34:00Z')

    # Create the root account object
    root_account = client.kin_account(derive_root_account(PASSPHRASE).secret_seed)
    print('Root account object created')

    minimum_fee = client.get_minimum_fee()
    # Create an account with 0 base reserve
    test_account = Keypair()
    root_account.create_account(test_account.public_address, 0, minimum_fee)
    assert client.does_account_exists(test_account.public_address)
    print('Test account created')

    # Add the account to the whitelist
    if not client.does_account_exists(WHITELIST_MANAGER_KEYPAIR.public_address):
        root_account.create_account(WHITELIST_MANAGER_KEYPAIR.public_address, 10000, 100)
    print('Created whitelisting account')

    initial_ledger = get_latest_ledger(client)['sequence']

    while initial_ledger == get_latest_ledger(client)['sequence']:
        time.sleep(0.5)

    print(f'Adding account to whitelist on ledger: {initial_ledger + 2}')

    builder = Builder('LOCAL', client.horizon, fee=minimum_fee, secret=WHITELIST_MANAGER_KEYPAIR.secret_seed)
    builder.get_sequence()
    builder.append_manage_data_op(test_account.public_address, test_account._hint)
    builder.sign()
    builder.submit()

    print('Added account to whitelist')

    while initial_ledger + 1 == get_latest_ledger(client)['sequence']:
        time.sleep(0.5)

    print(f'Submitting tx from test account on ledger: {initial_ledger + 3}')

    builder = Builder('LOCAL',client.horizon, fee=0, secret=test_account.secret_seed)
    builder.append_manage_data_op('test','test'.encode())
    builder.get_sequence()
    builder.sign()
    builder.submit()

    while initial_ledger + 2 == get_latest_ledger(client)['sequence']:
        time.sleep(0.5)

    populated_ledger_txs = client.horizon.ledger_transactions(initial_ledger + 3)['_embedded']['records']
    assert len(populated_ledger_txs) == 1
    assert populated_ledger_txs[0]['fee_paid'] == 0


if __name__ == '__main__':
    asyncio.run(main())
