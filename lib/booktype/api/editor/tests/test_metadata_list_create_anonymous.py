import pytest

from rest_framework import status
from rest_framework.test import APIClient

from django.core.urlresolvers import reverse


@pytest.mark.django_db
class TestMetadataListCreateAnonymous(object):
    def test_list_metadata_no_book(self):
        response = APIClient().get(
            reverse("v1:editor_metadata_list_create_api", kwargs={'pk': 1})
        )

        assert response.status_code is status.HTTP_403_FORBIDDEN

    def test_create_metadata_no_book(self):
        response = APIClient().post(
            reverse("v1:editor_metadata_list_create_api", kwargs={'pk': 1})
        )

        assert response.status_code is status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('books', [('First Book',)], indirect=True)
    def test_list_metadata(self, books):
        response = APIClient().get(
            reverse("v1:editor_metadata_list_create_api", kwargs={'pk': books[0].id})
        )

        assert response.status_code is status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('books', [('First Book',)], indirect=True)
    def test_metadata_chapter(self, books):
        response = APIClient().post(
            reverse("v1:editor_metadata_list_create_api", kwargs={'pk': books[0].id})
        )

        assert response.status_code is status.HTTP_403_FORBIDDEN
