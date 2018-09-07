#!/usr/bin/env bash
# build kinecosystem/horizon

set -x
set -e

BUILD_TIME=$(date -u --rfc-3339=seconds | sed 's/ /T/')
HORIZON_VERSION="kinecosystem/horizon-v0.12.3-immediate-preamble"

sudo docker run \
    -v $GOPATH/src/github.com/kinecosystem/go:/go/src/github.com/kinecosystem/go \
    kinecosystem/horizon-build \
    bash -c "go build -ldflags='-X \"github.com/kinecosystem/go/support/app.buildTime=$BUILD_TIME\" -X \"github.com/kinecosystem/go/support/app.version=${HORIZON_VERSION}\"' -o ./horizon ./services/horizon"
