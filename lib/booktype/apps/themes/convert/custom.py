import lxml
from lxml import etree

from booktype.apps.convert import plugin


class CustomPDF(plugin.MPDFPlugin):
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


__convert__ = {
 'mpdf': CustomPDF,
 'screenpdf': CustomPDF
}
