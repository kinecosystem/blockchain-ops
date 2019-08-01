# CORE DB

This is a docker image for a postgres internal DB 

## Usage

In docker-compose, inside the Core app.

```yaml
services:
  image: kinecosystem/postgres-core:v1.0.0
    environment:
      POSTGRES_USER: DB-USER
      POSTGRES_PASSWORD: "DB-PASSWORD"
      POSTGRES_DB: DB-NAME
    ports:
      - 5432:5432
    volumes:
      - /data/postgresql/data:/var/lib/postgresql/data
      - /var/run/postgresql:/var/run/postgresql
```

