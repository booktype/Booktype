import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User



class Command(BaseCommand):
    help = 'Shows users sign ups statistic per month'

    def _generate_months(self, first_month, first_year, end_month, end_year):
        """
        Creates generator with month, year walking
        :param first_month:
        :param first_year:
        :param end_month:
        :param end_year:
        :return: generator
        """
        month, year = first_month, first_year

        while True:
            yield month, year

            if (month, year) == (end_month, end_year):
                return

            month += 1
            if (month > 12):
                month = 1
                year += 1

    def handle(self, *args, **options):
        start = User.objects.all().order_by('date_joined').first().date_joined
        end = datetime.datetime.now()
        months_gen = self._generate_months(start.month, start.year, end.month, end.year)

        self.stdout.write(self.style.SUCCESS("#" * 73))
        self.stdout.write(self.style.SUCCESS("#" * 20 + " Monthly users sign up statistic " + "#" * 20))
        self.stdout.write(self.style.SUCCESS("#" * 73))

        for month, year in months_gen:
            sign_ups_count = User.objects.filter(date_joined__month=month, date_joined__year=year).count()

            self.stdout.write(self.style.WARNING('-' * 13))
            self.stdout.write(self.style.NOTICE("Date:") + self.style.SUCCESS('{}.{}'.format(month, year)))
            self.stdout.write(self.style.NOTICE("SignUps:") + self.style.SUCCESS(sign_ups_count))
