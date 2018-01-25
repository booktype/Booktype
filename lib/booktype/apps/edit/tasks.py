import celery
import time
import datetime
import logging
from collections import namedtuple

from django.conf import settings
from django.contrib.auth.models import User

import sputnik

from booki.editor import models
from booktype.utils import config, download
from booktype.apps.export.models import BookExport, ExportFile
from booktype.apps.export.utils import get_settings_as_dictionary
from booktype.apps.themes.models import BookTheme
from .utils import send_notification


logger = logging.getLogger('booktype')


def get_theme(book):
    data = {}

    try:
        theme = BookTheme.objects.get(book=book)
    except Exception:
        return data

    data = {'id': theme.active}

    if theme.active == 'custom':
        data['custom'] = theme.custom

    return data


@celery.task
def publish_book(*args, **kwargs):
    # global x

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
        _suffix = "-{}".format(_format.upper())

        if _format == "epub3":
            _ext = "epub"
        elif _format == "epub2":
            _ext = "epub"
        elif _format == "mobi":
            _ext = "mobi"
        elif _format == "xhtml":
            _ext = "zip"
        elif _format == "icml":
            _ext = "zip"
        elif _format == "xml":
            _ext = "zip"
        elif _format == "docx":
            _ext = "zip"
        elif _format == "pdfreactor":
            _ext = "pdf"
        elif _format == "pdfreactor-screenpdf":
            _ext = "pdf"

        format_settings = get_settings_as_dictionary(book, _format)

        data["outputs"][_format] = {
            "profile": _format,
            "config": {
                "project_id": book.url_title,
                "settings": format_settings,
                "theme": get_theme(book)
            },
            "output": "{0}_{1}{2}.{3}".format(
                book.url_title,
                datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
                _suffix,
                _ext
            )
        }

        if 'cover_image' in format_settings:
            if format_settings['cover_image'].strip() != '':
                cover_url = "{}/{}/_cover/{}".format(
                    settings.BOOKTYPE_URL,
                    book.url_title,
                    format_settings['cover_image']
                )
                data['assets']['{}_cover_image'.format(_format)] = cover_url
                data["outputs"][_format]["config"]["cover_image"] = '{}_cover_image'.format(_format)

    logger.debug(data)

    output_results = {}
    # _format: False for _format in data["outputs"].iterkeys()}

    convert_url = '{}/_convert/'.format(settings.CONVERT_URL)
    result = download.fetch_url(convert_url, data, method='POST')

    if not result:
        logger.error('Could not send the publishing request to [{}]'.format(convert_url))
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

    EXPORT_WAIT_FOR = config.get_configuration('EXPORT_WAIT_FOR', 90)  # noqa
    logger.debug('Waiting for the task %s to finish. Will wait for %s seconds.', task_id, EXPORT_WAIT_FOR)

    while True:
        if time.time() - start_time > EXPORT_WAIT_FOR:
            logger.error('Publishing request timed out after %s seconds.', int(time.time() - start_time))
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

        dta = download.fetch_url('{}/_convert/{}'.format(settings.CONVERT_URL, task_id), {}, method='GET')

        if not dta:
            logger.error(
                'Could not communicate with a server to fetch polling data.')

        if dta['state'] == 'SUCCESS':
            for _key in data["outputs"].iterkeys():
                if 'state' in dta['result'][_key]:
                    if dta['result'][_key]['state'] == 'SUCCESS':
                        output_results[_key] = True
                    elif dta['result'][_key]['state'] == 'FAILURE':
                        output_results[_key] = False

            if len(output_results) == len(data["outputs"].keys()):
                _now = datetime.datetime.now()
                export_name = "Book export - {0}".format(
                    datetime.datetime(
                        _now.year, _now.month, _now.day,
                        _now.hour, _now.minute, _now.second
                    )
                )

                exporter = User.objects.get(username=kwargs["username"])

                exprt = BookExport(
                    version=book.get_version(),
                    name=export_name,
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

                        ef = ExportFile(
                            export=exprt,
                            typeof=output_type,
                            filesize=filesize,
                            pages=pages,
                            status=status,
                            description=description,
                            filename=filename)
                        ef.save()

                        _files[output_type] = {
                            'filename': filename,
                            'status': status,
                            'description': description,
                            'filesize': filesize,
                            'pages': pages}

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

                logger.info('Successfully received status of the conversion task %s.', task_id)
                # emulate user object and request object needed for send_notification function
                user = namedtuple('user', 'username')(username=kwargs['username'])
                request = namedtuple('request', 'user clientID sputnikID')(user=user,
                                                                           clientID=kwargs['clientid'],
                                                                           sputnikID=kwargs['sputnikid'])

                send_notification(request, kwargs['bookid'], kwargs['version'],
                                  "notification_book_export_was_successful", export_name)

                break

        if dta['state'] == 'FAILURE':
            logger.error('Convert returned FAILURE status. Publishing will not be finished.')

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
