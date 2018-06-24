# json_check

A custom datadog-agent check that gets a json response from a given URL,
and extracts a specific metric from it based on a given JSON path.

## Install

To use the `json_check` check, you will need to install the "jsonpath-rw" Python package.

NOTE datadog-agent uses his own copies of python and pip.

```bash
$ /opt/datadog-agent/embedded/bin/pip install jsonpath-rw
```

## Configurations

Edit `json_check.yaml`:

- default_timout: how long to wait for the GET request to complete
- url: the URL to send the request to
- metrics: the name of the metrics to send to datadog,
and the JSON path the metric value should be fetched from.
See [Syntax for JSON path](https://github.com/kennknowles/python-jsonpath-rw#jsonpath-syntax) for additional information.

## Events

The check will send the following events in case of a failure:

- Request timeout: In the event of a timeout.
- Invalid status code for URL: For any status code other than HTTP 200.
- No matching value: When no value was found for the given JSON path.
- Unexpected match: When the value found is not a number.

## Example

Get the price of BTC and ETH

```yaml
init_config:
    default_timeout: 5

instances:
    - url: https://api.coinmarketcap.com/v2/ticker
      metrics:
      # Numeric key names should be in double quotes, otherwise they will be considered as an array index
        - usd.price: data."1".quotes.USD.price
        - eth.price: '[data]["1027"][quotes][USD][price]'
```
