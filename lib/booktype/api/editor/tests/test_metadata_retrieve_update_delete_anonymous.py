import pytest
from faker import Faker

from rest_framework import status
from rest_framework.test import APIClient

from django.core.urlresolvers import reverse

fake = Faker()


@pytest.mark.django_db
class TestMetadataRetrieveUpdateDeleteAnonymous(object):
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

    def _create_metadata(self, book_id, user):
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(
            reverse("v1:editor_metadata_list_create_api", kwargs={'pk': book_id}),
            data={
                'name': 'DC.creator',
                'value_string': 'AUTHOR IS HERE'
            },
            format='json'
        )

        return response.data['id']

    @pytest.mark.usefixtures('assign_api_perms_registered_role')
    @pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
    def test_retrieve_metadata(self, registered_users):
        # create book and metadata
        book_id = self._create_book(registered_users['bob'])
        metadata_id = self._create_metadata(book_id, registered_users['bob'])

        # retrieve metadata
        client = APIClient()

        response = client.get(
            reverse("v1:editor_metadata_retrieve_update_destroy_api", kwargs={'book_id': book_id, 'pk': metadata_id})
        )

        assert response.status_code is status.HTTP_403_FORBIDDEN

    @pytest.mark.usefixtures('assign_api_perms_registered_role')
    @pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
    def test_update_metadata(self, registered_users):
        # create book and metadata
        book_id = self._create_book(registered_users['bob'])
        metadata_id = self._create_metadata(book_id, registered_users['bob'])

        # update metadata
        client = APIClient()

        response = client.patch(
            reverse("v1:editor_metadata_retrieve_update_destroy_api", kwargs={'book_id': book_id, 'pk': metadata_id}),
            data={'title': 'New title'}
        )

        assert response.status_code is status.HTTP_403_FORBIDDEN

    @pytest.mark.usefixtures('assign_api_perms_registered_role')
    @pytest.mark.parametrize('registered_users', [('bob',)], indirect=True)
    def test_delete_metadata(self, registered_users):
        # create book and metadata
        book_id = self._create_book(registered_users['bob'])
        metadata_id = self._create_metadata(book_id, registered_users['bob'])

        # delete metadata
        client = APIClient()

        response = client.patch(
            reverse("v1:editor_metadata_retrieve_update_destroy_api", kwargs={'book_id': book_id, 'pk': metadata_id}),
        )

        assert response.status_code is status.HTTP_403_FORBIDDEN
