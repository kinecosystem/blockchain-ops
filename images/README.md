# Docker Images

This directory includes Dockerfiles for building and running Kin network apps.
It also includes automation scripts for launching a test network on your local machine.

## Local Network

The following example shows how to start a local test network:

```bash
# initialize a new local test network with single core + horizon instances
# see the steps in init.sh for further details
# and also see docker-compose.yml for listening ports
./init.sh

# read logs
docker-compose logs -f

# upgrade base reserve balance network setting to 0.5 XLM (executed automatically in init.sh)
# see the following section for more information:
# https://www.stellar.org/developers/stellar-core/software/admin.html#network-configuration
curl 'localhost:11626/upgrades?mode=set&upgradetime=1970-01-01T00:00:00Z&basereserve=5000000'

# NOTE max_tx_set_size has a different internal parameter name
curl 'localhost:11626/upgrades?mode=set&upgradetime=1970-01-01T00:00:00Z&maxtxsize=5000000'

# friendbot is available
curl -sS localhost:8001?addr=MyAddress

# stellar laboratory is also available
# open localhost:8002 in your web browser to interact with it

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
