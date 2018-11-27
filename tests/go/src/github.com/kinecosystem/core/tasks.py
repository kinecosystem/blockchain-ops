"""Call various Terraform actions."""
import os
import os.path
from time import sleep

from invoke import task


@task(help={'name': 'Dowload glide'})
def glide(c):
    GLIDE_VERSION = 'v0.13.2'
    GLIDE_ARCH = 'linux-amd64'

    # avoid redownloading file if exists
    if os.path.isfile('glide'):
        return

    c.run('curl -sSLo glide.tar.gz https://github.com/Masterminds/glide/releases/download/${glide_version}/glide-${glide_version}-${glide_arch}.tar.gz'.format(
        glide_version=GLIDE_VERSION, glide_arch=GLIDE_ARCH))
    c.run('tar -xf ./glide.tar.gz')
    c.run('mv ./${glide_arch}/glide ./glide'.format(glide_arch=GLIDE_ARCH))
    c.run('rm -rf ./${glide_arch} ./glide.tar.gz'.format(glide_arch=GLIDE_ARCH))


@task(glide)
def vendor(c):
    c.run('./glide install')


@task
def rm_network(c):
    with c.cd('images'):
        c.run('sudo docker-compose down -v', hide='stderr')

        c.run('sudo rm -rf volumes/stellar-core/opt/stellar-core/buckets')
        c.run('sudo rm -rf volumes/stellar-core/tmp')


@task(rm_network)
def network(c):
    """Initialize a new local test network with single core + horizon instances."""
    print('Launching local network')
    with c.cd('images'):
        c.run('sudo docker-compose up -d stellar-core-db', hide='stderr')
        sleep(2)

        # setup core database
        # https://www.stellar.org/developers/stellar-core/software/commands.html
        res = c.run('sudo docker-compose run stellar-core --newdb --forcescp', hide='both')

        # fetch root account seed
        for line in res.stdout.split('\n'):
            if 'Root account seed' in line:
                root_account_seed = line.strip().split()[7]
                break

        print('Root account seed: {}'.format(root_account_seed))

        # setup cache history archive
        c.run('sudo docker-compose run stellar-core --newhist cache', hide='both')

        # start a local private testnet core
        # https://www.stellar.org/developers/stellar-core/software/testnet.html
        c.run('sudo docker-compose up -d stellar-core', hide='stderr')

        # setup horizon database
        c.run('sudo docker-compose up -d horizon-db', hide='stderr')
        sleep(2)
        c.run('sudo docker-compose run horizon db init', hide='stderr')

        # start horizon
        # envsubst leaves windows carriage return "^M" artifacts when called by docker
        # this fixes it
        c.run('ROOT_ACCOUNT_SEED="{root_account_seed}" sudo -E docker-compose up -d horizon'.format(
            root_account_seed=root_account_seed), hide='stderr')

    print('Network ready')
