import ebooklib

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
                h.set('class', 'body-{}'.format(header))

        for idx, p in enumerate(content.xpath(".//p")):            
            if p.getprevious().tag in headers:
                p.set('class', 'body-first')
            else:
                p.set('class', 'body')

        return content


class AcademicEPUB(plugin.ConversionPlugin):
    def post_convert(self, original_book, book, output_path):
        content = render_to_string('convert/academic_frontmatter_epub.xhtml',
            self.convert._get_data(original_book))

        item = ebooklib.epub.EpubHtml(
            uid = 'imprint',
            title = 'Title',
            file_name = "Text/title_page.xhtml",
            content   = content)

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
