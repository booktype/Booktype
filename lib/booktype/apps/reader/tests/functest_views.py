from django.test import TestCase
from django.core.urlresolvers import reverse

from booktype.apps.core.tests.factory_models import UserFactory, BookFactory, BookVersionFactory
from booktype.apps.core.tests.factory_models import ChapterFactory, BookTocFactory
from booktype.apps.core.tests.factory_models import PLAIN_USER_PASSWORD

class ReaderBaseTestCase(TestCase):
    """
    Base test case for Booktype with common utility functions
    """
    
    def setUp(self):
        """
        Sets common attributes for test classes
        """
        self.book = BookFactory()
        self.book.version = BookVersionFactory(book=self.book)
        self.book.save()
        self.user = self.book.owner
    
    def assertTrueMultiple(self, response, var_list=[]):
        """
        Checks if response contains multiples variables in context
        """
        for var_name in var_list:
            self.assertTrue(var_name in response.context)

    def reload_from_db(self, obj):
        """
        Returns reloaded attributes of a given object from the database
        """
        return obj.__class__.objects.get(pk=obj.id)


class InfoPageTest(ReaderBaseTestCase):

    def setUp(self):
        # call parent setUp method
        super(InfoPageTest, self).setUp()

        self.dispatcher = reverse('reader:infopage', args=[self.book.url_title])
        
        # list of variables to check in context
        self.vars_to_check = [
            'book_collaborators',
            'book_admins',
            'book_history',
            'book_group',
            'is_book_admin'
        ]

    def test_details_as_anonymous(self):
        response = self.client.get(self.dispatcher)

        # response status code should be 200
        self.assertEquals(response.status_code, 200)

        # check if context has been filled correctly
        self.assertTrueMultiple(response, self.vars_to_check)
        
        # check if anonymous user is book admin
        self.assertEquals(response.context['is_book_admin'], False)

        # check absence of some elements in template
        self.assertNotContains(response, 'Edit book info')
        self.assertNotContains(response, 'Delete Book')

    def test_details_as_owner_logged_in(self):
        # first login with book owner user
        self.client.login(
            username=self.user.username,
            password=PLAIN_USER_PASSWORD
        )

        response = self.client.get(self.dispatcher)

        # check status code
        self.assertEquals(response.status_code, 200)

        # check if context has been filled correctly
        self.assertTrueMultiple(response, self.vars_to_check)

        # owner is also book admin, so this should be True
        self.assertEquals(response.context['is_book_admin'], True)

        # check admin actions available in response
        self.assertContains(response, 'Edit book info')
        self.assertContains(response, 'Delete Book')

class EditBookInfoTest(ReaderBaseTestCase):
    
    def setUp(self):
        # call parent setUp method
        super(EditBookInfoTest, self).setUp()

        self.dispatcher = reverse('reader:edit_info_book', args=[self.book.url_title])

    def test_anon_user(self):
        response = self.client.get(self.dispatcher)

        # response status code should be 302, you're not logged in
        self.assertEquals(response.status_code, 302)

    def test_as_book_owner(self):
        # first login as book owner user
        self.client.login(
            username=self.user.username,
            password=PLAIN_USER_PASSWORD
        )

        # ---- GET method ----
        response = self.client.get(self.dispatcher)
        
        # response status code should be 200
        self.assertEquals(response.status_code, 200)

        # check if returning the right template
        self.assertTemplateUsed(response, "reader/book_info_edit.html")

        # check if book object is in context
        self.assertTrue('book' in response.context)

        # check some content in response
        self.assertContains(response, 'Book description')
        self.assertContains(response, 'Book image')

        # ---- POST method -----
        new_description = 'lorem ipsum testing'
        response = self.client.post(self.dispatcher, dict(description=new_description))

        # response status code should be 200
        self.assertEquals(response.status_code, 200)

        # test if description has been updated correctly
        updated_book = self.reload_from_db(self.book)
        self.assertTrue(updated_book.description == new_description)

        # in post method, the template must have changed
        self.assertTemplateUsed(response, "reader/book_info_edit_redirect.html")

class DeleteBookTest(EditBookInfoTest):
    # NOTE: Inheriting from EditBookInfoTest because we need first
    # if login required is working good (def test_anon_user). 
    # Then we need to override 'test_as_book_owner' method
    
    def setUp(self):
        # call parent's setUp method
        super(DeleteBookTest, self).setUp()

        self.dispatcher = reverse('reader:delete_book', args=[self.book.url_title])

    def test_as_not_owner(self):
        # first login as other user not owner or admin
        other_user = UserFactory()

        self.client.login(
            username=other_user.username,
            password=PLAIN_USER_PASSWORD
        )

        # ---- POST method -----        
        response = self.client.post(self.dispatcher, dict(title=self.book.title))

        # response status code should be 200
        self.assertEquals(response.status_code, 200)

        # template must be the delete_error_template, because user doesn't 
        # have enough rights to delete the book
        self.assertTemplateUsed(response, "reader/book_delete_error.html")

    def test_as_book_owner(self):
        # first login as book owner user
        self.client.login(
            username=self.user.username,
            password=PLAIN_USER_PASSWORD
        )

        # ---- GET method ----
        response = self.client.get(self.dispatcher)
        
        # response status code should be 200
        self.assertEquals(response.status_code, 200)

        # check if returning the right template
        self.assertTemplateUsed(response, "reader/book_delete.html")

        # check if content in response
        self.assertContains(response, 'Delete Book')

        # ---- POST method -----        
        response = self.client.post(self.dispatcher, dict(title=self.book.title))

        # response status code should be 200
        self.assertEquals(response.status_code, 200)

        # in post method, the template must have changed
        self.assertTemplateUsed(response, "reader/book_delete_redirect.html")

        # check if book registry is not in database anymore
        Book = self.book.__class__
        self.assertRaises(Book.DoesNotExist, Book.objects.get, pk=self.book.id)

class DraftChapterTest(ReaderBaseTestCase):
    
    def setUp(self):
        # call parent setUp method
        super(DraftChapterTest, self).setUp()
        self.chapter = ChapterFactory()
        self.dispatcher = reverse('reader:draft_chapter_page', args=[self.book.url_title])
        self.book_toc = BookTocFactory.create_toc(self.book, self.book.version, self.chapter)

        # list of variables to check in context
        self.vars_to_check = [
            'content',
            'toc_items',
            'book_version',
            'can_edit'
        ]

    def test_context_as_anon(self):
        response = self.client.get(self.dispatcher)

        # response status code should be 200
        self.assertEquals(response.status_code, 200)

        # as anonymous user you can't edit the book
        self.assertEquals(response.context['can_edit'], False)

        # test if context is well formed
        self.assertTrueMultiple(response, self.vars_to_check)

    def test_can_edit_logged_in(self):
        # first login as book owner user
        self.client.login(
            username=self.user.username,
            password=PLAIN_USER_PASSWORD
        )
        
        response = self.client.get(self.dispatcher)

        # as anonymous user you can't edit the book
        self.assertEquals(response.context['can_edit'], True)