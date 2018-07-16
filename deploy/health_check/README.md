# Horizon Health Check

Health check for horizon that returns Healthy/Unhealthy based on the "state" of the stellar-core that the horizon is connected to

## Configuration

Edit the following parameters in the docker-compose file:

```yaml
BUILD_VERSION: c8407ce
REQUEST_TIMEOUT: 2
CORE_INFO_URL: http://xxxxx:11626/info
```

## Run

```bash
$ docker-compose up -d
```


# Endpoints

**GET '/status'**
```javascript
// HTTP 200
{
    "status": "Healthy",
    "description": "Core is synced",
    "start_timestamp": 1530433274,
    "build": "abcde"
}
```

```javascript
// HTTP 503
{
    "status": "Unhealthy",
    "description": "Core is unsynced/Unable to reach core : <exception>",
    "start_timestamp": 1530433274,
    "build": "abcde"
}
```
