#!/usr/bin/env bash
docker build . -t kinecosystem/horizon-telegraf-test-env:v1.0.0
docker push kinecosystem/horizon-telegraf-test-env:v1.0.0
