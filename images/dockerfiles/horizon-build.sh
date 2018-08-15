#!/usr/bin/env bash
# build kinecosystem/horizon

set -x
set -e

BUILD_TIME=$(date -u --rfc-3339=seconds | sed 's/ /T/')

sudo docker run \
    -v $GOPATH/src/github.com/kinecosystem/go:/go/src/github.com/kinecosystem/go \
    kinecosystem/horizon-build \
    bash -c "go build -ldflags='-X \"github.com/kinecosystem/go/support/app.buildTime=$BUILD_TIME\" -X \"github.com/kinecosystem/go/support/app.version=kinecosystem/horizon-v0.12.3-psql-optimization\"' -o ./horizon ./services/horizon"
