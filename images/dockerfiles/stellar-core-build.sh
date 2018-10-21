#!/usr/bin/env bash
# build kinecosystem/stellar-core

set -x
set -e

STELLAR_CORE_VERSION=$(cd $1 && git describe --tags HEAD)

sudo docker build \
    -f Dockerfile.stellar-core-build \
    -t kinecosystem/stellar-core-build \
    .

sudo docker run -v $1:/stellar-core kinecosystem/stellar-core-build $2

sudo docker build \
    -f Dockerfile.stellar-core-bin \
    -t kinecosystem/stellar-core:latest \
    -t kinecosystem/stellar-core:${STELLAR_CORE_VERSION} \
    .

sudo docker push kinecosystem/stellar-core:latest
sudo docker push kinecosystem/stellar-core:${STELLAR_CORE_VERSION}
