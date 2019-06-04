FROM stellar/base:latest

# postgresql
EXPOSE 5432
# horizon
EXPOSE 8000
# core p2p
EXPOSE 11625
# core http / admin
EXPOSE 11626

ADD dependencies /
RUN ["chmod", "+x", "dependencies"]
RUN /dependencies

# copy the binaries from the local path
COPY ./stellar-core  /usr/local/bin/stellar-core
COPY ./horizon  /usr/local/bin/horizon

RUN ["apt-get", "install", "gettext-base"]
RUN ["mkdir", "-p", "/opt/stellar"]
RUN ["touch", "/opt/stellar/.docker-ephemeral"]

RUN useradd --uid 10011001 --home-dir /home/stellar --no-log-init stellar \
    && mkdir -p /home/stellar \
    && chown -R stellar:stellar /home/stellar

RUN ["ln", "-s", "/opt/stellar", "/stellar"]
RUN ["ln", "-s", "/opt/stellar/core/etc/stellar-core.cfg", "/stellar-core.cfg"]
RUN ["ln", "-s", "/opt/stellar/horizon/etc/horizon.env", "/horizon.env"]
ADD common /opt/stellar-default/common
ADD pubnet /opt/stellar-default/pubnet
ADD testnet /opt/stellar-default/testnet
ADD standalone /opt/stellar-default/standalone


ADD start /
RUN ["chmod", "+x", "start"]

ENTRYPOINT ["/init", "--", "/start" ]

# CUSTOM section

# install libc6, required for core (compiled on Ubuntu 18.04 with glibc6)
RUN echo "deb http://ftp.debian.org/debian sid main" >> /etc/apt/sources.list
RUN apt-get update -qq && apt-get -t sid install -qq rsync libc6
