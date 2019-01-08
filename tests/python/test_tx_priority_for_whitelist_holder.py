"""Test the prioritization of transactions in the ledger for the whitelist_holder"""

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

    builder = Builder('LOCAL', client.horizon, fee=minimum_fee, secret=WHITELIST_MANAGER_KEYPAIR.secret_seed)
    builder.get_sequence()
    builder.append_manage_data_op(test_account.public_address, test_account._hint)
    builder.sign()
    builder.submit()

    print('Added account to whitelist')

    for _ in range(5):
        txs = []
        first_builder = Builder('LOCAL',client.horizon, fee=minimum_fee, secret=test_account.secret_seed)
        first_builder.append_manage_data_op('test','test'.encode())
        first_builder.get_sequence()
        first_builder.sign()
        txs.append(first_builder)

        second_builder = Builder('LOCAL', client.horizon, fee=minimum_fee, secret=WHITELIST_MANAGER_KEYPAIR.secret_seed)
        second_builder.append_payment_op(test_account.public_address, '1')
        second_builder.get_sequence()
        second_builder.sign()
        txs.append(second_builder)

        initial_ledger = get_latest_ledger(client)['sequence']
        print(f'Initial ledger: {initial_ledger}')
        while initial_ledger == get_latest_ledger(client)['sequence']:
            time.sleep(0.5)

        first_populated_ledger = initial_ledger + 2

        print(f'Sending on ledger: {first_populated_ledger}')

        print(f'Sending txs at {time.strftime("%d/%m/%Y %H:%M:%S")}')
        await send_txs(txs)
        print(f'Done sending txs at {time.strftime("%d/%m/%Y %H:%M:%S")}')

        first_ledger_txs = client.horizon.ledger_transactions(first_populated_ledger)['_embedded']['records']

        # First ledger should have tx from whitelist_manager
        assert WHITELIST_MANAGER_KEYPAIR.public_address == first_ledger_txs[0]['source_account']
        print('Verified tx from whitelist manager got priority')


if __name__ == '__main__':
    asyncio.run(main())
