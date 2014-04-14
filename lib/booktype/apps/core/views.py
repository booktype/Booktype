from django.views.generic import TemplateView

class BasePageView(object):
    page_title = ''
    title = ''
    
    def get_context_data(self, **kwargs):
        context = super(BasePageView, self).get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["title"] = self.title
        context["request"] = self.request

        return context

class PageView(BasePageView, TemplateView):
    pass