from django import template


register = template.Library()


def find_with_key(data, key, value):
    """Returns metadata info which has defined value for provided key.

    :Args:
      - data:  EPUB metadata
      - key: propery name we are searching for
      - value: Output profile (e.g. mpdf, screenpdf)

    :Returns:
      Returns metadata entries
    """

    for k, v in data.iteritems():
        for a, b in v.iteritems():
            for c in b:
                if c[1].get(key, '') == value:
                    yield c

    return


def _get_refines(data, prop, name):
    for value in find_with_key(data, 'property', prop):
        if value[0] == name:
            refines = value[1]['refines'][1:]
            val = find_with_key(data, 'id', refines)
            try:
                v = val.next()

                if v:
                    return v
            except StopIteration:
                return None

    return None


def get_refines(data, prop, name):
    """Returns metadata with defined property.

    :Args:
      - data:  EPUB metadata
      - prop: propery name we are searching for
      - name: value propery should have

    :Example:

    >>> get_refines(book.metadata, 'title-type', 'subtitle')

    :Returns:
      Returns metadata entry.
    """

    value = _get_refines(data, prop, name)

    if value:
        return value[0]
    return ''


def get_metadata(data, name):
    """Returns metadata with defined property.

    :Args:
      - data: EPUB metadata
      - name: name of the metadata

    :Example:

    >>> get_metadata(book.metadata, 'publisher')

    :Returns:
      Returns metadata entry.
    """

    for k, v in data.iteritems():
        for a, b in v.iteritems():
            if a == name:
                if len(b) > 0 and len(b[0]) > 0:
                    return b[0][0]

    return ''


def _get_property(data, name):
    """
    Returns metadata value for a property with a given name

    :Args:
      - name: name of the property

    :Returns:
      Returns metadata value.
    """

    val = find_with_key(data, 'property', name)

    if val:
        try:
            value = val.next()
            if value:
                return value[0]
        except StopIteration:
            return ''

    return ''


@register.assignment_tag(takes_context=True)
def get_meta(context, name):
    """Django template assignment tag which returns metadata value.

    :Args:
      - name: name of the metadata key

    :Example:

    >>> {% get_meta "publisher" as publisher %}

    :Returns:
      Returns metadata value.
    """
    return get_metadata(context['metadata'], name)


@register.assignment_tag(takes_context=True)
def get_property(context, name):
    """Django template assignment tag which returns metadata value.

    :Args:
      - name: name of the property

    :Example:

    >>> {% get_property "bkterms:short_description" as description %}

    :Returns:
      Returns metadata value.
    """

    return _get_property(context['metadata'], name)


@register.simple_tag(takes_context=True)
def show_property(context, name):
    """Django template tag which returns metadata value.

    Value is automatically inserted.

    :Args:
      - name: name of the property

    :Example:

    >>> {% show_property "bkterms:short_description"  %}

    :Returns:
      Returns metadata value.
    """

    val = find_with_key(context['metadata'], 'property', name)

    if val:
        try:
            value = val.next()
            if value:
                return value[0]
        except StopIteration:
            return ''

    return ''
