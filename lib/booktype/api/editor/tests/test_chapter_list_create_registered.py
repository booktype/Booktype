import pytest
from faker import Faker

from rest_framework import status
from rest_framework.test import APIClient

from django.core.urlresolvers import reverse


fake = Faker()


@pytest.mark.django_db
class TestChapterListCreateRegisteredNoPermissions(object):
    @pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
    def test_list_chapters_no_book(self, registered_users):
        user_bob = registered_users['bob']

        client = APIClient()
        client.force_authenticate(user=user_bob)

        response = client.get(
            reverse("v1:editor_chapter_list_create_api", kwargs={'pk': 1})
        )

        assert response.status_code is status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
    def test_create_chapter_no_book(self, registered_users):
        user_bob = registered_users['bob']

        client = APIClient()
        client.force_authenticate(user=user_bob)

        response = client.post(
            reverse("v1:editor_chapter_list_create_api", kwargs={'pk': 1})
        )

        assert response.status_code is status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
    @pytest.mark.parametrize('books', [('Bobs book',)], indirect=True)
    def test_list_chapters_book_owner(self, registered_users, books):
        user_bob = registered_users['bob']
        book = books[0]
        book.owner = user_bob
        book.save()

        client = APIClient()
        client.force_authenticate(user=user_bob)

        response = client.get(
            reverse("v1:editor_chapter_list_create_api", kwargs={'pk': book.id})
        )

        assert response.status_code is status.HTTP_200_OK

    @pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
    def test_create_chapter_book_owner(self, registered_users):
        # create client
        client = APIClient()
        client.force_authenticate(user=registered_users['bob'])

        # create book via api
        book_title = fake.name()
        response = client.post(
            reverse("v1:book-list"),
            data={
                'title': book_title,
                'language_id': 1,
                'owner_id': registered_users['bob'].id
            }
        )

        assert response.status_code is status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.usefixtures('assign_api_perms_registered_role')
@pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
class TestChapterListCreateRegisteredWithPermissions(object):
    def test_list_chapters_no_book(self, registered_users):
        user_bob = registered_users['bob']

        client = APIClient()
        client.force_authenticate(user=user_bob)

        response = client.get(
            reverse("v1:editor_chapter_list_create_api", kwargs={'pk': 1})
        )

        assert response.status_code is status.HTTP_404_NOT_FOUND

    def test_create_chapter_no_book(self, registered_users):
        user_bob = registered_users['bob']

        client = APIClient()
        client.force_authenticate(user=user_bob)

        response = client.post(
            reverse("v1:editor_chapter_list_create_api", kwargs={'pk': 1}),
        )

        assert response.status_code is status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize('books', [('Bobs book', 'Jacks book')], indirect=True)
    def test_list_chapters(self, registered_users, books):
        user_bob = registered_users['bob']
        books[0].owner = user_bob

        client = APIClient()
        client.force_authenticate(user=user_bob)

        response = client.get(
            reverse("v1:editor_chapter_list_create_api", kwargs={'pk': books[0].id})
        )

        # we got 200 OK
        assert response.status_code is status.HTTP_200_OK
        # we don't have chapters yet
        assert response.data['count'] is 0

        # another book
        response = client.get(
            reverse("v1:editor_chapter_list_create_api", kwargs={'pk': books[1].id})
        )

        # we got 200 OK
        assert response.status_code is status.HTTP_200_OK
        # we don't have chapters yet
        assert response.data['count'] is 0

    def test_create_chapter_success(self, registered_users):
        # create client
        client = APIClient()
        client.force_authenticate(user=registered_users['bob'])

        # create book via api
        book_title = fake.name()
        response = client.post(
            reverse("v1:book-list"),
            data={
                'title': book_title,
                'language_id': 1,
                'owner_id': registered_users['bob'].id
            }
        )
        book_id = response.data['id']

        assert response.data['title'] == book_title

        # create chapter
        chapter_title = fake.name()
        response = client.post(
            reverse("v1:editor_chapter_list_create_api", kwargs={'pk': book_id}),
            data={'title': chapter_title}, format='json'
        )

        assert response.status_code is status.HTTP_201_CREATED
        assert response.data['title'] == chapter_title

        # get list of chapters
        response = client.get(
            reverse("v1:editor_chapter_list_create_api", kwargs={'pk': book_id})
        )

        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == chapter_title

    def test_create_chapter_fail(self, registered_users):
        # create client
        client = APIClient()
        client.force_authenticate(user=registered_users['bob'])

        # create book via api
        book_title = fake.name()
        response = client.post(
            reverse("v1:book-list"),
            data={
                'title': book_title,
                'language_id': 1,
                'owner_id': registered_users['bob'].id
            }
        )
        book_id = response.data['id']

        assert response.data['title'] == book_title

        # create chapter
        response = client.post(
            reverse("v1:editor_chapter_list_create_api", kwargs={'pk': book_id}),
        )

        assert response.status_code is status.HTTP_400_BAD_REQUEST

        chapter_title = fake.name()
        response = client.post(
            reverse("v1:editor_chapter_list_create_api", kwargs={'pk': book_id}),
            data={'asdasd': chapter_title}
        )

        assert response.status_code is status.HTTP_400_BAD_REQUEST
