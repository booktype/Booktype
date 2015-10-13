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

        for idx, p in enumerate(content.xpath(".//p")):            
            if p.getprevious().tag in headers:
                p.set('class', 'body-first')
            else:
                p.set('class', 'body')

        return content


__convert__ = {
 'mpdf': CustomPDF,
 'screenpdf': CustomPDF
}
