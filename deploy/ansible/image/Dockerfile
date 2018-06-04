# image for testing against playbooks

# systemd is required for simulating a "real" ubuntu 16.04 instance with running services
# ssh is required for ansible to connect to the docker container,
# which represents a remote instance
#
# this image is based on the following one:
# https://github.com/solita/docker-systemd
FROM solita/ubuntu-systemd-ssh:16.04

# sudo without password
RUN apt-get -qq update && apt-get -qq install sudo && rm -rf /var/lib/apt/lists/*
COPY etc/sudoers /etc/sudoers
RUN visudo -qcf /etc/sudoers
RUN useradd -ms /bin/bash ubuntu && usermod -aG sudo ubuntu

# allow ssh connections dummy ansible key
COPY home/ubuntu/.ssh/authorized_keys /home/ubuntu/.ssh/authorized_keys

# ansible requires python installed
RUN apt-get -qq update && apt-get -qq install python3 && rm -rf /var/lib/apt/lists/*

# enable docker
RUN apt-get -qq update && apt-get -qq install curl && rm -rf /var/lib/apt/lists/*
RUN apt-get -qq update \
    && curl -sSo docker.deb https://download.docker.com/linux/ubuntu/dists/xenial/pool/stable/amd64/docker-ce_18.03.1~ce-0~ubuntu_amd64.deb \
    && apt -yqq install ./docker.deb \
    && rm -f docker.deb \
    && rm -rf /var/lib/apt/lists/*

VOLUME ["/var/run/docker.sock"]
