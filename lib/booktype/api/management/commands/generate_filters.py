# -*- coding: utf-8 -*-

# SOURCE https://github.com/olegpshenichniy/django-filter-generation/
# README https://github.com/olegpshenichniy/django-filter-generation/blob/master/README.md

from django.core.management.base import BaseCommand
from django.core.management import CommandError

from django.apps import apps

from django.db.models.fields import (CharField, IntegerField, BigIntegerField,
                                     BooleanField, DateField, DateTimeField,
                                     TextField, TimeField, EmailField,
                                     DecimalField, FloatField, FilePathField,
                                     IPAddressField, PositiveIntegerField,
                                     PositiveSmallIntegerField, SlugField,
                                     SmallIntegerField, URLField)

from django.db.models.fields.related import ForeignKey


TEMPLATE = "\n    {name} = django_filters.{filter_type}Filter(" \
           "name='{attr_name}', " \
           "lookup_expr='{lookup_expr}')"

CHAR_ICONTAINS = {
    'types': [CharField, TextField, EmailField, FilePathField, IPAddressField,
              SlugField, URLField],
    'lookup_expr': 'icontains',
    'filter_type': 'Char'
}
NUMBER_EXACT = {
    'types': [ForeignKey],
    'lookup_expr': 'exact',
    'filter_type': 'Number'
}
NUMBER_MAX_MIN = {
    'types': [IntegerField, BigIntegerField, DecimalField, FloatField,
              PositiveIntegerField, PositiveSmallIntegerField, SmallIntegerField],
    'lookup_expr': {
        'min': 'gte',
        'max': 'lte'
    },
    'filter_type': 'Number'
}
BOOLEAN_EXACT = {
    'types': [BooleanField],
    'lookup_expr': 'exact',
    'filter_type': 'Boolean'
}
TIME_MAX_MIN = {
    'types': [TimeField],
    'lookup_expr': {
        'min': 'gte',
        'max': 'lte'
    },
    'filter_type': 'Time'
}
DATE_MAX_MIN = {
    'types': [DateField],
    'lookup_expr': {
        'min': 'gte',
        'max': 'lte'
    },
    'filter_type': 'Date'
}
DATE_TIME_MAX_MIN = {
    'types': [DateTimeField],
    'lookup_expr': {
        'min': 'gte',
        'max': 'lte'
    },
    'filter_type': 'DateTime'
}


