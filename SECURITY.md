# Security Concerns

The following is a security checklist of issues that should be taken into account when managing Core and Horizon nodes.

## Stellar Security Guide

Start by reading through Stellar's [security guide](https://www.stellar.org/developers/guides/security.html).

## Seed Management

### Core

The seed of every core node is the most critical information to secure.
If a seed is compromised, an attacker could impersonate the Core node whose seed belongs to.

1. Secure and limit access to all copies of the seed:
    1. Core configuration file containing the seed should have limited user read access on the Core node instance.
    1. Backups should have very limited access.
        - At Kin we store the seed backups using AWS [SSM Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-paramstore.html)
using very limited permissions.

### Root Account

When a new network is started up from scratch, all initial XLM is deposited in a single account, called the *root account*.
The root account's seed is deterministically derived from the network passphrase, meaning it is accessible to everyone.
Thus, before exposing the network to the public, it is vital that the root account funds be transferred out to another account,
and have the root account master key burnt (have its weight set from 1 to 0).

## Network Access

### Core Ports

Core exposes two ports: P2P (11525) and control (11626).

1. P2P port should be publicly open.
1. The control port should be private and accessible only to Core's related Horizon.

### RDS

1. Databases should not be exposed, and given access only to the Core and related Horizon apps.

#### User Setup

Core's RDS should have two users set up:

1. User for Core access with read/write permissions to the "core" database.
1. User for Horizon access with read-only permissions to the "core" database.
1. RDS admin user should not be used in production.

Horizon's RDS should have a single user set up:

1. User for Horizon access with read/write permissions to the "horizon" database.
1. RDS admin user should not be used in production.

### S3

1. History archive should be publicly readable globally, and specifically available for other nodes to catch up.
1. Wriet access should only be given to the Core instance managing the archive.
