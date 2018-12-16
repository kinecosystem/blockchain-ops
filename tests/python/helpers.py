import asyncio
import logging
import math
from hashlib import sha256
from typing import List

import aiohttp

from kin import Keypair, KinClient
from kin.blockchain.builder import Builder
from kin_base import Keypair as BaseKeypair

NETWORK_NAME = 'LOCAL'
MIN_FEE = 100
MAX_OPS = 100
TX_SET_SIZE = 500


def root_account_seed(passphrase: str) -> str:
    """Return the root account seed based on the given network passphrase."""
    network_hash = sha256(passphrase.encode()).digest()
    return BaseKeypair.from_raw_seed(network_hash).seed().decode()


def derive_root_account(passphrase):
    """Return the keypair of the root account, based on the network passphrase."""
    network_hash = sha256(passphrase.encode()).digest()
    seed = BaseKeypair.from_raw_seed(network_hash).seed().decode()
    return Keypair(seed)


async def create_accounts(source: Builder, accounts_num, starting_balance):
    """Asynchronously create accounts and return a Keypair instance for each created account."""
    logging.info('creating %d accounts', accounts_num)

    # generate txs, squeezing as much "create account" ops as possible to each one.
    # when each tx is full with as much ops as it can include, sign and generate
    # that tx's XDR.
    # then, continue creating accounts using a new tx, and so on.
    # we stop when we create all ops required according to given accounts_num.
    kps = [Keypair() for _ in range(accounts_num)]
    xdrs = []
    batch_amount = (len(kps)+1) // (MAX_OPS+1)
    for batch_index in range(batch_amount):
        start = batch_index * MAX_OPS
        end = min(batch_index+1)*MAX_OPS, len(kps)

        batch_kps = kps[start:end]
        for kp in batch_kps:
            source.append_create_account_op(source=source.addres(),
                                            destination=kp.public_address,
                                            starting_balance=str(starting_balance))

        # sign with channel and root account
        source.sign(secret=source.keypair.seed().decode())
        xdrs.append(source.gen_xdr())

        # clean source builder for next transaction
        source.next()

    await send_txs(source.horizon.horizon_uri, xdrs, expected_statuses=[200])

    logging.info('created %d accounts', accounts_num)
    return kps


def generate_builders(kps: List[Keypair], env_name, horizon) -> List[Builder]:
    """Receive Keypair list and return Builder list with updated sequence numbers."""
    # fetch sequence numbers asynchronously for all created accounts
    sequences = await get_sequences(horizon, [kp.public_address for kp in kps])

    # create tx builders with up-to-date sequence number
    builders = []
    for i, kp in enumerate(kps):
        builder = Builder(env_name, horizon, MIN_FEE, kp.secret_seed)
        builder.sequence = sequences[i]
        builders.append(builder)

    for b in builders:
        logging.debug('created builder %s', b.address)

    return builders


def init_tx_builders(env, kps, sequences):
    """Initialize transaction builders for each given seed."""
    builders = []
    for i, kp in enumerate(kps):
        client = KinClient(env)
        builder = Builder(env.name, client.horizon, MIN_FEE, kp.secret_seed)
        builder.sequence = sequences[i]
        builders.append(builder)
    return builders


async def get(session: aiohttp.ClientSession, url, expected_status=200):
    """Send an HTTP GET request and return response JSON data.

    Fail if response isn't expected status code or format other than JSON.
    """
    async with session.get(url) as res:
        res_data = await res.json()

        if res.status != expected_status:
            logging.error('Error in HTTP GET request to %s: %s', url, res_data)
            raise RuntimeError('Error in HTTP GET request to {}'.format(url))

    return res_data


async def post(session: aiohttp.ClientSession, url, req_data, expected_statuses):
    """Send an HTTP POST request with given data and return response JSON data.

    Fail if response isn't expected status code or format other than JSON.

    NOTE expected status is either OK 200 or Server Timeout 504 if the transaction
    wasn't added to the next three ledgers.
    """
    async with session.post(url, data=req_data) as res:
        res_data = await res.json()

        if res.status not in expected_statuses:
            logging.error('Error in HTTP POST request to %s with data %s: %s', url, req_data, res_data)
            raise RuntimeError('Error in HTTP POST request to {}'.format(url))

    return res_data


class LoggingClientSession(aiohttp.ClientSession):
    """aiohttp client session that logs requests."""

    async def _request(self, method, url, **kwargs):
        logging.debug('Starting request <%s %r>', method, url)
        return await super()._request(method, url, **kwargs)


async def send_txs(endpoint, xdrs, expected_statuses=[200, 504]):
    """Send multiple async transaction XDRs to given endpoint."""
    logging.info('sending %d transactions', len(xdrs))

    async with LoggingClientSession(connector=aiohttp.TCPConnector(limit=5000)) as session:
        url = '{}/transactions'.format(endpoint)
        results = await asyncio.gather(*[post(session, url, {'tx': xdr.decode()}, expected_statuses) for xdr in xdrs])

    logging.info('%d transactions sent', len(xdrs))
    return results


async def get_sequences(endpoint, addresses):
    """Get sequence for multiple accounts."""
    logging.info('getting sequence for %d accounts', len(addresses))

    async with LoggingClientSession() as session:
        url = '{}/accounts'.format(endpoint)
        results = await asyncio.gather(*[get(session, '{}/{}'.format(url, address)) for address in addresses])

    logging.info('finished getting sequence for %d accounts', len(addresses))

    sequences = [int(r['sequence']) for r in results]
    return sequences


def get_latest_ledger(client):
    params = {'order': 'desc', 'limit': 1}
    return client.horizon.ledgers(params=params)['_embedded']['records'][0]


def add_prioritizers(builder: Builder, kps: List[Keypair]):
    """Add given addresses to whitelist account, making them transaction prioritizers."""
    logging.info('adding %d prioritizers', len(kps))

    for batch_index in range(max(1, math.ceil(len(kps)/MAX_OPS))):
        start = batch_index*MAX_OPS
        end = min((batch_index+1)*MAX_OPS,
                  len(kps))

        for i, kp in enumerate(kps[start:end], start=1):
            logging.debug('adding manage data op #%d', i)
            builder.append_manage_data_op(kp.public_address, kp._hint)

        builder.sign()

        logging.debug('submitting transaction with %d manage data ops', end-start)
        builder.submit()
        logging.debug('done')

        builder.clear()

    logging.info('%d prioritizers added', len(kps))


# TODO
# def remove_whitelisters(builder: Builder, kps: List[kin_base.Keypair]): pass
