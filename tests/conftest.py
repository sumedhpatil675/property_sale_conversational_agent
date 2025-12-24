import pytest
from django.conf import settings
import os

def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    os.environ["NINJA_SKIP_REGISTRY"] = "True"
    import django
    django.setup()

@pytest.fixture
def api_client():
    from ninja.testing import TestClient
    from agent.api import api
    return TestClient(api)

