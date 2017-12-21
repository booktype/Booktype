import os
import lxml
import ooxml
import logging
import zipfile
import datetime
from lxml import html, etree
from unidecode import unidecode

from django.core.files.base import ContentFile
from django.utils.translation import ugettext as _

from booki.editor import models
from booki.utils.log import logChapterHistory, logBookHistory

from booktype.utils import config
from booktype.utils.tidy import tidy_cleanup
from booktype.utils.misc import booktype_slugify, get_default_book_status
from booktype.importer.epub.readerplugins import TidyPlugin
from booktype.importer.notifier import CollectNotifier
from booktype.importer.delegate import Delegate
from booktype.importer.signals import book_imported, chapter_imported

from ooxml import importer, serialize, doc

from . import utils as docutils
from .styles import STYLE_EDITOR, STYLE_EPUB

logger = logging.getLogger("booktype.importer.docx.docximporter")


# Link to default serialize options in ooxml at the moment
# https://github.com/booktype/python-ooxml/blob/833e65808b39ca3bc5499f64ad38f73c6458372a/ooxml/serialize.py#L1034-L1060
# these options will be merged with ooxml default ones

SERIALIZE_OPTIONS = {
    'header': docutils.DocHeaderContext,
    'embed_styles': True,
    'embed_fontsize': True,
    'serializers': {
        doc.Math: docutils.serialize_empty,
        # doc.Footnote: serialize_footnote,
        # doc.Endnote: serialize_endnote
    },
    'hooks': {
        'p': [docutils.hook_p],
        'h': [docutils.check_h_tags_hook],
        'table': [docutils.hook_infobox_table],
        'footnote': [docutils.hook_footnote],
        'endnote': [docutils.hook_endnote]
    }
}


