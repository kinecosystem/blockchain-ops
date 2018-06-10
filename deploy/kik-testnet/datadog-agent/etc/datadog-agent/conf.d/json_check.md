# json_check
A custom datadog-agent check that gets a json response from a given URL, and extract a specific metric from it based on a given json path

## Installation

To use the json_check check, you will need to install the "jsonpath-rw" package
Remember the datadog-agent uses his own copy of python and pip so use them

```bash
/opt/datadog-agent/embedded/bin/pip install jsonpath-rw
```

## Configurations:
Edit the json_check.yaml file to configure the check

* ```default_timout``` - how long to wait for the GET request to complete
* ```url``` - the URL to send the request to
* ```metrics``` - the name of the metric to send, and the json path it should be in. [Syntax for json path](https://github.com/kennknowles/python-jsonpath-rw#jsonpath-syntax)

## Events:
The check will send events in case of a failure
* "request timeout" - in the event of a timeout
* "Invalid status code for URL" - for any status code other than 200
* "no matching value" - when no value was found for the given json path
* "unexpected match" - when the value found is not a number

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
