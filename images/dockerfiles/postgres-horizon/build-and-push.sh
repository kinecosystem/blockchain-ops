#!/usr/bin/env bash
docker build . -t kinecosystem/postgres-horizon:v1.0.0
docker push kinecosystem/postgres-horizon:v1.0.0
