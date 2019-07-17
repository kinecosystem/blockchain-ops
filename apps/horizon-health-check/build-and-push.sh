#!/usr/bin/env bash
docker build . -t kinecosystem/horizon-health-check:v1.0.2
docker push kinecosystem/horizon-health-check:v1.0.2
