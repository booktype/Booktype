# -*- coding: utf-8 -*- 

from django.shortcuts import render

from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from booki.utils import log

from booki.editor import models

import os, tempfile


from django import forms

class UploadForm(forms.Form):
    title = forms.CharField(required=False, 
                            label='Book title', 
                            widget=forms.TextInput(attrs={'placeholder': 'Only if you want to rename it'}))
    file  = forms.FileField(required=True,
                            label='Your EPUB file')




from booktype.utils.misc import import_book_from_file

class ImporterView(FormView):
    template_name = 'importer/frontpage.html'
    form_class = UploadForm
    success_url = '/importer/'

    def form_valid(self, form):
        fil = self.request.FILES['file']

        f = open('/tmp/acika.epub', 'wb+')
        for chunk in fil.chunks():
            f.write(chunk)        
        f.close()

        import_book_from_file('/tmp/acika.epub', self.request.user)

        return super(ImporterView, self).form_valid(form)    

from django.db import transaction

#@transaction.commit_manually
def frontpage(request):
    from django.http import HttpResponseRedirect

    if request.method == 'POST': # If the form has been submitted...
        form = UploadForm(request.POST, request.FILES) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass

            fil = request.FILES['file']

            f = open('/tmp/acika.epub', 'wb+')
            for chunk in fil.chunks():
                f.write(chunk)        
            f.close()


            try:
                title = None
                if form.cleaned_data['title'].strip() != '':
                    title = form.cleaned_data['title']

                book = import_book_from_file('/tmp/acika.epub', request.user, book_title=title)
            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()

            from django.core.urlresolvers import reverse

            res = HttpResponseRedirect(reverse('reader:infopage', kwargs={'bookid': book.url_title})) # Redirect after POST

            return res


    else:
        form = UploadForm() # An unbound form    
#    try:
    resp =  render(request, 'importer/frontpage.html', {'request': request,
                                                            'form': form})
    # except:
    #     transaction.rollback()
    #     raise
    # else:
    #     transaction.commit()

    return resp
