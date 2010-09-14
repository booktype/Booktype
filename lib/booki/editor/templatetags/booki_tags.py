from django import template
from django.template.loader import render_to_string

register = template.Library()

###############################################################################################################

class FormatBookiNode(template.Node):
    def __init__(self, booki_data):
        self.booki_data = template.Variable(booki_data)

    def render(self, context):
        chapter =  self.booki_data.resolve(context)

#        t = template.loader.get_template('authors.html')
#        t = template.loader.get_template_from_string('{{ content.content|safe }}')
        content = chapter.content

        # this has to be put somewhere outside
        if content.find("##AUTHORS##") != -1:
            t = template.loader.get_template_from_string('{% load booki_tags %} {% booki_authors book %}')
            con =  t.render(template.Context(context, autoescape=context.autoescape))
            
            content = content.replace('##AUTHORS##', con)

        return content

#        t = template.loader.get_template_from_string('{% load booki_tags %} '+content)
#        return t.render(template.Context(context, autoescape=context.autoescape))
#        except template.VariableDoesNotExist:
#            return ' GRESKA '


@register.tag(name="booki_format")
def booki_format(parser, token):
    try:
        tag_name, booki_data = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]

    return FormatBookiNode(booki_data)



###############################################################################################################

class FormatAuthorsNode(template.Node):
    def __init__(self, book):
        self.book = template.Variable(book)

    def render(self, context):
        book =  self.book.resolve(context)

        t = template.loader.get_template('authors.html')

        from booki.editor import models
        from django.contrib.auth import models as auth_models

        chapters = []

        for chapter in models.BookToc.objects.filter(book=book).order_by("-weight"):
            if not chapter: continue
            if not chapter.chapter: continue
            aut = []
            jebem_ti_mater = []
            for us_id in models.ChapterHistory.objects.filter(chapter=chapter.chapter).distinct():
                if not us_id: continue

                usr = auth_models.User.objects.get(id=us_id.user.id)
                if usr.username not in jebem_ti_mater:
                    aut.append(usr)
                    jebem_ti_mater.append(usr.username)

            chapters.append({"authors": aut, "name": chapter.chapter.title})

#        for us_id in models.ChapterHistory.objects.filter(chapter__book=book).values("user").distinct().order_by("user__username"):
#            authors.append(auth_models.User.objects.get(id=us_id["user"]))

        return t.render(template.Context({'chapters': chapters }, autoescape=context.autoescape))


@register.tag(name="booki_authors")
def booki_authors(parser, token):
    """
    Django Tag. Shows list of authors for this book. Accepts one argument, book. Reads template authors.html.
    Needs a lot of work.

        {% load booki_tags %}
        {% booki_authors book %}
    """

    try:
        tag_name, book = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]

    return FormatAuthorsNode(book)
        
