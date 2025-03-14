import django_webtest
import pytest
from django.contrib.contenttypes.models import ContentType
from passerelle.base.models import ApiUser, AccessRight

from passerelle_imio_ia_tech.models import imio_atal

# Doc for this project
# https://doc-publik.entrouvert.com/dev/developpement-d-un-connecteur/#Tests-unitaires
# https://git.entrouvert.org/entrouvert/passerelle/src/branch/main/tests/test_plone_restapi.py

SLUG_APP = imio_atal.get_connector_slug()
SLUG_CONNECTOR = "test"


@pytest.fixture
def app(request):
    """Create a Django test app."""
    app = django_webtest.DjangoTestApp()
    return app


@pytest.fixture
def connector(db):
    # création du connecteur et ouverture de la permission "can_access" sans authentification.
    connector = imio_atal.objects.create(
        slug=SLUG_CONNECTOR,
        base_url='https://demov6.imio-app.be',
        api_key="secret",
    )
    api = ApiUser.objects.create(username='all', keytype='', key='')
    obj_type = ContentType.objects.get_for_model(connector)
    AccessRight.objects.create(
            codename='can_access', apiuser=api,
            resource_type=obj_type, resource_pk=connector.pk)
    return connector

def test_third_parties(app, connector):
    """Test the get method."""
    res = app.get(f'/{SLUG_APP}/{SLUG_CONNECTOR}/third_parties')
    assert res.status_code == 200
