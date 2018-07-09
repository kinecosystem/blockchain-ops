# nginx-proxy

In a case of an SSE event, horizon may not send any data for 60+ seconds, which causes a 504 timeout by Amazon's ELB
With this docker image we can proxy requests to horizon, timeout requests on our own instead or letting ELB do it, and send 200 instead of 504 for SSE reqests.

## Usage

In docker-compose:

```yaml
  horizon:
    image: kinecosystem/horizon
    ports:
      - 8000:8000
    environment:
      driver: json-file
      .
      .
      .


  nginx:
    image: kinecosystem/nginx-proxy:67910b1
    ports:
      - 80:80
      - 443:443
    environment:
      PROXY_READ_TIMEOUT: 10
      PROXY_PASS_URL: http://horizon:8000
```
