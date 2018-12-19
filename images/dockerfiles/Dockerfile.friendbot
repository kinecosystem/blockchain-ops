FROM ubuntu:16.04

ENV FRIENDBOT_SEED = \
    PORT = "8000" \
    NETWORK_PASSPHRASE = "private testnet" \
    HORIZON_ADDRESS = "http://horizon:8000" \
    STARTING_BALANCE = "10.00"

RUN apt-get -qq update && apt-get -qq install gettext

RUN mkdir -p /opt/friendbot
WORKDIR /opt/friendbot
VOLUME ["/opt/friendbot"]
EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/friendbot"]

COPY ./volumes/go-git/friendbot /usr/local/bin/
