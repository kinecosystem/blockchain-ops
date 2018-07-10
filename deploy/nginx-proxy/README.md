# Horizon Nginx Proxy

In the of an SSE event, Horizon may not send any data for 60+ seconds.
This causes AWS ELB to cut the connection and return HTTP 504,
which in turn looks like an error.

See the following issue for more information: [stellar/go/issues/154](https://github.com/stellar/go/issues/154)

With this docker image we can proxy requests to Horizon,
timeout requests on our own instead or letting ELB do it,
and send 200 instead of 504 for SSE reqests.

## Usage

In docker-compose.yml:

```yaml
version: "3"

horizon:
  image: kinecosystem/horizon
  # ...

horizon-nginx-proxy:
  image: kinecosystem/horizon-nginx-proxy:latest  # or any other version
  ports:
    - 8000:8000
  environment:
    PROXY_READ_TIMEOUT: 10
    PROXY_PASS_URL: http://horizon:8000
```
