# Stellar Operations

Devops repository for Stellar Core and Horizon.

## Local Private Testnet

```bash
# initialize a new local test network with single core + horizon instances
# see the steps in init.sh for further details
# and also see docker-compose.yml for listening ports
cd image
./init.sh

# read logs
docker compose logs -f

# interesting metrics:

# horizon
curl -sS localhost:8000
curl -sS localhost:8000/metrics

# core
# https://www.stellar.org/developers/stellar-core/software/commands.html
curl -sS localhost:11626/info
curl -sS localhost:11626/quorum
curl -sS localhost:11626/peers

# for /metrics, pipe output to jq for easier reading:
curl -sS localhost:11626/metrics | jq .
```

## Official Resources

### Core

1. [Administration](https://www.stellar.org/developers/stellar-core/software/admin.html)
1. [CLI Commands + HTTP API](https://www.stellar.org/developers/stellar-core/software/commands.html)
1. [Se tup a Private Network](https://www.stellar.org/developers/stellar-core/software/testnet.html)
1. [github.com/stellar/stellar-core](https://github.com/stellar/stellar-core)
1. [github.com/stellar/stellar-protocol](https://github.com/stellar/stellar-protocol)

### Horizon

1. [Administration](https://www.stellar.org/developers/horizon/reference/admin.html)
1. [github.com/stellar/horizon](https://github.com/stellar/horizon)
  1. Deprecated repo
  1. Has latest stable release v0.11.1
1. [github.com/stellar/go](https://github.com/stellar/go)
  1. New mono-repo
  1. Has v0.12.0 RC
  1. Includes various other tools e.g. archivist, bifrost, hd wallet, etc.
