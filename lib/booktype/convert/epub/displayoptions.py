
XML_TEXT = """<?xml version="1.0" encoding="UTF-8"?>
<display_options>
<platform name="*">
<option name="specified-fonts">%(specified_fonts)s</option>
</platform>
</display_options>"""

DEFAULT_OPTIONS = {
    "specified_fonts": "true",
}


def make_display_options_xml(**kwargs):
    options = DEFAULT_OPTIONS

    if kwargs.get("specified_fonts"):
        options["specified_fonts"] = "true"

    return XML_TEXT % options
