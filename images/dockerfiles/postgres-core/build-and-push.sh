#!/usr/bin/env bash
docker build . -t kinecosystem/postgres-core:v1.0.0
docker push kinecosystem/postgres-core:v1.0.0
