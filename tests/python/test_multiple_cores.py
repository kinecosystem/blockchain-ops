"""Tests several actions with transactions on multiple kin-cores"""

import sys
import asyncio
import time

from kin import KinClient, Environment, Keypair, KinErrors
from kin.blockchain.builder import Builder
from helpers import derive_root_account, send_txs, get_latest_ledger

clients = []


def initialize():
    if len(sys.argv) < 4:
        print('invalid number of params :', len(clients))
        sys.exit(1)

    global PASSPHRASE
    global WHITELIST_MANAGER_KEYPAIR
    global root_account
    global tx_count

    PASSPHRASE = sys.argv[1]
    WHITELIST_MANAGER_KEYPAIR = Keypair(sys.argv[2])
    tx_count = int(sys.argv[3])

    for arg in sys.argv[4:]:
        local_env = Environment('LOCAL', arg, PASSPHRASE, 'http://localhost:8001')

        # Creates a client
        clients.append(KinClient(local_env))
        print('Client ', len(clients), ' created!')

    # Create the root account object
    root_account = clients[0].kin_account(derive_root_account(PASSPHRASE).secret_seed)
    print('Root account object created')


async def main():
    initialize()

    txs = []
    accounts = []

    minimum_fee = clients[0].get_minimum_fee()

    # Creating new test accounts
    accounts.append(Keypair())
    accounts.append(Keypair())
    accounts.append(Keypair())

    print('Creating new test accounts')
    root_account.create_account(accounts[0].public_address, 100000000, minimum_fee)
    root_account.create_account(accounts[1].public_address, 100000000, minimum_fee)
    assert clients[0].does_account_exists(accounts[1].public_address) and clients[0].does_account_exists(
        accounts[0].public_address)
    print('2 Test accounts created - Passed')

    for i in range(tx_count):
        # generating transactions using multiple kin-cores
        builder = Builder('LOCAL', clients[i % len(clients)].horizon, fee=minimum_fee,
                          secret=accounts[i % len(accounts)].secret_seed)
        builder.get_sequence()
        builder.append_manage_data_op('test' + str(i), 'test'.encode())
        builder.sign()
        txs.append(builder)

    # waiting for the txs receipts from different cores
    receipts = await send_txs(txs)

    assert len(receipts) == tx_count
    print('All of the transactions approved by different cores - Passed')

    assert len(set([(rec._result['ledger']) for rec in receipts])) == 1
    print('All of the transactions are in the same ledger - Passed')

    cores_hashes = [(rec._result['hash']) for rec in receipts]
    ledger_no = receipts[0]._result['ledger']

    # waiting for the next ledger
    while ledger_no + 1 > get_latest_ledger(clients[0])['sequence']:
        time.sleep(0.5)

    # getting ledger txs from horizon
    ledger_txs = clients[0].horizon.ledger_transactions(ledger_no)['_embedded']['records']

    # comparing ledger hashes with the core hashes
    assert set(cores_hashes) & set([t['hash'] for t in ledger_txs])
    print('Multi cores test - Passed')


if __name__ == '__main__':
    asyncio.run(main())
