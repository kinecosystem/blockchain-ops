import asyncio
import logging
import math
from hashlib import sha256
from typing import List

import aiohttp

from kin import Keypair, Environment
from kin.blockchain.horizon import Horizon
from kin.blockchain.builder import Builder
from kin.config import SDK_USER_AGENT
from kin_base import Keypair as BaseKeypair

import kin
import kin_base

NETWORK_NAME = 'LOCAL'
MIN_FEE = 100
MAX_OPS = 100
TX_SET_SIZE = 500


def root_account_seed(passphrase: str) -> str:
    """Return the root account seed based on the given network passphrase."""
    network_hash = sha256(passphrase.encode()).digest()
    return kin_base.Keypair.from_raw_seed(network_hash).seed().decode()


def derive_root_account(passphrase):
    """Return the keypair of the root account, based on the network passphrase."""
    network_hash = sha256(passphrase.encode()).digest()
    seed = BaseKeypair.from_raw_seed(network_hash).seed().decode()
    return Keypair(seed)


async def create_accounts(env: Environment, channels: List[Builder], root_account: BaseKeypair, starting_balance, horizon_addresses: List[str] = []):
    """Asynchronously create accounts and return a transaction Builder instance for each account.

    The amount of accounts to create is determined by how many channels are given
    and the maximum operatinos allowed in transaction e.g. 10 channels with 100 max ops
    would cause 10*100=1000 accounts to be created.

    In addition, each Builder instance uses a different Horizon endpoint if given a non-empty list.
    """
    accounts_to_create_num = len(channels) * MAX_OPS
    logging.info('creating %d accounts', accounts_to_create_num)

    accounts_to_create = [Keypair() for _ in range(accounts_to_create_num)]
    xdrs = []
    for i, channel in enumerate(channels):
        for kp in accounts_to_create[i*MAX_OPS : i*(MAX_OPS) + MAX_OPS]:
            # use the root account as the source of the operations
            #
            # NOTE channels need a starting balance since they need to pay fees because they are not prioritized
            channel.append_create_account_op(source=root_account.address(),
                                             destination=kp.public_address,
                                             starting_balance=str(starting_balance))

        # sign with channel and root account
        channel.sign(secret=channel.keypair.seed().decode())
        if root_account.seed().decode() != channel.keypair.seed().decode():
            channel.sign(secret=root_account.seed().decode())
        xdrs.append(channel.gen_xdr())

        channel.next()

    horizon_uri = channels[0].horizon.horizon_uri
    await send_txs(horizon_uri, xdrs, expected_statuses=[200])

    # fetch sequence numbers asynchronously for all created accounts
    sequences = await get_sequences(horizon_uri, [a.public_address for a in accounts_to_create])

    # create tx builders with up-to-date sequence number
    builders = []
    horizons = ([Horizon(horizon_uri=addr, user_agent=SDK_USER_AGENT) for addr in horizon_addresses]
                if horizon_addresses
                else [horizon_uri])
    for i, kp in enumerate(accounts_to_create):
        # deterministically pick horizon endpoint from all available endpoint
        # according to keypair index in account list
        horizon = horizons[i % len(horizons)]
        builder = Builder(env.name, horizon, MIN_FEE, kp.secret_seed)
        builder.sequence = sequences[i]
        builders.append(builder)

    for b in builders:
        logging.debug('created builder %s', b.address)

    return builders


def init_tx_builders(env, kps, sequences):
    """Initialize transaction builders for each given seed."""
    builders = []
    for i, kp in enumerate(kps):
        client = kin.KinClient(env)
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
