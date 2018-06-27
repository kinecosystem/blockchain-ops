"""
Parameters for the health check
"""

# The stellar-core the horizon process connect to
CORE_INFO_URL = 'http://xxx:11626/info'

# The horizon process to check
HORIZON_METRICS_URL = 'http://localhost:8000/metrics'

# Max amount of failure/total request ratio that is 'Healthy'
MAX_REQUEST_RATIO = 0.1

# Commit hash for this build
BUILD_VERSION = ''

REQUEST_TIMEOUT = 2
