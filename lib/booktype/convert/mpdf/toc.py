from django.utils.safestring import mark_safe

# hardcoded for now while we move to using depth provided
SECTION_LEVEL = 0
CHAPTER_LEVEL = 1


class TocItem(dict):
    """
    TocItem it's a dummy class to be rendered on mpdf body templates.
    They key of this dict based class is the render method, which depending
    on the type of the item, it will behave a bit different
    """

    _toc_entry_text = '<tocentry level="%(entry_level)s" content="%(title)s"></tocentry>'
    _section_text = '<h1 class="section">%(title)s</h1>'

    def _render_toc_entry(self, level):
        values = {'entry_level': level}
        values.update(self)
        return self._toc_entry_text % values

    def _render_section(self):
        return self._section_text % self

    def render(self):
        if 'type' not in self.keys():
            raise AttributeError("Provide item type before calling render method")

        item_type = self.get('type')
        show_in_toc = self.get('show_in_toc')
        is_chapter = item_type == 'chapter'
        level = CHAPTER_LEVEL if is_chapter else SECTION_LEVEL

        cnt = self.get('content', '')
        # in case it's a section, render h1 tag
        if not is_chapter:
            cnt = self._render_section()

        toc_entry = ''
        if show_in_toc:
            toc_entry = self._render_toc_entry(level)

        return mark_safe(toc_entry + cnt)
