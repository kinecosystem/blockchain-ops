#!/usr/bin/env python
"""Receive seed and print address."""

import sys
from stellar_base.keypair import Keypair


if __name__ == '__main__':
    kp = Keypair.from_seed(sys.argv[1])
    print(kp.address().decode())
