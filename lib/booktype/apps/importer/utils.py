import shutil
import logging
import tempfile

from contextlib import contextmanager

from booktype.importer.delegate import Delegate
from booktype.importer.notifier import CollectNotifier
from booktype.importer import utils as importer_utils
from booktype.importer.epub.epubimporter import EpubImporter
from booktype.apps.export.utils import get_exporter_class

from booktype.convert.utils.epub import get_sections_settings
from booktype.apps.convert.plugin import SectionsSettingsPlugin
from booktype.utils.misc import booktype_slugify, get_file_extension


logger = logging.getLogger('booktype.apps.importer.utils')


@contextmanager
def temporary_directory():
    """
    This method is meant to delete the temporary directory when operation finish.
    The main idea is to avoid keeping not necessary garbage
    """

    name = tempfile.mkdtemp()
    try:
        yield name
    finally:
        shutil.rmtree(name)


def import_based_on_book(base_book_version, book_dest):
    """
    This will create an epub file from an existing book to later
    use our importing mechanism and put its content into a second book
    (just like cloning action but based on epub)

    Keyword arguments:
        base_book_version -- Book version to be used as base
        book_dest -- Destiny book
    """

    with temporary_directory() as temp_dir:
        temporale_epub = '%s/temporale.epub' % temp_dir

        # it should return object epub book
        # we should be able to write it as a separate thing
        get_exporter_class()(temporale_epub, base_book_version).run()

        return import_based_on_epub(temporale_epub, book_dest)


def import_based_on_epub(epub_file, book_dest):
    """
    It will import an epub file into a existent book on the system.
    This will also try to import sections settings and stuff

    Keyword arguments:
        epub_file -- EPUB file to be imported into book_dest
        book_dest -- Destiny book

    TODO: add docstrings of return info
    """

    notifier = CollectNotifier()
    delegate = Delegate()

    epub_importer = EpubImporter()
    epub_importer.notifier = notifier
    epub_importer.delegate = delegate

    result = {}

    try:
        epub_book = epub_importer.import_file(epub_file, book_dest)
    except Exception as e:
        epub_book = None
        logger.error('ImporterView::Some kind of error while importing book.')
        logger.exception(e)
        notifier.errors.append(str(e))

    # let's try to save sections settings
    if epub_book is not None:
        settings_dict = get_sections_settings(epub_book)
        book_dest_version = book_dest.get_version(None)
        sec_count = 1

        for toc_item in book_dest_version.get_toc():
            if toc_item.is_section():
                url_title = booktype_slugify(toc_item.name)
                section_key = SectionsSettingsPlugin.build_section_key(url_title, sec_count)
                section_settings = settings_dict.get(section_key, None)

                if section_settings is not None:
                    toc_item.settings = section_settings
                    toc_item.save()

                    sec_count += 1

    result['infos'] = notifier.infos
    result['warnings'] = notifier.warnings
    result['errors'] = notifier.errors

    return result


def import_based_on_file(import_file, book_dest):
    """
    It will import the content from a given file (docx or epub for now) into a existent
    book on the system. Note that this is not going to import section settings

    Keyword arguments:
        import_file -- EPUB/DOCX file to be imported into book_dest
        book_dest -- Destiny book
    """

    ext = get_file_extension(import_file.name)

    notifier = CollectNotifier()
    delegate = Delegate()
    result = {}

    try:
        book_importer = importer_utils.get_importer_module(ext)
    except KeyError:
        logger.error('ImporterView::No importer for this extension')
        raise NotImplementedError('Extension not supported!')

    try:
        book_importer(import_file, book_dest, notifier=notifier, delegate=delegate)
        logger.debug('ImporterView::Book imported.')
    except Exception as e:
        logger.error('ImporterView::Some kind of error while importing book.')
        logger.exception(e)
        notifier.errors.append(str(e))

    result['infos'] = notifier.infos
    result['warnings'] = notifier.warnings
    result['errors'] = notifier.errors

    return result
