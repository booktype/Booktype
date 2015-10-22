import logging
import requests
import json

logger = logging.getLogger('booktype')


def fetch_url(url, data, method='GET'):
    """Send and receive JSON data from the server.

    :Args:
      - url: URL we are communicating with
      - data: Dictionary with data we are sending
      - method: GET or POST method

    :Returns:
      Dictionary with JSON data. None in case of errors.
    """
    headers = {
        'Content-Type': 'application/json',
        'Content-Length': len(data)
    }

    try:
        if method.lower() == 'get':
            req = requests.get(url, headers=headers, params=data)
        else:
            req = requests.post(url, headers=headers, data=json.dumps(data))
    except requests.exceptions.ConnectionError:
        logger.exception('Connection error when loading {}.'.format(url))
    except requests.exceptions.Timeout:
        logger.exception('Timeout when loading {}.'.format(url))
    except requests.exceptions.RequestException:
        logger.exception('Could not load {}.'.format(url))

    if req.status_code != 200:
        logger.exception('Got {} response code when loading URL {}.'.format(req.status_code, url))
        return None

    try:
        dta = req.json()
    except ValueError:
        logger.exception('Could not load JSON data.')
        return None

    return dta
