FROM python:3.7-alpine3.9

WORKDIR /opt/blockchain-pulse-service

COPY Pipfile Pipfile.lock /opt/blockchain-pulse-service/
# Install dependencies
RUN pip install pipenv \
    && apk add -qU --no-cache -t .build-deps gcc musl-dev git \
    && pipenv sync --bare --clear \
    && apk del -q .build-deps

COPY main.py /opt/blockchain-pulse-service/
EXPOSE 8000
