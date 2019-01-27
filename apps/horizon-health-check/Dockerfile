FROM python:alpine3.6

COPY main.py Pipfile Pipfile.lock /opt/horizon-health-check/
WORKDIR /opt/horizon-health-check

# Install dependencies
RUN pip install pipenv \
    && apk add -qU --no-cache -t .build-deps gcc musl-dev git \
    && pipenv sync --bare --clear \
    && apk del -q .build-deps

EXPOSE 8000
