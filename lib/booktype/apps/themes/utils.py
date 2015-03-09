import json
import codecs


def read_theme_info(file_path):
    # TODO
    # Check for any kind of error
    f = codecs.open(file_path, 'r', 'utf8')
    data = json.loads(f.read())

    return data
