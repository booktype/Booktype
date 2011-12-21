from django.template.defaultfilters import slugify

def bookiSlugify(text):
    """
    Wrapper for default Django function. Default function does not work with unicode strings.

    @type text: C{string}
    @param: Text you want to slugify

    @rtype: C{string}
    @return: Returns slugified text
    """
    
    try:
        import unidecode

        text = unidecode.unidecode(text)
    except ImportError:
        pass

    return slugify(text)
