import json
import celery
import urllib
import urllib2
import httplib
import time
import datetime
import logging
from collections import namedtuple

from django.conf import settings
from django.contrib.auth.models import User

import sputnik

from booki.editor import models
from booktype.apps.export.models import BookExport, ExportFile
from booktype.apps.export.utils import get_settings_as_dictionary
from .utils import send_notification


logger = logging.getLogger('booktype')


def fetch_url(url, data, method='GET'):
    if method.lower() == 'get':
        url = url + '?' + urllib.urlencode(data)

        req = urllib2.Request(url)
    else:
        try:
            data_json = json.dumps(data)
        except TypeError:
            logger.exception('Could not serialize to JSON.')
            return None

        req = urllib2.Request(url, data_json)

    req.add_header('Content-Type', 'application/json')
    req.add_header('Content-Length', len(data_json))

    try:
        r = urllib2.urlopen(req)
    except (urllib2.HTTPError, urllib2.URLError, httplib.HTTPException):
        logger.exception('Could not load URL {}.'.format(url))
        return None
    except Exception:
        logger.exception('Could not load URL {}.'.format(url))
        return None

    # should really be a loop of some kind
    try:
        s = r.read()
        dta = json.loads(s.strip())
    except:
        logger.exception('Could not load JSON data.')
        return None

    return dta


def get_theme(book, username):
    from booktype.apps.themes.models import UserTheme

    data = {}
    owner = User.objects.get(username=username)

    try:
        theme = UserTheme.objects.get(book=book, owner=owner)
    except Exception:
        return data

    data = {'id': theme.active}

    if theme.active == 'custom':
        data['custom'] = theme.custom

    return data


@celery.task
def publish_book(*args, **kwargs):
    global x

    # Entire publisher is at the moment hard coded for pdf output

    # set logger
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
                "project_id": book.url_title,
                "settings": get_settings_as_dictionary(book, _format),
                "theme": get_theme(book, kwargs["username"])
            },
            "output": "{}.{}".format(book.url_title, _ext)
        }

    logger.debug(data)

    output_results = {}
    # _format: False for _format in data["outputs"].iterkeys()}

    convert_url = '{}/_convert/'.format(settings.CONVERT_URL)
    result = fetch_url(convert_url, data, method='POST')

    if not result:
        logger.error('Could not fetch the book from [{}]'.format(convert_url))
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

                exporter = User.objects.get(username=kwargs["username"])

                exprt = BookExport(version=book.get_version(),
                                   name='Book export - {}'.format(_now),
                                   user=exporter,
                                   task_id=task_id,
                                   created=_now,
                                   published=None,
                                   status=0)
                exprt.save()

                _files = {}

                for output_type, result in dta['result'].iteritems():
                    if 'state' in result:
                        if result['state'] == 'SUCCESS':
                            status = 0
                            description = ''
                            filename = result['result']['output']
                            filesize = result['result'].get('size', 0)
                            pages = result['result'].get('pages', 0)
                        else:
                            status = 1
                            description = result.get('error', '')
                            filename = None
                            filesize = 0
                            pages = 0

                        ef = ExportFile(export=exprt,
                                        typeof=output_type,
                                        filesize=filesize,
                                        pages=pages,
                                        status=status,
                                        description=description,
                                        filename=filename
                                        )
                        ef.save()

                        _files[output_type] = {'filename': filename,
                                               'status': status,
                                               'description': description,
                                               'filesize': filesize,
                                               'pages': pages
                                               }

                export_name = "Book export - {}".format(_now)

                sputnik.addMessageToChannel2(
                    kwargs['clientid'],
                    kwargs['sputnikid'],
                    "/booktype/book/%s/%s/" % (book.pk, kwargs['version']), {
                        "command": "book_published",
                        "state": 'SUCCESS',
                        "name": export_name,
                        "username": kwargs["username"],
                        "task_id": task_id,
                        "created": _now.strftime("%d.%m.%Y %H:%M:%S"),
                        "published": "",
                        "status": 0,
                        "files": _files,
                        "comments": []
                    },
                    myself=True
                )

                # emulate user object and request object needed for send_notification function
                user = namedtuple('user', 'username')(username=kwargs['username'])
                request = namedtuple('request', 'user clientID sputnikID')(user=user,
                                                                           clientID=kwargs['clientid'],
                                                                           sputnikID=kwargs['sputnikid'])

                send_notification(request, kwargs['bookid'], kwargs['version'],
                                  "notification_book_export_was_successful", export_name)

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
