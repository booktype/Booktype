import os
import ooxml
import zipfile
import datetime

from django.core.files.base import ContentFile
from django.utils.translation import ugettext as _

from booki.editor import models
from booki.utils.log import logChapterHistory, logBookHistory
from booktype.utils.misc import booktype_slugify
from booktype.importer.notifier import Notifier
from booktype.importer.delegate import Delegate

from ooxml import importer, serialize

from .utils import convert_image
from .styles import STYLE_EDITOR, STYLE_EPUB


class WordImporter(object):

    def __init__(self):
        self.notifier = Notifier()
        self.delegate = Delegate()

        # Attachment objects indexed by image file name
        self._attachments = {}
        # Chapter objects indexed by document file name
        self._chapters = {}

    def _check_for_elements(self):
        from ooxml import doc

        found_math = False
        found_footnote = False

        for elem in self.dfile.document.elements:
            if isinstance(elem, doc.Paragraph):
                for el in elem.elements:
                    if isinstance(el, doc.Math):
                        found_math = True

                    if isinstance(el, doc.Footnote):
                        found_footnote = True

        if found_math:
            # Translators: Warning during the DOCX import
            warn_msg = _('Note: When importing formulas have been found and highlighted in the text, which are not supported by many e-readers and easy editor.') # noqa
            self.notifier.warning(warn_msg)

        if found_footnote:
            # Translators: Warning during the DOCX import
            warn_msg = _('Note: When importing foot or endnotes were found, which are not yet supported by easy editor.') # noqa
            self.notifier.warning(warn_msg)

    def import_file(self, file_path, book, options=None):
        from ooxml import doc

        self.delegate.notifier = self.notifier
        self.broken_images = []
        self.converted_images = []

        def serialize_empty(ctx, document, elem, root):
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
                    doc.Footnote: serialize_empty
                }
            }

            chapters = importer.get_chapters(
                self.dfile.document, options=options,
                serialize_options=serialize_options
            )

            self._import_attachments(book, self.dfile.document)
            self._import_chapters(book, chapters)

            # get the styles
            self._import_styles(book)
            self.dfile.close()

            self._check_for_elements()
        except zipfile.BadZipfile:
            notif_msg = _('The file could not be imported because it was not saved in the .docx format. Try to open the file in Word and save it as a .docx.') # noqa
            self.notifier.error(notif_msg)
        except:
            err_msg = _('The docx file you uploaded contains errors and cannot be converted. Please contact customer support.') # noqa
            self.notifier.error(err_msg)

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
        stat = models.BookStatus.objects.filter(book=book, name="new")[0]

        unimportable_image = False

        for rel_id, rel_value in doc.relationships.iteritems():
            schema_url = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image' # noqa
            if rel_value['type'] == schema_url:
                att = models.Attachment(
                    book=book, version=book.version, status=stat)

                valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
                import_msg = _("Note: Some images couldn't be imported.")
                try:
                    target_file = self.dfile.read_file(rel_value['target'])
                    with ContentFile(target_file) as content_file:
                        att_name, att_ext = os.path.splitext(
                            os.path.basename(rel_value['target']))
                        original_ext = att_ext[:]

                        if att_ext.lower() in ['.tif', '.tiff']:
                            try:
                                content_file = convert_image(
                                    'tiff', content_file)
                                self.converted_images.append(
                                    'static/{}{}'.format(rel_id, original_ext))

                                att_ext = '.png'
                            except:
                                if not unimportable_image:
                                    self.notifier.warning(import_msg)
                                    unimportable_image = True

                                content_file = None
                                # broken image
                        elif att_ext.lower() not in valid_extensions:
                            if not unimportable_image:
                                self.notifier.warning(import_msg)
                                unimportable_image = True
                            content_file = None

                        if content_file:
                            att.attachment.save('{}{}'.format(
                                rel_id, att_ext), content_file, save=False)
                            att.save()
                        else:
                            self.broken_images.append(
                                'static/{}{}'.format(rel_id, original_ext))

                            assets_dir = os.path.join(
                                os.path.dirname(__file__), "assets/")
                            data = open(
                                '{}placeholder_broken_img.jpg'.format(
                                    assets_dir), 'rb').read()
                            content_file = ContentFile(data)

                            att.attachment.save(
                                '{}.jpg'.format(rel_id),
                                content_file,
                                save=False
                            )
                            att.save()
                except:
                    pass

    def _import_chapters(self, book, chapters):
        now = datetime.datetime.now()
        stat = models.BookStatus.objects.filter(book=book, name="new")[0]
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

            chapter_content = self._parse_chapter(chapter_content)

            chapter = models.Chapter(
                book=book,
                version=book.version,
                url_title=booktype_slugify(possible_title),
                title=possible_title,
                status=stat,
                content=chapter_content[6:-8],
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

        return etree.tostring(
            tree, pretty_print=True, encoding="utf-8", xml_declaration=False)
