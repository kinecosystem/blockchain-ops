from hashlib import sha256

from kin import Keypair
from kin_base import Keypair as BaseKeypair


def derive_root_account(passphrase):
    """Return the keypair of the root account, based on the network passphrase"""
    network_hash = sha256(passphrase.encode()).digest()
    seed = BaseKeypair.from_raw_seed(network_hash).seed().decode()
    return Keypair(seed)
