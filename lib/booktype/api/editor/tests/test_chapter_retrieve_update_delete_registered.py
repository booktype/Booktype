import pytest
from faker import Faker

from rest_framework import status
from rest_framework.test import APIClient

from django.core.urlresolvers import reverse

fake = Faker()


@pytest.mark.django_db
class TestChapterRetrieveUpdateDeleteRegisteredNoPermissions(object):
    def _create_book(self, user):
        client = APIClient()
        client.force_authenticate(user=user)

        book_title = fake.name()
        response = client.post(
            reverse("v1:book-list"),
            data={
                'title': book_title,
                'language_id': 1,
                'owner_id': user.id
            }
        )
        return response.data['id']

    def _create_chapter(self, book_id, user):
        client = APIClient()
        client.force_authenticate(user=user)

        chapter_title = fake.name()
        response = client.post(
            reverse("v1:editor_chapter_list_create_api", kwargs={'pk': book_id}),
            data={'title': chapter_title}, format='json'
        )

        return response.data['id']

    @pytest.mark.parametrize('superusers', [('elvis',)], indirect=True)
    @pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
    def test_retrieve_chapter(self, superusers, registered_users):
        # create book and chapter
        book_id = self._create_book(superusers['elvis'])
        chapter_id = self._create_chapter(book_id, superusers['elvis'])

        # retrive chapter
        client = APIClient()
        client.force_authenticate(user=registered_users['bob'])

        response = client.get(
            reverse("v1:editor_chapter_retrieve_update_destroy_api", kwargs={'book_id': book_id, 'pk': chapter_id})
        )

        assert response.status_code is status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('superusers', [('elvis',)], indirect=True)
    @pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
    def test_retrieve_chapter(self, superusers, registered_users):
        # create book and chapter
        book_id = self._create_book(superusers['elvis'])
        chapter_id = self._create_chapter(book_id, superusers['elvis'])

        # update chapter
        client = APIClient()
        client.force_authenticate(user=registered_users['bob'])

        response = client.patch(
            reverse("v1:editor_chapter_retrieve_update_destroy_api", kwargs={'book_id': book_id, 'pk': chapter_id}),
            data={'title': fake.name()}
        )

        assert response.status_code is status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('superusers', [('elvis',)], indirect=True)
    @pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
    def test_delete_chapter(self, superusers, registered_users):
        # create book and chapter
        book_id = self._create_book(superusers['elvis'])
        chapter_id = self._create_chapter(book_id, superusers['elvis'])

        # delete chapter
        client = APIClient()
        client.force_authenticate(user=registered_users['bob'])

        response = client.delete(
            reverse("v1:editor_chapter_retrieve_update_destroy_api", kwargs={'book_id': book_id, 'pk': chapter_id}),
        )

        assert response.status_code is status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.usefixtures('assign_api_perms_registered_role')
class TestChapterRetrieveUpdateDeleteRegistered(object):
    def _create_book(self, user):
        client = APIClient()
        client.force_authenticate(user=user)

        book_title = fake.name()
        response = client.post(
            reverse("v1:"
                    "book-list"),
            data={
                'title': book_title,
                'language_id': 1,
                'owner_id': user.id
            }
        )
        return response.data['id']

    def _create_chapter(self, book_id, user):
        client = APIClient()
        client.force_authenticate(user=user)

        chapter_title = fake.name()
        response = client.post(
            reverse("v1:editor_chapter_list_create_api", kwargs={'pk': book_id}),
            data={'title': chapter_title}, format='json'
        )

        return response.data['id']

    @pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
    def test_retrieve_chapter(self, registered_users):
        # create book and chapter
        book_id = self._create_book(registered_users['bob'])
        chapter_id = self._create_chapter(book_id, registered_users['bob'])

        # retrive chapter
        client = APIClient()
        client.force_authenticate(user=registered_users['bob'])

        response = client.get(
            reverse("v1:editor_chapter_retrieve_update_destroy_api", kwargs={'book_id': book_id, 'pk': chapter_id})
        )

        assert response.status_code is status.HTTP_200_OK
        assert response.data['id'] == chapter_id

    @pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
    def test_update_chapter(self, registered_users):
        # create book and chapter
        book_id = self._create_book(registered_users['bob'])
        chapter_id = self._create_chapter(book_id, registered_users['bob'])

        # update chapter
        new_title = fake.century()
        client = APIClient()
        client.force_authenticate(user=registered_users['bob'])
        response = client.patch(
            reverse("v1:editor_chapter_retrieve_update_destroy_api", kwargs={'book_id': book_id, 'pk': chapter_id}),
            data={'title': new_title}
        )

        assert response.data['title'] == new_title
        assert response.status_code is status.HTTP_200_OK

    @pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
    def test_update_chapter_fail(self, registered_users):
        # create book and chapter
        book_id = self._create_book(registered_users['bob'])
        chapter_id = self._create_chapter(book_id, registered_users['bob'])

        # update chapter
        new_title = fake.century()
        client = APIClient()

        client.force_authenticate(user=registered_users['bob'])
        response = client.put(
            reverse("v1:editor_chapter_retrieve_update_destroy_api", kwargs={'book_id': book_id, 'pk': chapter_id}),
            data={'BLABLA': new_title}
        )

        assert response.status_code is status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
    def test_delete_chapter(self, registered_users):
        # create book and chapter
        book_id = self._create_book(registered_users['bob'])
        chapter_id = self._create_chapter(book_id, registered_users['bob'])

        # delete chapter
        client = APIClient()
        client.force_authenticate(user=registered_users['bob'])
        response = client.delete(
            reverse("v1:editor_chapter_retrieve_update_destroy_api", kwargs={'book_id': book_id, 'pk': chapter_id})
        )

        assert response.status_code is status.HTTP_204_NO_CONTENT

        # retrive chapter
        response = client.get(
            reverse("v1:editor_chapter_retrieve_update_destroy_api", kwargs={'book_id': book_id, 'pk': chapter_id})
        )

        assert response.status_code is status.HTTP_404_NOT_FOUND
