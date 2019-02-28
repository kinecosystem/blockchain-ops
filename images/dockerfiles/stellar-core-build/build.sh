#!/usr/bin/env bash
set -e
set -x

cd /stellar-core

export C=gcc-6 CFLAGS="-O2 -g1"
export CXX=g++-6 CXXFLAGS="-w -O2 -g1"

./autogen.sh

./configure --enable-asan --enable-extrachecks --enable-sdfprefs

# make format

# build
make -j $(nproc)

# test
# export ALL_VERSIONS=1
# make check
