#!/bin/sh
set -e

# Edit the network.js file to change the network used
sed -i "s@https://horizon-testnet.stellar.org@$HORIZON_ENDPOINT_TESTNET@g" /opt/laboratory/dist/app*.js
sed -i "s@r.Networks.TESTNET@'$NETWORK_PASSPHRASE_TESTNET'@g" /opt/laboratory/dist/app*.js

# Edit the accountCreator.js file to change the friendbot service used
sed -i "s@https://friendbot.stellar.org@$FRIENDBOT_ENDPOINT@g" /opt/laboratory/dist/app*.js

http-server /opt/laboratory/dist
