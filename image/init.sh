#!/usr/bin/env bash
# initialize a new local test network with single core + horizon instances
set -x
set -e

sudo docker-compose down -v

# setup core database
# https://www.stellar.org/developers/stellar-core/software/commands.html
#
# also, cache root account seed, used by friendbot later on
sudo docker-compose up -d stellar-core-db
sleep 2

ROOT_ACCOUNT_SEED=$(sudo docker-compose run stellar-core --newdb --forcescp \
    | grep "Root account seed" | cut -d ' ' -f 8)

echo Root account seed: $ROOT_ACCOUNT_SEED

# start a local private testnet core
# https://www.stellar.org/developers/stellar-core/software/testnet.html
sudo docker-compose up -d stellar-core

# setup horizon database
sudo docker-compose up -d horizon-db
sleep 2
sudo docker-compose run horizon db init

# start horizon
# envsubst leaves windows carriage return "^M" artifacts when called by docker
# this fixes it
ROOT_ACCOUNT_SEED="$ROOT_ACCOUNT_SEED" sudo -E docker-compose up -d horizon

# start friendbot
# currenty disabled for horizon v0.11.r1
# see docker-compose comment for more information
# ROOT_ACCOUNT_SEED="$ROOT_ACCOUNT_SEED" sudo -E docker-compose up -d friendbot
