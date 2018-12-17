import asyncio
import concurrent.futures
import logging
import multiprocessing
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


# XXX concurrent.futures behavior: why can't this function be a local function in generate_keypairs()?
def keypair_list(n):
    return [Keypair() for _ in range(n)]


async def generate_keypairs(n) -> List[Keypair]:
    """Generate Keypairs efficiently using all available CPUs."""
    logging.info('generating %d keypairs', n)

    # split amounts of keypairs to create to multiple inputs,
    # one for each cpu
    cpus = multiprocessing.cpu_count()
    d, m = n // cpus, n % cpus
    keypair_amounts = [d]*cpus + [m]*(1 if m else 0)

    # generate keypairs across multiple cpus
    loop = asyncio.get_running_loop()
    futurs = []  # futures
    with concurrent.futures.ProcessPoolExecutor() as pool:
        futurs = [loop.run_in_executor(pool, keypair_list, amount) for amount in keypair_amounts]

    # aggregate results
    kps = []
    for kp in futurs:
        kps.extend(await kp)

    logging.info('%d keypairs generated', n)
    return kps


async def create_accounts(source: Builder, horizon_endpoints, accounts_num, starting_balance):
    """Asynchronously create accounts and return a Keypair instance for each created account."""
    logging.info('creating %d accounts', accounts_num)

    # generate txs, squeezing as much "create account" ops as possible to each one.
    # when each tx is full with as much ops as it can include, sign and generate
    # that tx's XDR.
    # then, continue creating accounts using a new tx, and so on.
    # we stop when we create all ops required according to given accounts_num.
    def batch(iterable, n=1):
        l = len(iterable)
        for ndx in range(0, l, n):
            yield iterable[ndx:min(ndx + n, l)]

    kps = await generate_keypairs(accounts_num)
    xdrs = []
    for batch_kps in batch(kps, MAX_OPS):
        for kp in batch_kps:
            source.append_create_account_op(source=source.address,
                                            destination=kp.public_address,
                                            starting_balance=str(starting_balance))

        # sign with channel and root account
        source.sign(secret=source.keypair.seed().decode())
        xdrs.append(source.gen_xdr())

        # clean source builder for next transaction
        source.next()

    await send_txs_multiple_endpoints(horizon_endpoints, xdrs, expected_statuses=[200])

    logging.info('created %d accounts', accounts_num)
    return kps


def next_builder(b: Builder) -> Builder:
    """Reimplementation of kin.blockchain.Builder.next() that returns a new builder."""
    next_builder = Builder(network=b.network,
                           horizon=b.horizon,
                           fee=b.fee,
                           secret=b.keypair.seed().decode(),
                           address=b.address)

    next_builder.keypair = b.keypair
    next_builder.sequence = str(int(b.sequence)+1)

    return next_builder


async def generate_builders(kps: List[Keypair], env_name, horizon) -> List[Builder]:
    """Receive Keypair list and return Builder list with updated sequence numbers."""
    # fetch sequence numbers asynchronously for all created accounts
    sequences = await get_sequences_multiple_endpoints([horizon], [kp.public_address for kp in kps])

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
        try:
            res_data = await res.json()
        except aiohttp.client_exceptions.ContentTypeError as e:
            logging.error(e)
            logging.error(await res.text())

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


async def send_txs_multiple_endpoints(endpoints, xdrs, expected_statuses=[200, 504]):
    """Send multiple async transaction XDRs submitting to one of given endpoints.

    endpoints are iterated one after the other in a round robin manner.
    """
    logging.info('sending %d transactions', len(xdrs))

    async with LoggingClientSession(connector=aiohttp.TCPConnector(limit=5000)) as session:
        urls = ['{}/transactions'.format(e) for e in endpoints]
        results = []
        for i, xdr in enumerate(xdrs):
            # submit to one of the urls in a round robin manner
            results.append(post(session, urls[i % len(urls)], {'tx': xdr.decode()}, expected_statuses))

        results = await asyncio.gather(*results)

    logging.info('%d transactions sent', len(xdrs))
    return results


async def get_sequences_multiple_endpoints(endpoints, addresses):
    """Get sequence for multiple accounts, using one of given endpoints.

    endpoints are iterated one after the other in a round robin manner.
    """
    logging.info('getting sequence for %d accounts', len(addresses))

    async with LoggingClientSession() as session:
        urls = ['{}/accounts'.format(e) for e in endpoints]
        results = []
        for i, address in enumerate(addresses):
            # send request to one of the urls in a round robin manner
            results.append(get(session, '{}/{}'.format(urls[i % len(urls)], address)))

        results = await asyncio.gather(*results)

    logging.info('finished getting sequence for %d accounts', len(addresses))

    sequences = []
    for r in results:
        try:
            seq = int(r['sequence'])
        except KeyError:
            # can occur if request failed
            seq = 0
        sequences.append(seq)

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
