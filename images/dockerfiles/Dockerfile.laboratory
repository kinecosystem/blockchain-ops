FROM node:9.11-alpine

ENV LABORATORY_COMMIT 4ae9ca92d74fd8ff0a71889819154f6713d1c4bb

RUN mkdir -p /opt/laboratory

RUN apk add -qU --no-cache -t .build-deps git \
    &&  cd /opt/laboratory \
    &&  git init \
    &&  git remote add origin https://github.com/stellar/laboratory.git \
    &&  git pull origin master \
    &&  git reset --hard $LABORATORY_COMMIT \
    &&  npm install -s \
    &&  npm install -g http-server \
    &&  apk del -q .build-deps \
    &&  ./node_modules/.bin/gulp build \
    &&  ls | grep -v dist | xargs rm -r

COPY ./laboratory/opt/laboratory/init.sh /opt/laboratory

EXPOSE 8080

CMD /opt/laboratory/init.sh
