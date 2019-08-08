#!/usr/bin/env bash
docker build . -t kinecosystem/blockchain-pulse-service:v1.0.0
docker push kinecosystem/blockchain-pulse-service:v1.0.0
