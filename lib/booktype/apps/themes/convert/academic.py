import ebooklib
from lxml import etree

from django.template.loader import render_to_string

from booktype.apps.convert import plugin


class AcademicPDF(plugin.MPDFPlugin):
    def get_mpdf_config(self):
        return {
            'mirrorMargins': True,
            'useSubstitutions': False
        }

    def fix_content(self, content):
        headers = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

        for header in headers:
            for idx, h in enumerate(content.xpath('.//{}'.format(header))):
                if header == 'h1' and h.getprevious() is None:
                    h.set('class', 'chapter-{}'.format(header))
                else:
                    h.set('class', 'body-{}'.format(header))

        for quote in content.xpath(".//p[@class='quote']"):
            div = etree.Element('div', {'class': 'quote'})
            div1 = etree.Element('div', {'class': 'quote-before'})
            div1.text = '"'

            quote.tag = 'div'
            quote.set('class', 'quote-content')

            quote.addprevious(div)
            div.insert(0, div1)
            div.insert(1, quote)

        for idx, p in enumerate(content.xpath(".//p")):
            if p.get('class', '') != '':
                continue

            prev = p.getprevious()
            if prev is not None and prev.tag in headers:
                p.set('class', 'body-first')
            else:
                p.set('class', 'body')

        return content


class AcademicEPUB(plugin.ConversionPlugin):
    def post_convert(self, original_book, book, output_path):
        content = render_to_string(
            'themes/academic/frontmatter_epub.xhtml',
            self.convert._get_data(original_book)
        )

        item = ebooklib.epub.EpubHtml(
            uid='imprint',
            title='Title',
            file_name="Text/title_page.xhtml",
            content=content
        )

        book.add_item(item)
        book.spine.insert(1, item)

        toc_entry = ebooklib.epub.Link(
            href=item.file_name,
            title=item.title,
            uid=item.id)
        book.toc.insert(0, toc_entry)

__convert__ = {
    'mpdf': AcademicPDF,
    'screenpdf': AcademicPDF,
    'epub': AcademicEPUB
}