class WordImporter(object):

    def __init__(self, book=None, chapter=None, serialize_options=SERIALIZE_OPTIONS, **kwargs):
        """
        Args:
            - book (`booki.editor.models.Book`) Booktype model instance of book
            - chapter (`booki.editor.models.Chapter`) Booktype model instance of chapter
            - serialize_options (`dict`) A dictionary with options to be passed to ooxml library

            kwargs: Some keyword arguments might be:
                - delegate (`importer.delegate.Delegate`) Delegate instance
                - notifier (`importer.notifier.CollectNotifier`) Notifier instance
                - user (`django.contrib.auth.models.User`) Django user instance

        """

        self.book = book
        self.chapter = chapter
        self.is_chapter_mode = (chapter is not None)

        self._serialize_options = serialize_options

        self.notifier = kwargs.get('notifier', CollectNotifier())
        self.delegate = kwargs.get('delegate', Delegate())
        self.user = kwargs.get('user', None)

        # Attachment objects indexed by image file name
        self._attachments = {}

        # Chapter objects indexed by document file name
        self._chapters = {}

    def _check_for_elements(self):
        found_math = False

        for elem in self.dfile.document.elements:
            if isinstance(elem, doc.Paragraph):
                for el in elem.elements:
                    if isinstance(el, doc.Math):
                        found_math = True

        if found_math:
            warn_msg = _("Please note: Mathematical formulae have been found, and highlighted in the text. These formulae are not supported by many e-readers, or the Booktype editor at present.")  # noqa
            self.notifier.warning(warn_msg)

    def import_file(self, file_path, options={'scale_font_size': True}, **kwargs):
        # TODO: document this asap

        self.delegate.notifier = self.notifier
        self.broken_images = []
        self.converted_images = []

        book = self.book
        process_mode = kwargs.get('process_mode', 'overwrite')

        try:
            self.dfile = ooxml.read_from_file(file_path)
            if self.is_chapter_mode:
                chapter_content = serialize.serialize(
                    self.dfile.document, self._serialize_options)
                self._import_single_chapter(self.chapter, chapter_content, process_mode)
            else:
                chapters = importer.get_chapters(
                    self.dfile.document, options=options,
                    serialize_options=self._serialize_options)
                self._import_chapters(book, chapters)

            # save attachments and tyles
            self._import_attachments(book, self.dfile.document)
            self._import_styles(book)
            self.dfile.close()

            self._check_for_elements()

            # trigger signal depending on the import mode
            # TODO: allow attaching user as sender on `book_imported` signal
            if self.is_chapter_mode:
                chapter_imported.send(sender=(self.user or self), chapter=self.chapter)
            else:
                book_imported.send(sender=self, book=book)

        except zipfile.BadZipfile:
            notif_msg = _("The file could not be imported because it was not saved in the .docx format. Try to open the file in Word and save it as a .docx.")  # noqa
            self.notifier.error(notif_msg)
        except Exception as err:
            err_msg = _("The docx file you uploaded contains errors and cannot be converted. Please contact customer support.")  # noqa
            self.notifier.error(err_msg)
            logger.exception("Error trying to import docx file. Msg: %s" % err)

    def _import_styles(self, book):
        from django.conf import settings

        options = {}

        if hasattr(self.dfile.document, 'base_font_size') and \
           self.dfile.document.base_font_size != -1:
            options['scale_to_size'] = self.dfile.document.base_font_size
        elif len(self.dfile.document.possible_text) > 0:
            options['scale_to_size'] = self.dfile.document.possible_text[-1]

        editor_style = serialize.serialize_styles(
            self.dfile.document, prefix='#contenteditor', options=options)

        epub_style = serialize.serialize_styles(
            self.dfile.document, prefix='', options=options)

        dir_name = '{}/styles/{}/'.format(settings.DATA_ROOT, book.url_title)

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        f = open('{}/editor_style.css'.format(dir_name), 'wt')
        f.write(STYLE_EDITOR)
        f.write(editor_style)
        f.close()

        f = open('{}/epub_style.css'.format(dir_name), 'wt')
        f.write(STYLE_EPUB)
        f.write(epub_style)
        f.close()

    def _import_attachments(self, book, doc):
        default_status = get_default_book_status()
        stat = models.BookStatus.objects.filter(book=book, name=default_status)[0]

        unimportable_image = False
        not_supported = False

        for rel_id, rel_value in doc.relationships['document'].iteritems():
            if rel_value.get('type', '') == 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image':
                att = models.Attachment(book=book, version=book.version, status=stat)

                valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
                import_msg = _("The file format you uploaded is not supported. Please save the image as jpg file and upload it again.")  # noqa

                try:
                    with ContentFile(self.dfile.read_file(rel_value['target'])) as content_file:
                        att_name, att_ext = os.path.splitext(
                            os.path.basename(rel_value['target']))
                        original_ext = att_ext[:]

                        if att_ext.lower() in ['.tif', '.tiff']:
                            try:
                                content_file = docutils.convert_image('tiff', content_file)
                                self.converted_images.append(
                                    'static/{}{}'.format(rel_id, original_ext))

                                att_ext = '.png'
                            except:
                                # broken image
                                if not unimportable_image:
                                    self.notifier.warning(import_msg)
                                    unimportable_image = True

                                content_file = None

                        elif att_ext.lower() not in valid_extensions:
                            if not unimportable_image:
                                self.notifier.warning(import_msg)
                                unimportable_image = True

                            content_file = None

                        if content_file:
                            att.attachment.save('{}{}'.format(rel_id, att_ext), content_file, save=False)
                            att.save()
                        else:
                            if not not_supported:
                                self.notifier.warning(_("An error occurred while importing images. Some images couldn't be imported. Missing images are marked within the text. Please upload missing images manually."))  # noqa
                                not_supported = True

                            self.broken_images.append('static/{}{}'.format(rel_id, original_ext))

                            assets_dir = os.path.join(os.path.dirname(__file__), "assets/")
                            pholder_path = '{}placeholder_broken_img.jpg'.format(assets_dir)
                            data = open(pholder_path, 'rb').read()
                            content_file = ContentFile(data)

                            att.attachment.save('{}.jpg'.format(rel_id), content_file, save=False)
                            att.save()
                except Exception as err:
                    logger.exception("Exception while importing attachments. Msg: %s" % err)

    def _import_chapters(self, book, chapters):
        now = datetime.datetime.now()
        default_status = get_default_book_status()
        stat = models.BookStatus.objects.filter(book=book, name=default_status)[0]
        n = 100

        for chapter_title, chapter_content in chapters:
            if len(chapter_title) > 100:
                chapter_title = u'{}...'.format(chapter_title[:100])

            if chapter_title == '':
                chapter_title = _('Title Page') if n == 100 else _('Title')

            chapter_n = 0
            possible_title = chapter_title

            while True:
                does_exists = models.Chapter.objects.filter(
                    book=book, version=book.version,
                    url_title=booktype_slugify(possible_title)
                ).exists()

                if does_exists:
                    chapter_n += 1
                    possible_title = u'{} - {}'.format(chapter_title, chapter_n)
                else:
                    break

            if chapter_content[6:-8].strip() == '':
                continue

            _content = self._parse_chapter(chapter_content)
            try:
                chapter_content = unidecode(_content)[6:-8]
            except UnicodeDecodeError:
                chapter_content = _content.decode('utf-8', errors='ignore')[6:-8]
            except Exception as err:
                chapter_content = 'Error parsing chapter content'
                logger.exception("Error while decoding chapter content {0}".format(err))

            chapter = models.Chapter(
                    book=book,
                    version=book.version,
                    url_title=booktype_slugify(possible_title),
                    title=possible_title,
                    status=stat,
                    content=chapter_content,
                    created=now,
                    modified=now
                )
            chapter.save()

            toc_item = models.BookToc(
                    book=book,
                    version=book.version,
                    name=chapter.title,
                    chapter=chapter,
                    weight=n,
                    typeof=1
                )
            toc_item.save()
            n -= 1

            self._save_history_records(book, chapter)

    def _save_history_records(self, book, chapter, kind='chapter_create'):
        """
        Save history records for chapter and book. It saves a revision of the chapter


        :Args:
          - book: `booki.edit.models.Book` Django model instance
          - chapter: `booki.edit.models.Chapter` Django model instance
          - kind: `str` the chapter history type. See booki.editor.models.HISTORY_CHOICES

        """

        rev = chapter.revision

        if kind != 'chapter_create':
            rev = chapter.revision + 1

        # time to save revisions correctly
        user = self.user or book.owner
        history = logChapterHistory(
                chapter=chapter,
                content=chapter.content,
                user=user,
                comment='',
                revision=rev
            )

        if history:
            logBookHistory(
                book=book,
                version=book.version,
                chapter=chapter,
                chapter_history=history,
                user=user,
                kind=kind
            )

    def _import_single_chapter(self, chapter, content, process_mode):
        """
        Cleans and parse the given docx content in lxml node tree mode
        and will import into a existing chapter registered on the database

        :Args:
          - chapter: (`booki.edit.models.Chapter`) Django model instance
          - content: (`str`) html content of the imported document
          - process_mode: (`str`) string indicating how to treat new content: overwrite or append

        """

        _content = self._parse_chapter(content)
        try:
            chapter_content = unidecode(_content)[6:-8]  # 6:-8 cause _parse_chapter returns from body tag as root
        except UnicodeDecodeError:
            chapter_content = _content.decode('utf-8', errors='ignore')[6:-8]
        except Exception as err:
            error_msg = "Error while decoding chapter content {0}".format(err)
            logger.exception(error_msg)
            self.notifier.errors(error_msg)
            return

        # let's save a revision before we merge contents
        self._save_history_records(chapter.book, self.chapter, kind='chapter_save')

        if process_mode == 'overwrite':
            chapter.content = chapter_content
        else:
            chapter_content = chapter.content + chapter_content
            chapter.content = self._fix_merged_content(chapter_content)

        chapter.save()

    def _fix_merged_content(self, content):
        """
        After concatenated content, we need to make sure the structure of chapter is correct.
        For example: endnotes should always go at the end of the chapter and fix endnotes references

        Args:
          - content (`str`) chapter's html string content
        """

        # there might be some cases where the html content of the chapter it's no fully clean
        # because of old importer class. Let's apply some cleanup just in case
        content = tidy_cleanup(content, **TidyPlugin.OPTIONS)[1]

        utf8_parser = html.HTMLParser(encoding='utf-8')
        tree = html.document_fromstring(content, parser=utf8_parser)

        # first we check if there are endnotes
        endnotes = tree.xpath('.//ol[@class="endnotes"]')
        if len(endnotes) == 0:
            return content

        # let's create a new final block of endnotes to merge them all
        endnotes_block = etree.SubElement(tree.find('body'), 'ol', {'class': 'endnotes'})
        idx_endnote = 1

        for note in tree.xpath('.//li[starts-with(@id, "endnote-")]'):
            key = note.get('id', '').replace('endnote-', '')

            # let's find the reference, otherwise we delete the endnote
            try:
                sup = tree.xpath('//sup[@data-id="{}"]'.format(key))[0]
            except IndexError:
                self.notifier.warning(_("Reference not found for endnote: {}").format(note.text))
                continue

            # make sure reference number is correct
            sup.text = '{}'.format(idx_endnote)
            idx_endnote += 1

            endnotes_block.append(note)

        # remove old endnotes block from content
        for oldblock in endnotes:
            oldblock.drop_tree()

        # let's use only body and its content
        return etree.tostring(tree.find('body'), encoding='utf-8', xml_declaration=False)

    def _fix_images_path(self, content):
        """
        Adjusts the path for images that come with the imported content
        to match with the Booktype images paths

        :Args:
          - content: lxml node tree with the parsed content

        """

        imgs = content.xpath('.//img')

        for _img in imgs:
            image_name = _img.get('src')
            att_name, att_ext = os.path.splitext(os.path.basename(image_name))

            if image_name in self.broken_images:
                _img.set('src', 'static/{}.jpg'.format(att_name))

            if image_name in self.converted_images:
                _img.set('src', 'static/{}.png'.format(att_name))

    def _fix_header_levels(self, tree):
        """
        Adjusts content header levels when it's not chapter_mode import
        In chapter_mode we want to keep original header tags
        """

        def _find(tag):
            return tree.xpath('//' + tag)

        headers = []
        for n in range(5):
            headers.append(_find('h{}'.format(n + 1)))

        # we start at level 1 because we want to keep
        # a second level of h1 tags as h1 body
        level = 1

        # if more than one H1 is found
        if len(headers[0]) > 1:
            for header in headers[0][1:]:
                header.tag = 'h{}'.format(level)
            level += 1

        for levels in headers[1:]:
            for header in levels:
                header.tag = 'h{}'.format(level)

            if levels:
                if level < 6:
                    level += 1

    def _clean_span_tags(self, tree):
        """
        After doc serializing a lot of unneccesary span tags are created within
        the content. They are neccesary at the moment of parsing content but
        at this point they're just garbage. Let's clean them out
        """

        for tag in tree.xpath('.//span'):
            class_name = tag.get('class', None)
            parent_class = tag.getparent().get('class', '')

            if not class_name or class_name in parent_class:
                tag.drop_tag()

    def _fix_p_styles(self, tree):
        """
        This is just to set adecuate classes to p tags according to current
        logic in Booktype: p.body-first and p.body
        """

        P_STYLES = config.get_configuration('DOCX_PARAGRAPH_STYLES_MAP', {})
        headers = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

        for p in tree.xpath(".//p"):
            # avoid fixing styles for already matched classes
            if p.get('class', '') in P_STYLES.values():
                continue

            prev = p.getprevious()
            classes = p.get('class', '')

            if prev is not None and prev.tag in headers:
                p.set('class', 'body-first %s' % classes)
            else:
                p.set('class', 'body %s' % classes)

    def _handle_endnotes(self, tree):
        """
        Parse endnotes from docx file and generates the right container for it
        """

        has_endnotes = False
        endnotes = None
        endnote_counter = 1

        for sup in tree.xpath('.//sup[@class="endnote"]'):
            key = sup.get('data-id', '')

            # below values were set in custom hooks endnotes and footnotes
            relation_id = sup.get('data-relation-id', '')
            relationship = sup.get('data-relationship', '')

            # continue if there is no key or relationship is not of interest here
            if key == '' or relationship != 'endnotes':
                continue

            sup.text = '{}'.format(endnote_counter)
            endnote_counter += 1
            note_content = None

            # extract self.dfile.document.{footnotes|endnotes} dict
            # notes_source_dict = getattr(self.dfile.document, relationship)
            notes_source_dict = self.dfile.document.endnotes
            if relation_id not in notes_source_dict.keys():
                continue

            note_element = notes_source_dict[relation_id]
            note_content = serialize.serialize_elements(
                self.dfile.document, note_element, {
                    'embed_styles': False,
                    'pretty_print': False,
                    'relationship': relationship
                })

            if note_content is not None:
                if not has_endnotes:
                    endnotes = etree.SubElement(tree.find('body'), 'ol', {'class': 'endnotes'})
                    has_endnotes = True

                parser = lxml.html.HTMLParser(
                    encoding='utf-8', remove_blank_text=True, remove_comments=True)
                note_tree = lxml.html.fragment_fromstring(
                    note_content, create_parent=True, parser=parser)

                li = etree.SubElement(endnotes, 'li', {'id': 'endnote-{}'.format(key)})
                for child in note_tree.find('div').getchildren():
                    li.append(child)

                # children are normally just one element which inside has more children
                # so in this case, we just drop_tag and keep content
                for x in li.getchildren():
                    x.drop_tag()
            else:
                pass  # FIXME: should we remove the sup tag?

    def _handle_footnotes(self, tree):
        """Just adds a warning for user to convert footnotes to endnotes in Word
        and then try again the import"""

        warn_msg = _("We do not support footnotes. Please use endnotes in Word file. Convert them in Word file and upload this file again.")  # noqa
        self.notifier.warning(warn_msg)

    def _parse_chapter(self, content):
        # TODO: add docstrings and improve logic

        utf8_parser = html.HTMLParser(encoding='utf-8')
        tree = html.document_fromstring(content, parser=utf8_parser)

        # Translators: Default chapter title when importing DOCX
        # files. In case title does not exists.
        translators_title = _('Title')

        h1_headers = tree.xpath('.//h1')

        if h1_headers:
            for h1 in h1_headers:
                if h1.text == 'Unknown':
                    h1.text = translators_title

        # we should fix headers levels according to BK-2254 criteria
        self._fix_header_levels(tree)

        # time to adjust the src attribute of images
        self._fix_images_path(tree)

        # let's do some clean out on the not necessary tags,
        # like span tags with no reason to be
        self._clean_span_tags(tree)

        # now we need to set body and body-first styles to paragraphs
        self._fix_p_styles(tree)

        # parse and fix endnotes
        self._handle_endnotes(tree)

        # footnes we just add a warning
        self._handle_footnotes(tree)

        # let's cleanout infoboxes a bit
        docutils.clean_infobox_content(tree)
        docutils.fix_citations(tree)

        return etree.tostring(tree.find('body'), encoding='utf-8', xml_declaration=False)
