FROM postgres:10-alpine

EXPOSE 5432

RUN postgres -c 'config_file=/etc/postgresql/postgresql.conf'

COPY conf-files/postgresql.conf /etc/postgresql
