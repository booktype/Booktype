import celery
import celery.result

from booki.editor import models

import sputnik


def fetch_url(url, data):
    import urllib2
    import httplib
    import json

    try:
        data_json = json.dumps(data)
    except TypeError:
        return None

    req = urllib2.Request(url, data_json)

    req.add_header('Content-Type', 'application/json')
    req.add_header('Content-Length', len(data_json))

    try:
        r = urllib2.urlopen(req)
    except (urllib2.HTTPError, urllib2.URLError, httplib.HTTPException) as e:
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
    import urllib
    import httplib
    import json

    import logging
    logger = logging.getLogger('booktype')
    logger.debug(kwargs)

    book = models.Book.objects.get(id=kwargs['bookid'])

    data = {"assets" : {
                         "testbook.epub" : "http://127.0.0.1:8000/%s/_export/" % book.url_title
                        },
             "input" : "testbook.epub",
             "outputs": {
             "two" : {
                      "profile" : "epub-bodde",
                      "config": {
                                'project_id':  book.url_title
                                },
                      "output" : "testbook.epub"
                    }
                    }
            }   
    logger.debug(data)

    result = fetch_url('http://127.0.0.1:8000/_convert/', data)
    logger.debug(result)
    task_id = result['task_id']


    while True:
        logger.debug('http://127.0.0.1:8000/_convert/%s' % task_id)
        response = urllib2.urlopen('http://127.0.0.1:8000/_convert/%s' % task_id).read()
        dta = json.loads(response)
        logger.debug(dta)

        sputnik.addMessageToChannel2(kwargs['clientid'], kwargs['sputnikid'], "/booktype/book/%s/%s/" % (book.pk, kwargs['version']),
                                     {"command": "publish_progress",
                                      "state": dta['state']}, myself=True)

        if dta['state'] in ['SUCCESS', 'FAILURE']:
            break


