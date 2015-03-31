import json
import celery
import urllib
import urllib2
import httplib
import time
import datetime

from django.conf import settings

import sputnik

from booki.editor import models


def fetch_url(url, data, method='GET'):
    if method.lower() == 'get':
        url = url + '?' + urllib.urlencode(data)

        req = urllib2.Request(url)
    else:
        try:
            data_json = json.dumps(data)
        except TypeError:
            return None

        req = urllib2.Request(url, data_json)

    req.add_header('Content-Type', 'application/json')
    req.add_header('Content-Length', len(data_json))

    try:
        r = urllib2.urlopen(req)
    except (urllib2.HTTPError, urllib2.URLError, httplib.HTTPException):
        pass
    except Exception:
        pass

    # should really be a loop of some kind
    try:
        s = r.read()
        dta = json.loads(s.strip())
    except:
        return None

    return dta


@celery.task
def publish_book(*args, **kwargs):
    import urllib2
    import json
    import logging

    # Entire publisher is at the moment hard coded for pdf output

    # set logger
    logger = logging.getLogger('booktype')
    logger.debug(kwargs)

    book = models.Book.objects.get(id=kwargs['bookid'])

    book_url = "%s/%s/_export/" % (settings.BOOKTYPE_URL, book.url_title)

    data = {
        "assets": {
            "input.epub": book_url
        },
        "input": "input.epub",
        "outputs": {}
    }

    for _format in kwargs['formats']:
        _ext = "pdf"
        if _format == "epub":
            _ext = "epub"

        data["outputs"][_format] = {
            "profile": _format,
            "config": {
                "project_id": book.url_title
            },
            "output": "{}.{}".format(book.url_title, _ext)
        }

    logger.debug(data)

    output_results = {}
    # _format: False for _format in data["outputs"].iterkeys()}

    result = fetch_url(
        '{}/_convert/'.format(settings.BOOKTYPE_URL), data, method='POST')

    if not result:
        sputnik.addMessageToChannel2(
            kwargs['clientid'],
            kwargs['sputnikid'],
            "/booktype/book/%s/%s/" % (book.pk, kwargs['version']),
            {
                "command": "book_published",
                "state": 'FAILURE'
            },
            myself=True
        )
        return

    task_id = result['task_id']
    start_time = time.time()

    while True:
        if time.time() - start_time > 45:
            sputnik.addMessageToChannel2(
                kwargs['clientid'],
                kwargs['sputnikid'],
                "/booktype/book/%s/%s/" % (book.pk, kwargs['version']),
                {
                    "command": "book_published",
                    "state": 'FAILURE'
                },
                myself=True
            )
            break

        try:
            response = urllib2.urlopen(
                '{}/_convert/{}'.format(settings.BOOKTYPE_URL, task_id)).read()
        except (urllib2.HTTPError, urllib2.URLError, httplib.HTTPException):
            logger.error(
                'Could not communicate with a server to fetch polling data.')
        except Exception:
            logger.error(
                'Could not communicate with a server to fetch polling data.')

        try:
            dta = json.loads(response)
        except TypeError:
            dta = {'state': ''}
            logger.error('Could not parse JSON string.')

        if dta['state'] == 'SUCCESS':
            for _key in data["outputs"].iterkeys():
                if 'state' in dta['result'][_key]:
                    if dta['result'][_key]['state'] == 'SUCCESS':
                        output_results[_key] = True
                    elif dta['result'][_key]['state'] == 'FAILURE':
                        output_results[_key] = False

            if len(output_results) == len(data["outputs"].keys()):
                def _x(_key):
                    d = {}
                    if 'result' in dta['result'][_key]:
                        d = dta['result'][_key]['result']
                    d['status'] = output_results[_key]
                    return d

                urls = {_key: _x(_key) for _key in output_results.iterkeys()}

                _now = datetime.datetime.now()

                sputnik.addMessageToChannel2(
                    kwargs['clientid'],
                    kwargs['sputnikid'],
                    "/booktype/book/%s/%s/" % (book.pk, kwargs['version']), {
                        "command": "book_published",
                        "state": 'SUCCESS',
                        "username": kwargs["username"],
                        "exported": _now.isoformat(),
                        "urls": urls
                    },
                    myself=True
                )
                break

        if dta['state'] == 'FAILURE':
            sputnik.addMessageToChannel2(
                kwargs['clientid'],
                kwargs['sputnikid'],
                "/booktype/book/%s/%s/" % (book.pk, kwargs['version']),
                {
                    "command": "book_published",
                    "state": 'FAILURE'
                },
                myself=True
            )
            break

        time.sleep(0.5)
