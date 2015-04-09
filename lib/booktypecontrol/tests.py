from django.contrib.auth.models import User
from django.test import TestCase

from booki.editor.models import Book
from booktypecontrol.forms import BookRenameForm


class BookRenameFormTest(TestCase):
    def setUp(self):
        user = User.objects.create_user('zohan')
        self.book = Book.objects.create(
            title='Test Book',
            url_title='test_book',
            owner=user,
        )

    def test_valid_form(self):
        valid_form_data = {
            'title': 'Foo Book',
            'url_title': 'foo_book'
        }

        valid_form = BookRenameForm(data=valid_form_data,
                                    instance=self.book)
        self.assertTrue(valid_form.is_valid())

        valid_form.save()

        self.assertEqual(
            Book.objects.get(pk=valid_form.instance.pk).title,
            valid_form_data['title']
        )

    def test_invalid_form(self):
        invalid_form_data = {
            'title': '',
            'url_title': 'foo_book'
        }

        invalid_form = BookRenameForm(data=invalid_form_data)
        self.assertFalse(invalid_form.is_valid())
        self.assertEqual(
            invalid_form.errors,
            {
                'title': [u'Title is required.'],
            }
        )
