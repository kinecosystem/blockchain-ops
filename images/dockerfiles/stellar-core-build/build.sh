#!/usr/bin/env bash
set -e
set -x

cd /stellar-core

export C=gcc-6 CFLAGS="-O2 -g1"
export CXX=g++-6 CXXFLAGS="-w -O2 -g1"

./autogen.sh

# sdfprefs equals -fcolor-diagnostics and --enable-silent-rules
./configure --enable-sdfprefs

# build
make -j $(nproc)

# test
# export ALL_VERSIONS=1
# make check
