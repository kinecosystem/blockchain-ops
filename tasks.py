"""Call various Terraform actions."""
import os
import os.path
from datetime import datetime, timezone
from hashlib import sha256
from time import sleep
import platform

import requests
from invoke import task, call
from invoke.exceptions import Exit, Failure

from kin import KinClient, Environment as KinEnvironment
from kin.blockchain.builder import Builder
import kin_base


@task
def glide(c, version='v0.13.2'):
    """Download glide."""
    print('Downloading glide')

    # find glide version, copied from glide installation script
    os_name = platform.system().lower()
    if os_name == 'linux':
        arch = 'linux-amd64'
    elif os_name == 'darwin':
        arch = 'darwin-amd64'
    else:
        raise Failure(os_name_res, reason='Only supported on OSx and Linux')
    print('Glide arch: {arch}'.format(arch=arch))

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
def vendor(c):
    """Vendor go dependencies."""
    glide(c)

    print('Vendoring dependencies')
    if not os.path.isdir('{}/vendor'.format(c.cwd)):
        c.run('./glide install', hide='stderr')


def is_image_exists(c, name):
    """Return true if given Docker image exists."""
    res = c.run('sudo docker images', hide='stdout')
    for image in res.stdout.split('\n'):
        if name == image.split(' ')[0]:
            print('Image {name} exists'.format(name=name))
            return True

    print('Image {name} doesn\'t exist'.format(name=name))
    return False


def is_git_dir_modified(c):
    """Return True if the given git repo directory is unmodified."""
    res = c.run('git status --porcelain', hide='both')
    for line in res.stdout:
        if line.startswith(' M '):
            print('Git directory {} is modified'.format(c.cwd))
            return True

    print('Git directory {} is unmodified'.format(c.cwd))
    return False


def git_dir_checkout_branch(c, branch):
    """Checkout a specific branch for given repo directory."""
    print('Checking out kinecosystem/master')
    c.run('git checkout {}'.format(branch))


def init_git_repo(c, git_url, dir_name, branch='kinecosystem/master'):
    """Make sure git repo directory is available before building."""
    # clone git repo if it doesn't exist,
    # otherwise checkout kinecosystem/master branch
    if not os.path.isdir('{}/{}/volumes/{}'.format(os.getcwd(), c.cwd, dir_name)):
        print('Core git repository doesn\'t exist, cloning')
        c.run('git clone --branch {branch} {git_url} volumes/{dir_name}'.format(branch=branch, git_url=git_url, dir_name=dir_name))
    else:
        with c.cd('volumes/{}'.format(dir_name)):
            if is_git_dir_modified(c):
                raise Exit('Stopping, please clean changes and retry')

            git_dir_checkout_branch(c, branch)


@task
def build_core(c, version, branch='kinecosystem/master', production=True):
    """Build Core binary docker image.

    By default, builds a Docker image tagged ready for production.

    When production is disabled, it builds using docker-compose without properly tagging,
    mainly used for local network tests.
    """
    with c.cd('images'):
        # we always rebuild production images,
        # but we don't for non-production (e.g. local test network)
        #
        # NOTE docker compose doesn't have a way of knowing if an image was already
        # built, so we search for it manually
        if not production and is_image_exists(c, 'images_stellar-core'):
            return

        init_git_repo(c, 'https://github.com/kinecosystem/stellar-core.git', 'stellar-core-git', branch)

        print('Building core')

        if production:
            c.run('sudo docker build '
                  '-f dockerfiles/Dockerfile.stellar-core-build '
                  '-t kinecosystem/stellar-core-build '
                  '.')

            c.run('sudo docker run --rm '
                  '-v {}/{}/volumes/stellar-core-git:/stellar-core '
                  'kinecosystem/stellar-core-build'.format(os.getcwd(), c.cwd))

            c.run('sudo docker build '
                  '-f dockerfiles/Dockerfile.stellar-core '
                  '-t kinecosystem/stellar-core:latest '
                  '-t kinecosystem/stellar-core:{version} '
                  '.'.format(version=version))
        else:
            c.run('sudo docker-compose build stellar-core-build')
            c.run('sudo docker-compose run stellar-core-build')
            c.run('sudo docker-compose build stellar-core')


