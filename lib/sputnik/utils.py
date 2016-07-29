from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder


class LazyEncoder(DjangoJSONEncoder):
    """
    Simple encoder to be able to send lazy translated strings
    through sputnik or via json response. This will force the convert of
    things like __proxy__ objects into unicode strings
    """

    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)
