import asyncio
from hashlib import sha256

from kin import Keypair
from kin_base import Keypair as BaseKeypair

from concurrent.futures import ThreadPoolExecutor


def derive_root_account(passphrase):
    """Return the keypair of the root account, based on the network passphrase"""
    network_hash = sha256(passphrase.encode()).digest()
    seed = BaseKeypair.from_raw_seed(network_hash).seed().decode()
    return Keypair(seed)


async def send_txs(txs):
    with ThreadPoolExecutor(max_workers=len(txs)) as executor:
        loop = asyncio.get_running_loop()
        promises = [loop.run_in_executor(executor, tx.submit) for tx in txs]

        for _ in await asyncio.gather(*promises):
            return promises


def get_latest_ledger(client):
    params = {'order': 'desc', 'limit': 1}
    return client.horizon.ledgers(params=params)['_embedded']['records'][0]
