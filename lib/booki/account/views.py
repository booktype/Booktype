from django.shortcuts import render_to_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
try:
    from django.core.validators import email_re
except:
    from django.forms.fields import email_re

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
    
    return HttpResponseRedirect("/?error=auth")

# register user

def register(request):
    from django.contrib.auth.models import User
    from django.contrib import auth
   
    #make GET string of returnable parameters
    #xxx probably should encode the values
    returnable_params="&username="+request.POST["username"]+"&email="+request.POST["email"]+"&fullname="+request.POST["fullname"]

    #username checks - first one check its not blank
    if request.POST["username"] == '':
	return HttpResponseRedirect("/?error=username"+returnable_params)
 
    #check the email is valid 
    if not bool(email_re.match(request.POST["email"])):
	return HttpResponseRedirect("/?error=email"+returnable_params)

    #check the password is the same as teh confirmation password, and that the password doesnt match the username
    if (not request.POST["password"] == request.POST["password2"]) or ( request.POST["password"] == request.POST["username"]) or len(request.POST["password"]) < 6:
	return HttpResponseRedirect("/?error=password"+returnable_params)

    #XXX fix me 
    #import crack
    # crack it
#   try:
#	crack.VeryFascistCheck(request.POST["password"])
#   except:
#	return HttpResponseRedirect("/?error=password")

    #check for non-blank full name
    if request.POST["fullname"] == '':
	return HttpResponseRedirect("/?error=fullname"+returnable_params)

    # Try to create a django user
    try:
    	user = User.objects.create_user(username=request.POST["username"], 
                                    email=request.POST["email"],
                                    password=request.POST["password"])
    except IntegrityError:
	#username already exists
	return HttpResponseRedirect("/?error=duplicate"+returnable_params)

    #
    #The checks for all the attributes are done
    #

    #set the django FIRST NAME to be the FULL NAME
    user.first_name = request.POST["fullname"]

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


## user settings

class SettingsForm(forms.Form):
    email = forms.EmailField(required=True)
    firstname = forms.CharField(required=True, label='First name')
    lastname = forms.CharField(required=True, label='Last name')
    description = forms.CharField(widget=forms.Textarea(), required=False, label="Blurb about yourself")

    image = forms.Field(widget=forms.FileInput(), required=False)

## user settings

def user_settings(request, username):
    from django.contrib.auth.models import User
    from booki.editor import models

    from django.template.defaultfilters import slugify

    user = User.objects.get(username=username)

    if request.method == 'POST':
        settings_form = SettingsForm(request.POST, request.FILES)
        if settings_form.is_valid():

            # this is very stupid and wrong 
            # change the way it works
            # make utils for
            #     - get image url
            #     - get image path
            #     - seperate storage for

            from django.core.files import File
            profile = user.get_profile()

            user.email      = settings_form.cleaned_data['email']
            user.first_name = settings_form.cleaned_data['firstname']
            user.last_name  = settings_form.cleaned_data['lastname']
            user.save()

            profile.description = settings_form.cleaned_data['description']

            if settings_form.cleaned_data['image']:
                import tempfile
                import os

                # check this later
                fh, fname = tempfile.mkstemp(suffix='', prefix='profile')

                f = open(fname, 'wb')
                for chunk in settings_form.cleaned_data['image'].chunks():
                    f.write(chunk)
                f.close()

                import Image

                im = Image.open(fname)
                im.thumbnail((120, 120), Image.NEAREST)
                imageName = '%s.jpg' % fname
                im.save(imageName)
                
                profile.image.save('%s.jpg' % user.username, File(file(imageName)))
                os.unlink(fname)
                

            profile.save()
        
            return HttpResponseRedirect("/accounts/%s/" % username)
    else:
        settings_form = SettingsForm(initial = {'image': 'aaa',
                                                'firstname': user.first_name,
                                                'lastname': user.last_name,
                                                'description': user.get_profile().description,
                                                'email': user.email})

    return render_to_response('account/user_settings.html', {"request": request, 
                                                             "user": user, 
                                                             
                                                             "settings_form": settings_form, 
                                                             })



def view_profilethumbnail(request, profileid):
    from django.http import HttpResponse
    from booki import settings
    
    from django.contrib.auth.models import User
    u = User.objects.get(username=profileid)

    # this should be a seperate function

    if not u.get_profile().image:
        name = '%s_profile_images/_anonymous.jpg' % settings.MEDIA_ROOT
    else:
        name =  u.get_profile().image.name

    import Image

    image = Image.open(name)
    image.thumbnail((24, 24), Image.NEAREST)

    # serialize to HTTP response
    response = HttpResponse(mimetype="image/jpg")
    image.save(response, "JPEG")
    return response
