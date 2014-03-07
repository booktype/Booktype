from django.utils.translation import ugettext_lazy as _

from booktype.apps.core.views import PageView


class FrontPageView(PageView):
    template_name = "portal/frontpage.html"
    page_title = _('Booktype') 
    title = _('Home')

    def get_context_data(self, **kwargs):
        context = super(FrontPageView, self).get_context_data(**kwargs)

        return context

