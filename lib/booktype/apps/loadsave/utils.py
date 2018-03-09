import fnmatch
import tempfile

from django.conf import settings
from django.core.exceptions import PermissionDenied

from booktype.apps.export.utils import get_exporter_class


def split_domain_port(host):
    """
    Splits a host into a (domain, port) tuple and lowecases
    the domain
    """
    host = host.lower()

    if host[-1] == ']':
        # It's an IPv6 address without a port.
        return host, ''

    bits = host.rsplit(':', 1)
    if len(bits) == 2:
        return tuple(bits)

    return bits[0], ''


def validate_host(host, allowed_hosts):
    """
    Validate that the host is in the list of allowed_hosts

    Hosts can have patterns like the ones in the ``fnmatch`` module.
    Also, any host begining with a period will match the domain and all
    subdomains.

    ``*`` matches everything.

    Return ``True`` if the host is valid, ``False`` otherwise.
    """

    for pattern in allowed_hosts:
        pattern = pattern.lower()
        if pattern[0] == '.':
            if fnmatch.fnmatch(host, pattern[1:]) or \
               fnmatch.fnmatch(host, '*' + pattern[1:]):
                return True
        else:
            if fnmatch.fnmatch(host, pattern):
                return True

    return False


class RestrictExport(object):
    def get_host(self, request):
        keys = 'REMOTE_HOST', 'REMOTE_ADDR', 'HTTP_X_FORWARDED_SERVER'
        for key in keys:
            host = request.META.get(key, '')

            if host:
                return host

    def dispatch(self, request, *args, **kwargs):
        host = self.get_host(request)
        domain, port = split_domain_port(host)

        if not (domain and validate_host(
                domain, settings.EXPORT_ALLOWED_HOSTS)):
            raise PermissionDenied()

        return super(RestrictExport, self).dispatch(request, *args, **kwargs)

