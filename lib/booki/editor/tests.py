from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from booki.editor.models import Book


class BookRenameManagementCommandTest(TestCase):
    def test_command_error_raised_with_no_args(self):
        with self.assertRaises(CommandError):
            call_command('bookrename')

    def test_command_error_raised_book_does_not_exist(self):
        with self.assertRaises(CommandError):
            call_command(
                'bookrename',
                'The Island'
            )

    def test_command_error_raised_owner_does_not_exist(self):
        shadowman = User.objects.create_user('shadowman')
        book = Book.objects.create(title='The Island of Truth', owner=shadowman)

        with self.assertRaises(CommandError):
            call_command(
                'bookrename',
                book.url_title,
                owner='rochard'
            )

    def test_save_new_book_title(self):
        user = User.objects.create_user('rochard')
        book = Book.objects.create(
            title='The Island of Truth',
            owner=user,
            url_title='the_island_of_truth'
        )

        call_command(
            'bookrename',
            book.url_title,
            new_book_title='The Island'
        )

        book = Book.objects.get(id=book.id)
        self.assertEqual(book.title, 'The Island')

    def test_save_new_book_url(self):
        user = User.objects.create_user('rochard')
        book = Book.objects.create(
            title='The Island of Truth',
            owner=user,
            url_title='the_island_of_truth'
        )

        call_command(
            'bookrename',
            book.url_title,
            new_book_title='The Island',
            new_book_url='the_island'
        )

        book = Book.objects.get(id=book.id)
        self.assertEqual(book.title, 'The Island')
        self.assertEqual(book.url_title, 'the_island')