@task
def build_horizon(c, version, branch='kinecosystem/master', production=True):
    """Build Horizon binary docker image.

    By default, builds a Docker image tagged ready for production.

    When production is disabled, it builds using docker-compose without properly tagging,
    mainly used for local network tests.
    """
    with c.cd('images'):
        # we always rebuild production images,
        # but we don't for non-production (e.g. local test network)
        #
        # NOTE docker compose doesn't have a way of knowing if an image was already
        # built, so we search for it manually
        if not production and is_image_exists(c, 'images_horizon'):
            return

        init_git_repo(c, 'https://github.com/kinecosystem/go.git', 'go-git', branch)

        with c.cd('volumes/go-git'):
            vendor(c)

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

        if production:
            # build
            c.run('sudo docker build '
                  '-f dockerfiles/Dockerfile.horizon-build '
                  '-t kinecosystem/horizon-build '
                  '.')

            c.run('sudo docker run '
                  '--rm '
                  '-v {}/{}/volumes/go-git:/go/src/github.com/kinecosystem/go kinecosystem/horizon-build '
                  '{}'.format(os.getcwd(), c.cwd, cmd))

            c.run('sudo docker build '
                  '-f dockerfiles/Dockerfile.horizon '
                  '-t kinecosystem/horizon:latest '
                  '-t kinecosystem/horizon:{version} '
                  '.'.format(version=version))
        else:
            # build using docker compose for local test network
            c.run('sudo docker-compose run horizon-build {cmd}'.format(cmd=cmd))
            c.run('sudo docker-compose build horizon')


@task
def push_dockerhub(c, app, version, latest=True):
    """Push image to Dockerhub."""
    if app.lower() == 'core':
        c.run('sudo docker push kinecosystem/stellar-core:{version}'.format(version=version))
        if latest:
            c.run('sudo docker push kinecosystem/stellar-core:latest')
    elif app.lower() == 'horizon':
        c.run('sudo docker push kinecosystem/horizon:{version}'.format(version=version))
        if latest:
            c.run('sudo docker push kinecosystem/horizon:latest')
    else:
        Exit('Unknown application {}'.format(app))


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
    """Apply Core network parameter upgrade."""
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


def base_reserve_0():
    """Set base reserve to 0, necessary for spam prevention tests."""
    print('Setting base reserve to 0')
    upgrade('basereserve', 'base_reserve_in_stroops', 0)


def protocol_version_9():
    """Protocol is already at 9, but this fixes a bug which prevents manageData ops."""
    print('Setting protocol version to 9')
    upgrade('protocolversion', 'protocol_version', 9)


def derive_root_account_seed(passphrase):
    """Return the root account seed based on the given network passphrase."""
    network_hash = sha256(passphrase.encode()).digest()
    return kin_base.Keypair.from_raw_seed(network_hash).seed().decode()


@task
def root_account_seed(_, passphrase):
    """Print root account seed according to given network passphrase."""
    print(derive_root_account_seed(passphrase))


@task
def address_from_seed(_, seed):
    """Print account address according to given seed."""
    print(kin_base.Keypair.from_seed(seed).address().decode())


def create_whitelist_account():
    """Create whitelist account for prioritizing transactions in tests."""
    print('Creating whitelist account')

    env = KinEnvironment('LOCAL', 'http://localhost:8000', 'private testnet')
    root_client = KinClient(env)
    root_seed = derive_root_account_seed('private testnet')
    builder = Builder(env.name, root_client.horizon, 100, root_seed)

    builder.append_create_account_op('GBR7K7S6N6C2A4I4URBXM43W7IIOK6ZZD5SAGC7LBRCUCDMICTYMK4LO', str(100e5))
    builder.sign()
    builder.submit()


@task(pre=[call(build_core, version='kinecosystem/master', production=False)])
def start_core(c):
    """Start a local test Core instance."""
    with c.cd('images'):
        print('Starting Core database')
        c.run('sudo docker-compose up -d stellar-core-db', hide='stderr')
        sleep(2)

        # setup core database
        # https://www.stellar.org/developers/stellar-core/software/commands.html
        print('Initializing Core database')
        c.run('sudo docker-compose run stellar-core --newdb --forcescp', hide='both')

        # setup cache history archive
        print('Initializing Core history archive')
        c.run('sudo docker-compose run stellar-core --newhist cache', hide='both')

        # start a local private testnet core
        # https://www.stellar.org/developers/stellar-core/software/testnet.html
        print('Starting Core')
        c.run('sudo docker-compose up -d stellar-core', hide='stderr')


@task(pre=[call(build_horizon, version='kinecosystem/master', production=False)])
def start_horizon(c):
    """Start a local test Horizon instance."""
    with c.cd('images'):
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
            root_account_seed=derive_root_account_seed('private testnet')), hide='stderr')


@task(rm_network, start_core, start_horizon)
def network(_):
    """Initialize a new local test network with single core and horizon instances."""
    base_reserve_0()
    protocol_version_9()
    create_whitelist_account()

    print('Root account seed: {}'.format(derive_root_account_seed('private testnet')))
    print('Network is up')
