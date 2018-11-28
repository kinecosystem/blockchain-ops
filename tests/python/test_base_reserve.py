"""Tests several actions with an account with 0 balance"""

import sys

from kin import KinClient, Environment, Keypair, KinErrors
from kin.blockchain.builder import Builder
from helpers import derive_root_account

PASSPHRASE = sys.argv[1]
WHITELIST_MANAGER_KEYPAIR = Keypair(sys.argv[2])


def main():
    # Create the environment
    local_env = Environment('LOCAL', 'http://localhost:8000', PASSPHRASE, 'http://localhost:8001')

    # Create a client
    client = KinClient(local_env)
    print('Client created')

    # Create the root account object
    root_account = client.kin_account(derive_root_account(PASSPHRASE).secret_seed)
    print('Root account object created')

    minimum_fee = client.get_minimum_fee()
    # Create an account with 0 base reserve
    test_account = Keypair()
    root_account.create_account(test_account.public_address, 0, minimum_fee)
    assert client.does_account_exists(test_account.public_address)
    print('Test account created')

    # Send a tx that does not require spending kin
    builder = Builder('LOCAL', client.horizon, fee=0, secret=test_account.secret_seed)
    builder.get_sequence()
    builder.append_manage_data_op('test', 'test'.encode())
    builder.sign()

    try:
        builder.submit()
    except KinErrors.HorizonError as e:
        # Tx should fail since the fee is under minimum fee
        assert e.extras.result_codes.transaction == KinErrors.TransactionResultCode.INSUFFICIENT_FEE
        print('Sending under minimum fee - Passed')

    builder = Builder('LOCAL', client.horizon, fee=minimum_fee, secret=test_account.secret_seed)
    builder.get_sequence()
    builder.append_manage_data_op('test', 'test'.encode())
    builder.sign()

    try:
        builder.submit()
    except KinErrors.HorizonError as e:
        # Tx should fail since the account cant pay the fee
        assert e.extras.result_codes.transaction == KinErrors.TransactionResultCode.INSUFFICIENT_BALANCE
        print('Sending with no fee to pay - Passed')

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

    # test_account is now a whitelister, so the fee should be ignored
    builder = Builder('LOCAL', client.horizon, fee=0, secret=test_account.secret_seed)
    builder.get_sequence()
    builder.append_manage_data_op('test2', 'test2'.encode())
    builder.sign()
    builder.submit()

    print('Sending prioritized tx under minimum fee - Passed')

    builder = Builder('LOCAL', client.horizon, fee=999999, secret=test_account.secret_seed)
    builder.get_sequence()
    builder.append_manage_data_op('test3', 'test3'.encode())
    builder.sign()
    builder.submit()

    print('Sending prioritized tx with fee > balance - Passed')

    # Try the same if the account is not a whitelister, but the tx is whitelisted
    test_account2 = Keypair()
    root_account.create_account(test_account2.public_address, 0, minimum_fee)

    builder = Builder('LOCAL', client.horizon, fee=999999, secret=test_account2.secret_seed)
    builder.get_sequence()
    builder.append_manage_data_op('test', 'test'.encode())
    builder.sign()
    # sign with the whitelister as well to prioritize the tx
    builder.sign(secret=test_account.secret_seed)
    builder.submit()

    print('Sending prioritized tx2 with fee > balance - Passed')


if __name__ == '__main__':
    main()
