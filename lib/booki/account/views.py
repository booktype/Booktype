from django.shortcuts import render_to_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect

from django.contrib.auth.decorators import login_required

from django import forms

# this should probahly just list all accounts

def view_accounts(request):
    return HttpResponse("AJME MENI", mimetype="text/plain")

# signout

def signout(request):
    from django.contrib import auth

    auth.logout(request)

    return HttpResponseRedirect("/")

# signin

def signin(request):
    from django.contrib import auth

    if(request.POST.has_key("username")):
        user = auth.authenticate(username=request.POST["username"], password=request.POST["password"])

        if user:
            auth.login(request, user)
            return HttpResponseRedirect("/accounts/%s/" % request.POST["username"])
    
    return HttpResponseRedirect("/")

# register user

def register(request):
    from django.contrib.auth.models import User
    from django.contrib import auth

    user = User.objects.create_user(username=request.POST["username"], 
                                    email=request.POST["email"],
                                    password=request.POST["password"])
    user.save()

    user2 = auth.authenticate(username=request.POST["username"], password=request.POST["password"])

    auth.login(request, user2)

    return HttpResponseRedirect("/accounts/%s/" % request.POST["username"])

# project form

class BookForm(forms.Form):
    title = forms.CharField(required=False)
    license = forms.ChoiceField(choices=(('1', '1'), ))

    def __init__(self, *args, **kwargs):
        super(BookForm, self).__init__(*args, **kwargs)

        from booki.editor import models
        self.fields['license'].initial = 'Unknown'
        self.fields['license'].choices = [ (elem.abbrevation, elem.name) for elem in models.License.objects.all().order_by("name")]


class ImportForm(forms.Form):
    archive_id = forms.CharField(required=False)


class ImportEpubForm(forms.Form):
    url = forms.CharField(required=False)
    

def view_profile(request, username):
    from django.contrib.auth.models import User
    from booki.editor import models

    from django.template.defaultfilters import slugify

    user = User.objects.get(username=username)

    if request.method == 'POST':
        project_form = BookForm(request.POST)
        import_form = ImportForm(request.POST)
        epub_form = ImportEpubForm(request.POST)
        espri_url = "http://objavi.flossmanuals.net/espri.cgi"

        if import_form.is_valid() and import_form.cleaned_data["archive_id"] != "":
            from booki.editor import common

            common.importBookFromURL(user, espri_url + "?mode=zip&book="+import_form.cleaned_data["archive_id"], createTOC = True)

        if epub_form.is_valid() and epub_form.cleaned_data["url"] != "":
            from booki.editor import common
            common.importBookFromURL(user, espri_url + "?mode=zip&url="+epub_form.cleaned_data["url"], createTOC = True)

        if project_form.is_valid() and project_form.cleaned_data["title"] != "":
            title = project_form.cleaned_data["title"]
            url_title = slugify(title)
            license   = project_form.cleaned_data["license"]


            import datetime
            # should check for errors
            lic = models.License.objects.get(abbrevation=license)

            book = models.Book(owner = request.user,
                                         url_title = url_title,
                                         title = title,
                                         license=lic,
                                         published = datetime.datetime.now())
            book.save()

            from booki.editor import common
            common.logBookHistory(book = book, 
                                  user = request.user,
                                  kind = 'book_create')
            
            status = models.BookStatus(book=book, name="not published",weight=0)
            status.save()
            book.status = status
            book.save()


            return HttpResponseRedirect("/accounts/%s/" % username)
    else:
        project_form = BookForm()
        import_form = ImportForm()
        epub_form = ImportEpubForm()

    books = models.Book.objects.filter(owner=request.user)
    
    groups = request.user.members.all()
    return render_to_response('account/view_profile.html', {"request": request, 
                                                            "user": user, 

                                                            "project_form": project_form, 
                                                            "import_form": import_form, 
                                                            "epub_form": epub_form, 

                                                            "books": books,
                                                            "groups": groups})

