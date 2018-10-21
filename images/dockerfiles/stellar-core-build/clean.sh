#!/usr/bin/env bash
set -e
set -x

cd /stellar-core
make maintainer-clean distclean clean
