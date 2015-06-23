from django.contrib.auth import logout

from booktype.utils.security import Security, get_security


class SecurityMiddleware(object):

    def process_template_response(self, request, response):

        if request.is_ajax():
            return response

        sec = response.context_data.get('security', None)
        if not sec or type(sec) is not Security:
            sec = get_security(request.user)

        response.context_data['can_view_books_list'] = sec.has_perm('portal.can_view_books_list')
        response.context_data['can_view_groups_list'] = sec.has_perm('portal.can_view_groups_list')
        response.context_data['can_view_user_list'] = sec.has_perm('portal.can_view_user_list')

        return response


class StrictAuthentication(object):

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated() and not request.user.is_active:
            logout(request)
