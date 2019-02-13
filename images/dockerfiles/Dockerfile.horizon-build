# image used to build kinecosystem/horizon
# kinecosystem/go repo should be mounted into a container,
# then you can execute the build

FROM golang:1.11-stretch

RUN BUILD_DEPS="build-essential git mercurial postgresql-client mysql-client"; \
    apt-get -qq update && apt-get -qq install $BUILD_DEPS

RUN curl -sS https://raw.githubusercontent.com/golang/dep/master/install.sh | sh

RUN mkdir -p /go/src/github.com/kinecosystem/go
WORKDIR "/go/src/github.com/kinecosystem/go"
VOLUME ["/go/src/github.com/kinecosystem/go"]
