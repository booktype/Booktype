import os
import lxml
import uuid
import ooxml
import logging
import zipfile
import datetime
from unidecode import unidecode

from django.core.files.base import ContentFile
from django.utils.translation import ugettext as _

from booki.editor import models
from booki.utils.log import logChapterHistory, logBookHistory

from booktype.utils.misc import booktype_slugify, get_default_book_status
from booktype.importer.notifier import Notifier
from booktype.importer.delegate import Delegate

from ooxml import importer, serialize, doc

from .utils import convert_image
from .styles import STYLE_EDITOR, STYLE_EPUB

logger = logging.getLogger("booktype.importer.docx")


class WordImporter(object):

    def __init__(self):
        self.notifier = Notifier()
        self.delegate = Delegate()

        # Attachment objects indexed by image file name
        self._attachments = {}
        # Chapter objects indexed by document file name
        self._chapters = {}

        self.endnotes = {}
        self.footnotes = {}

    def _check_for_elements(self):
        from ooxml import doc

        found_math = False

        for elem in self.dfile.document.elements:
            if isinstance(elem, doc.Paragraph):
                for el in elem.elements:
                    if isinstance(el, doc.Math):
                        found_math = True

        if found_math:
            warn_msg = _("Please note: Mathematical formulae have been found, and highlighted in the text. These formulae are not supported by many e-readers, or the Booktype editor at present.")  # noqa
            self.notifier.warning(warn_msg)

    def import_file(self, file_path, book, options=None):
        self.delegate.notifier = self.notifier
        self.broken_images = []
        self.converted_images = []

        def serialize_empty(ctx, document, elem, root):
            return root

        def serialize_endnote(ctx, document, el, root):
            # <sup class="endnote" data-id="1454855960556">1</sup>

            if el.rid not in self.endnotes:
                data_id = str(uuid.uuid1()).replace('-', '')
                self.endnotes[el.rid] = data_id
            else:
                data_id = self.endnotes[el.rid]

            note = lxml.etree.SubElement(
                root, 'sup', {'class': 'endnote', 'data-id': data_id})
            note.text = '1'

            return root

        def serialize_footnote(ctx, document, el, root):
            # <sup class="endnote" data-id="1454855960556">1</sup>

            if el.rid not in self.footnotes:
                data_id = str(uuid.uuid1()).replace('-', '')
                self.footnotes[el.rid] = data_id
            else:
                data_id = self.footnotes[el.rid]

            note = lxml.etree.SubElement(
                root, 'sup', {'class': 'endnote', 'data-id': data_id})
            note.text = '1'

            return root

        if not options:
            options = {'scale_font_size': True}

        try:
            self.dfile = ooxml.read_from_file(file_path)

            serialize_options = {
                'embed_styles': True,
                'embed_fontsize': True,
                # 'empty_paragraph_as_nbsp': True,
                'serializers': {
                    doc.Math: serialize_empty,
                    doc.Footnote: serialize_footnote,
                    doc.Endnote: serialize_endnote
                }
            }

            chapters = importer.get_chapters(
                self.dfile.document, options=options,
                serialize_options=serialize_options)

            self._import_attachments(book, self.dfile.document)
            self._import_chapters(book, chapters)

            # get the styles
            self._import_styles(book)
            self.dfile.close()

            self._check_for_elements()
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
                                content_file = convert_image('tiff', content_file)
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
                if n == 100:
                    chapter_title = _('Title Page')
                else:
                    chapter_title = _('Title')

            chapter_n = 0
            possible_title = chapter_title

            while True:
                does_exists = models.Chapter.objects.filter(
                    book=book, version=book.version,
                    url_title=booktype_slugify(possible_title)
                ).exists()

                if does_exists:
                    chapter_n += 1
                    possible_title = u'{} - {}'.format(
                        chapter_title, chapter_n)
                else:
                    break

            if chapter_content[6:-8].strip() == '':
                continue

            _content = self._parse_chapter(chapter_content)
            try:
                chapter_content = unidecode(_content)[6:-8]
            except UnicodeDecodeError:
                chapter_content = self._parse_chapter(_content).decode('utf-8', errors='ignore')[6:-8]
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

            # time to save revisions correctly
            history = logChapterHistory(
                chapter=chapter,
                content=chapter.content,
                user=book.owner,
                comment='',
                revision=chapter.revision
            )

            if history:
                logBookHistory(
                    book=book,
                    version=book.version,
                    chapter=chapter,
                    chapter_history=history,
                    user=book.owner,
                    kind='chapter_create'
                )

    def _parse_chapter(self, content):
        def _find(tag):
            return tree.xpath('//' + tag)

        from lxml import html, etree

        utf8_parser = html.HTMLParser(encoding='utf-8')
        tree = html.document_fromstring(content, parser=utf8_parser)

        headers = []

        h1_headers = tree.xpath('.//h1')

        if h1_headers:
            for h1 in h1_headers:
                if h1.text == 'Unknown':
                    # Translators: Default chapter title when importing DOCX
                    # files. In case title does not exists.
                    h1.text = _('Title')

        for n in range(5):
            headers.append(_find('h{}'.format(n + 1)))

        level = 2

        if len(headers[0]) > 1:
            for header in headers[0][1:]:
                header.tag = 'h{}'.format(level)
            level += 1

        for levels in headers[1:]:
            has_changed = False

            for header in levels:
                header.tag = 'h{}'.format(level)

            if has_changed:
                if level < 6:
                    level += 1

        imgs = tree.xpath('.//img')

        for _img in imgs:
            image_name = _img.get('src')
            att_name, att_ext = os.path.splitext(os.path.basename(image_name))

            if image_name in self.broken_images:
                _img.set('src', 'static/{}.jpg'.format(att_name))

            if image_name in self.converted_images:
                _img.set('src', 'static/{}.png'.format(att_name))

        has_endnotes = False
        endnotes = None
        idx_endnote = 1

        for endnote in tree.xpath('.//sup[@class="endnote"]'):

            key = endnote.get('data-id', '')
            if key == '':
                continue

            endnote.text = '{}'.format(idx_endnote)
            idx_endnote += 1

            endnote_key = None
            footnote_key = None

            for k, v in self.endnotes.iteritems():
                if v == key:
                    endnote_key = k

            for k, v in self.footnotes.iteritems():
                if v == key:
                    footnote_key = k

            note_content = None

            if endnote_key:
                endnote = self.dfile.document.endnotes[endnote_key]
                note_content = serialize.serialize_elements(
                    self.dfile.document, endnote, {
                        'embed_styles': False, 'pretty_print': False,
                        'relationship': 'endnotes'
                    })

            if footnote_key:
                endnote = self.dfile.document.footnotes[footnote_key]
                note_content = serialize.serialize_elements(
                    self.dfile.document, endnote, {
                        'embed_styles': False, 'pretty_print': False,
                        'relationship': 'footnotes'
                    })

            if note_content is not None:
                if not has_endnotes:
                    endnotes = etree.SubElement(tree.find('body'), 'ol', {'class': 'endnotes'})
                    has_endnotes = True

                note_tree = lxml.html.fragment_fromstring(
                    note_content, create_parent=True,
                    parser=lxml.html.HTMLParser(
                        encoding='utf-8', remove_blank_text=True, remove_comments=True)
                )
                li = etree.SubElement(endnotes, 'li', {'id': 'endnote-{}'.format(key)})
                for child in note_tree.find('div').getchildren():
                    li.append(child)

        return etree.tostring(
            tree, pretty_print=True, encoding='utf-8', xml_declaration=False)
