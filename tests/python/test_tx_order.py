"""Test the prioritization of transactions in the ledger"""

import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

from kin import KinClient, Environment, Keypair
from kin.blockchain.builder import Builder
from helpers import derive_root_account

import requests

import time

PASSPHRASE = sys.argv[1]
WHITELIST_MANAGER_KEYPAIR = Keypair(sys.argv[2])


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
    local_env = Environment('LOCAL', 'http://localhost:8008', PASSPHRASE, 'http://localhost:8001')

    # Create a client
    client = KinClient(local_env)
    print('Client created')

    initial_ledger_size = get_latest_ledger(client)['max_tx_set_size']
    try:
        # Set ledger tx size to 3
        # TODO: change to py-invoke
        requests.get('http://localhost:11626/upgrades?mode=set&maxtxsize=3&upgradetime=2018-10-15T18:34:00Z')
        requests.get('http://localhost:11627/upgrades?mode=set&maxtxsize=3&upgradetime=2018-10-15T18:34:00Z')

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

        accounts = [Keypair() for _ in range(5)]
        builder = Builder('LOCAL', client.horizon, fee=minimum_fee, secret=root_account.keypair.secret_seed)
        for keypair in accounts:
            builder.append_create_account_op(keypair.public_address, '100')

        builder.get_sequence()
        builder.sign()
        builder.submit()

        print('Created 5 accounts')

        txs = []
        for account in accounts:
            builder = Builder('LOCAL', client.horizon, fee=minimum_fee, secret=account.secret_seed)
            builder.append_manage_data_op('test', 'test'.encode())
            builder.get_sequence()
            builder.sign()
            txs.append(builder)

        for tx in txs[2:]:
            tx.sign(test_account.secret_seed)

        print('Whitelisted 3 transactions')

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

        # First ledger should have 2 whitelisted txs, and 1 non-whitelisted
        whitelisted_amount = sum(1 for tx in first_ledger_txs if len(tx['signatures']) == 2)
        assert whitelisted_amount == 2

        regular_amount = sum(1 for tx in first_ledger_txs if len(tx['signatures']) == 1)
        assert regular_amount == 1

        # # Second ledger should have 1 whitelisted tx, and 1 non-whitelisted
        whitelisted_amount = sum(1 for tx in second_ledger_txs if len(tx['signatures']) == 2)
        assert whitelisted_amount == 1

        regular_amount = sum(1 for tx in second_ledger_txs if len(tx['signatures']) == 1)
        assert regular_amount == 1

    except:
        raise
    finally:
        # Set tx size to what it was before
        # TODO: change to py-invoke
        requests.get(f'http://localhost:11626/upgrades?mode=set&maxtxsize={initial_ledger_size}&upgradetime=2018-10-15T18:34:00Z')
        requests.get(f'http://localhost:11627/upgrades?mode=set&maxtxsize={initial_ledger_size}&upgradetime=2018-10-15T18:34:00Z')

if __name__ == '__main__':
    asyncio.run(main())
