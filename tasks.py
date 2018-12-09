"""Call various Terraform actions."""
import json
import os
import os.path
from datetime import datetime, timezone
from hashlib import sha256
from time import sleep

import requests
from invoke import task

from kin import Keypair, KinClient, Environment as KinEnvironment
from kin.blockchain.builder import Builder
import kin_base


GLIDE_ARCH = 'linux-amd64'


@task
def glide(c, arch=GLIDE_ARCH, version='v0.13.2'):
    """Dowload glide."""
    print('Downloading glide')

    # avoid redownloading file if exists
    if os.path.isfile('{cwd}/glide'.format(cwd=c.cwd)):
        print('Glide exists')
        return

    c.run('curl -sSLo glide.tar.gz https://github.com/Masterminds/glide/releases/download/{version}/glide-{version}-{arch}.tar.gz'.format(
        version=version, arch=arch), hide='stdout')
    c.run('tar -zxf ./glide.tar.gz', hide='stdout')
    c.run('mv ./{arch}/glide ./glide'.format(arch=arch), hide='stdout')
    c.run('rm -rf ./{arch} ./glide.tar.gz'.format(arch=arch), hide='stdout')

    print('Glide downloaded')


@task
def vendor(c, arch='linux-amd64',):
    """Vendor go dependencies."""
    glide(c, arch)

    print('Vendoring dependencies')
    c.run('./glide install', hide='stderr')


def is_image_exists(c, name):
    res = c.run('sudo docker images', hide='stdout')
    for image in res.stdout.split('\n'):
        if name in image:
            print('Image {name} exists'.format(name=name))
            return True

    print('Image {name} doesn\'t exist'.format(name=name))
    return False


@task
def build_core(c, version='kinecosystem/master'):
    """Build Core binary docker image."""
    with c.cd('images'):
        if is_image_exists(c, 'images_stellar-core'):
            return

        if not os.path.isdir('./images/volumes/stellar-core-git'):
            print('Core git repository doesn\'t exist, cloning')
            c.run('git clone --branch kinecosystem/master https://github.com/kinecosystem/stellar-core.git volumes/stellar-core-git')

        print('Building core')
        c.run('sudo docker-compose build stellar-core-build')
        c.run('sudo docker-compose run stellar-core-build')
        c.run('sudo docker-compose build stellar-core')


@task
def build_horizon(c, version='kinecosystem/master'):
    """Build Horizon binary docker image."""
    with c.cd('images'):
        if is_image_exists(c, 'images_horizon'):
            return

        if not os.path.isdir('./images/volumes/go-git'):
            print('Go (Horizon) Core git repository doesn\'t exist, cloning')
            c.run('git clone --branch kinecosystem/master https://github.com/kinecosystem/go.git volumes/go-git')

        with c.cd('volumes/go-git'):
            vendor(c, arch='linux-amd64')

        cmd = ' '.join([
            'bash', '-c',
            ('"go build -ldflags=\''
             '-X \\"github.com/kinecosystem/go/support/app.buildTime={timestamp}\\"'
             ' '
             '-X \\"github.com/kinecosystem/go/support/app.version={version}\\"'
             ' \''
             ).format(timestamp=datetime.now(timezone.utc).isoformat(), version=version),
            '-o', './horizon', './services/horizon"',
        ])

        print('Building Horizon')
        c.run('sudo docker-compose run horizon-build {cmd}'.format(cmd=cmd))
        c.run('sudo docker-compose build horizon')


@task
def rm_network(c):
    """Destroy local test network."""
    print('Stopping local test network and removing containers')
    with c.cd('images'):
        c.run('sudo docker-compose down -v', hide='stderr')

        c.run('sudo rm -rf volumes/stellar-core/opt/stellar-core/buckets')
        c.run('sudo rm -f volumes/stellar-core/opt/stellar-core/*.log')
        c.run('sudo rm -rf volumes/stellar-core/tmp')


def upgrade(param, ledger_param, value):
    while True:
        r = requests.get('http://localhost:11626/upgrades',
                         params={'mode': 'set', 'upgradetime': '1970-01-01T00:00:00Z', param: value})
        r.raise_for_status()

        r = requests.get('http://localhost:8000/ledgers?order=desc&limit=1',
                         params={'order': 'desc', 'limit': 1})
        r.raise_for_status()
        res = r.json()
        records = res['_embedded']['records']
        # NOTE records can be empty if called straight after network has started
        # since no ledgers have been added yet
        if records and int(records[0][ledger_param]) == value:
            break

        sleep(1)


@task
def base_reserve_0(_):
    """Set base reserve to 0, necessary for spam prevention tests."""
    print('Setting base reserve to 0')
    upgrade('basereserve', 'base_reserve_in_stroops', 0)


@task
def protocol_version_9(_):
    """Protocol is already at 9, but this fixes a bug which prevents manageData ops."""
    print('Setting protocol version to 9')
    upgrade('protocolversion', 'protocol_version', 9)


@task
def create_whitelist_account(_):
    """Create whitelist account for prioritizing transactions in tests."""
    print('Creating whitelist account')


    def root_account_seed(passphrase: str) -> str:
        """Return the root account seed based on the given network passphrase."""
        network_hash = sha256(passphrase.encode()).digest()
        return kin_base.Keypair.from_raw_seed(network_hash).seed().decode()


    env = KinEnvironment('LOCAL', 'http://localhost:8000', 'private testnet')
    root_client = KinClient(env)
    root_seed = root_account_seed('private testnet')
    builder = Builder(env.name, root_client.horizon, 100, root_seed)

    builder.append_create_account_op('GBR7K7S6N6C2A4I4URBXM43W7IIOK6ZZD5SAGC7LBRCUCDMICTYMK4LO', str(100e5))
    builder.sign()
    builder.submit()


@task(pre=[build_core, build_horizon, rm_network],
      post=[base_reserve_0, protocol_version_9, create_whitelist_account])
def network(c):
    """Initialize a new local test network with single core and horizon instances."""
    print('Launching local network')
    with c.cd('images'):
        print('Starting Core database')
        c.run('sudo docker-compose up -d stellar-core-db', hide='stderr')
        sleep(2)

        # setup core database
        # https://www.stellar.org/developers/stellar-core/software/commands.html
        print('Initializing Core database')
        res = c.run('sudo docker-compose run stellar-core --newdb --forcescp', hide='both')

        # fetch root account seed
        for line in res.stdout.split('\n'):
            if 'Root account seed' in line:
                root_account_seed = line.strip().split()[7]
                break

        print('Root account seed: {}'.format(root_account_seed))

        # setup cache history archive
        print('Initializing Core history archive')
        c.run('sudo docker-compose run stellar-core --newhist cache', hide='both')

        # start a local private testnet core
        # https://www.stellar.org/developers/stellar-core/software/testnet.html
        print('Starting Core')
        c.run('sudo docker-compose up -d stellar-core', hide='stderr')

        # setup horizon database
        print('Starting Horizon database')
        c.run('sudo docker-compose up -d horizon-db', hide='stderr')
        sleep(2)
        print('Initializing Horizon database')
        c.run('sudo docker-compose run horizon db init', hide='stderr')

        # start horizon
        # envsubst leaves windows carriage return "^M" artifacts when called by docker
        # this fixes it
        print('Starting Horizon')
        c.run('ROOT_ACCOUNT_SEED="{root_account_seed}" sudo -E docker-compose up -d horizon'.format(
            root_account_seed=root_account_seed), hide='stderr')

    print('Network is up')
