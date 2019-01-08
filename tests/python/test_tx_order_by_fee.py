"""Test the prioritization of transactions in the ledger according to the fee"""

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


async def send_txs(txs):
    with ThreadPoolExecutor(max_workers=5) as executor:
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

    # Set ledger tx size to 3
    requests.get('http://localhost:11626/upgrades?mode=set&maxtxsize=3&upgradetime=2018-10-15T18:34:00Z')

    # Create the root account object
    root_account = client.kin_account(derive_root_account(PASSPHRASE).secret_seed)
    print('Root account object created')

    minimum_fee = client.get_minimum_fee()
    # Create an account with 0 base reserve
    test_account = Keypair()
    root_account.create_account(test_account.public_address, 0, minimum_fee)
    assert client.does_account_exists(test_account.public_address)
    print('Test account created')

    accounts = [Keypair() for _ in range(5)]
    builder = Builder('LOCAL', client.horizon, fee=minimum_fee, secret=root_account.keypair.secret_seed)
    for keypair in accounts:
        builder.append_create_account_op(keypair.public_address, '100')

    builder.get_sequence()
    builder.sign()
    builder.submit()

    print('Created 5 accounts')

    txs = []
    for index, account in enumerate(accounts, start=1):
        builder = Builder('LOCAL', client.horizon, fee=minimum_fee * index, secret=account.secret_seed)
        builder.append_manage_data_op('test', 'test'.encode())
        builder.get_sequence()
        builder.sign()
        txs.append(builder)

    initial_ledger = get_latest_ledger(client)['sequence']
    print(f'Initial ledger: {initial_ledger}')
    while initial_ledger == get_latest_ledger(client)['sequence']:
        time.sleep(0.5)

    first_populated_ledger = initial_ledger + 2
    second_populated_ledger = initial_ledger + 3

    print(f'Sending on ledger: {first_populated_ledger}')

    print(f'Sending txs at {time.strftime("%d/%m/%Y %H:%M:%S")}')
    await send_txs(txs)
    print(f'Done sending txs at {time.strftime("%d/%m/%Y %H:%M:%S")}')

    first_ledger_txs = client.horizon.ledger_transactions(first_populated_ledger)['_embedded']['records']
    second_ledger_txs = client.horizon.ledger_transactions(second_populated_ledger)['_embedded']['records']

    # First ledger should have txs where fee>=300
    first_txs = sum(1 for tx in first_ledger_txs if tx['fee_paid'] >= 300)
    assert first_txs == 3

    print('Verified first ledger')

    # Second ledger should have txs where fee<=200
    second_txs = sum(1 for tx in second_ledger_txs if tx['fee_paid'] <= 200)
    assert second_txs == 2

    print('Verified seconds ledger')


if __name__ == '__main__':
    asyncio.run(main())
