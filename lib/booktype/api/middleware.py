import json
from django.contrib.auth import authenticate, login


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
