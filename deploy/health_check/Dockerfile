FROM python:alpine3.6

# Copy the project
COPY . /opt/health_check

WORKDIR /opt/health_check

# Install dependencies
RUN pip install pipenv \
    &&  apk add -qU --no-cache -t .build-deps gcc musl-dev git \
    &&  pipenv install \
    &&  apk del -q .build-deps
EXPOSE 8000
CMD pipenv run gunicorn -b 0.0.0.0:8000 main:APP