class Command(BaseCommand):
    """
    Fast made command for automation generating django-filters class
    for provided app.Model
    """
    help = 'Generate filters class by provided app.Model'

    def add_arguments(self, parser):
        parser.add_argument('<app app ...>', nargs=1, type=str)

    def handle(self, *args, **options):
        if not options['<app app ...>'][0]:
            raise CommandError('Enter app.Model')

        app_name = options['<app app ...>'][0].split('.')[0]
        model_name = options['<app app ...>'][0].split('.')[1]

        model = apps.get_model(app_label=app_name, model_name=model_name)

        filters = []

        # add greeting message
        result = "###############################\n" \
                 "# FILTERS FOR '{0}' MODEL \n" \
                 "###############################" \
                 "\n\n".format(model.__name__)

        # add class name and extend django filters
        result += "class {0}Filter(django_filters.FilterSet):\n".format(
            model.__name__)

        # docs
        result += '    """\n    FILTERS FOR {0}.{1} MODEL \n    """'.format(
            app_name, model.__name__)

        # loop by modeld fields
        for attr in model._meta.fields[1:]:

            if attr.__class__ in CHAR_ICONTAINS['types']:
                filters.append(attr.name)
                result += TEMPLATE.format(
                    name=attr.name,
                    attr_name=attr.name,
                    filter_type=CHAR_ICONTAINS['filter_type'],
                    lookup_expr=CHAR_ICONTAINS['lookup_expr']
                )

            elif attr.__class__ in NUMBER_EXACT['types']:
                filters.append(attr.name)
                result += TEMPLATE.format(
                    name=attr.name,
                    attr_name=attr.name,
                    filter_type=NUMBER_EXACT['filter_type'],
                    lookup_expr=NUMBER_EXACT['lookup_expr'])

            elif attr.__class__ in NUMBER_MAX_MIN['types']:
                filters.append('max_{0}'.format(attr.name))
                result += TEMPLATE.format(
                    name='max_{0}'.format(attr.name),
                    attr_name=attr.name,
                    filter_type=NUMBER_MAX_MIN['filter_type'],
                    lookup_expr=NUMBER_MAX_MIN['lookup_expr']['max']
                )
                filters.append('min_{0}'.format(attr.name))
                result += TEMPLATE.format(
                    name='min_{0}'.format(attr.name),
                    attr_name=attr.name,
                    filter_type=NUMBER_MAX_MIN['filter_type'],
                    lookup_expr=NUMBER_MAX_MIN['lookup_expr']['min']
                )

            elif attr.__class__ in BOOLEAN_EXACT['types']:
                filters.append(attr.name)
                result += TEMPLATE.format(
                    name=attr.name,
                    attr_name=attr.name,
                    filter_type=BOOLEAN_EXACT['filter_type'],
                    lookup_expr=BOOLEAN_EXACT['lookup_expr'])

            elif attr.__class__ in BOOLEAN_EXACT['types']:
                filters.append(attr.name)
                result += TEMPLATE.format(
                    name=attr.name,
                    attr_name=attr.name,
                    filter_type=BOOLEAN_EXACT['filter_type'],
                    lookup_expr=BOOLEAN_EXACT['lookup_expr'])

            elif attr.__class__ in TIME_MAX_MIN['types']:
                filters.append('to_{0}'.format(attr.name))
                result += TEMPLATE.format(
                    name='to_{0}'.format(attr.name),
                    attr_name=attr.name,
                    filter_type=TIME_MAX_MIN['filter_type'],
                    lookup_expr=TIME_MAX_MIN['lookup_expr']['max']
                )
                filters.append('from_{0}'.format(attr.name))
                result += TEMPLATE.format(
                    name='from_{0}'.format(attr.name),
                    attr_name=attr.name,
                    filter_type=TIME_MAX_MIN['filter_type'],
                    lookup_expr=TIME_MAX_MIN['lookup_expr']['min']
                )

            elif attr.__class__ in DATE_MAX_MIN['types']:
                filters.append('to_{0}'.format(attr.name))
                result += TEMPLATE.format(
                    name='to_{0}'.format(attr.name),
                    attr_name=attr.name,
                    filter_type=DATE_MAX_MIN['filter_type'],
                    lookup_expr=DATE_MAX_MIN['lookup_expr']['max']
                )
                filters.append('from_{0}'.format(attr.name))
                result += TEMPLATE.format(
                    name='from_{0}'.format(attr.name),
                    attr_name=attr.name,
                    filter_type=DATE_MAX_MIN['filter_type'],
                    lookup_expr=DATE_MAX_MIN['lookup_expr']['min']
                )

            elif attr.__class__ in DATE_TIME_MAX_MIN['types']:
                filters.append('to_{0}'.format(attr.name))
                result += TEMPLATE.format(
                    name='to_{0}'.format(attr.name),
                    attr_name=attr.name,
                    filter_type=DATE_TIME_MAX_MIN['filter_type'],
                    lookup_expr=DATE_TIME_MAX_MIN['lookup_expr']['max']
                )
                filters.append('from_{0}'.format(attr.name))
                result += TEMPLATE.format(
                    name='from_{0}'.format(attr.name),
                    attr_name=attr.name,
                    filter_type=DATE_TIME_MAX_MIN['filter_type'],
                    lookup_expr=DATE_TIME_MAX_MIN['lookup_expr']['min']
                )

        # add meta
        result += "\n\n    " \
                  "class Meta:" \
                  "\n        model = {0}" \
                  "\n        fields = {1}\n".format(model.__name__, tuple(filters))

        print result
