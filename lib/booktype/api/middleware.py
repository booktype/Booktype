import logging
import pprint

from django.contrib.auth import authenticate, login

logger = logging.getLogger('api.editor.middleware')


class AuthMiddleware(object):
    """
    Simple middleware if there is a token and user in the request
    that has been generated with the api. This middleware class needs
    to be used together with booktype.api.auth.ApiBackend
    """

    def process_request(self, request):
        if request.method == 'GET':
            data = request.GET

            if 'token' in data and 'user_id' in data:
                user = authenticate(
                    pk=data['user_id'], token=data['token'])

                if user:
                    login(request, user)


class APILoggingMiddleware(object):
    """
    Middleware which will log all `*/_api/*` requests
    """

    MATCH_URL_PREFIX = u'/_api/'

    def process_response(self, request, response):
        if request.path.startswith(self.MATCH_URL_PREFIX) and self.MATCH_URL_PREFIX != request.path:
            logging_data = {
                'request': {},
                'response': {}
            }

            if response.get('content-type') == 'application/json':
                if getattr(response, 'streaming', False):
                    response_body = '<<<<< Streaming >>>>>'
                else:
                    response_body = response.content
            else:
                response_body = '<<<<< NOT application/json >>>>>'

            # request
            logging_data['request']['method'] = request.method
            logging_data['request']['user'] = getattr(request, 'user', None)
            logging_data['request']['path'] = request.path
            logging_data['request']['adress'] = request.META['REMOTE_ADDR']
            # response
            logging_data['response']['status'] = response.status_code
            logging_data['response']['body'] = response_body
            # log it with pformat
            logger.info('\n' + pprint.pformat(logging_data))

        return response
