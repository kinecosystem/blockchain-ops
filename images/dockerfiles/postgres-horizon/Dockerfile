FROM postgres:10-alpine

EXPOSE 5432

COPY conf-files/postgresql.conf /etc/postgresql/postgresql.conf
RUN chown -R postgres:postgres /etc/postgresql
CMD ["postgres", "-c", "config-file=/etc/postgresql/postgresql.conf"]
