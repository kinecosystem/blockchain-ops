#!/usr/bin/env bash
# initialize a new local test network with single core + horizon instances
set -x
set -e

sudo docker-compose down -v

# setup core database
# https://www.stellar.org/developers/stellar-core/software/commands.html
sudo docker-compose up -d stellar-core-db
sudo docker-compose run stellar-core --newdb --forcescp

# start a local private testnet core
# https://www.stellar.org/developers/stellar-core/software/testnet.html
sudo docker-compose up -d stellar-core

# setup horizon database
sudo docker-compose up -d horizon-db
sudo docker-compose run horizon db init

# start horizon
sudo docker-compose up -d horizon
