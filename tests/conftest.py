import django
import pytest
from django.conf import settings


def pytest_configure():
    """Configure Django once, before the first ``django_password_strength`` import.

    The widgets build their markup with ``render_to_string``, so a Django Template
    Language engine with ``APP_DIRS`` has to be live: the four widget templates ship
    inside the app and rely on ``{% load i18n %}`` and
    ``{% load djpassword_strength_tags %}``, neither of which the Jinja2 backend can
    parse. ``django_password_strength`` itself must be installed for both the template
    loader and the app-level ``locale/`` catalogs to be discovered.
    """
    if settings.configured:
        return
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=[
            'django.contrib.staticfiles',
            'django_password_strength',
        ],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {},
        }],
        USE_I18N=True,
        USE_TZ=True,
        LANGUAGE_CODE='en',
        # Only the languages the package actually ships a catalog for, so that a
        # `translation.override` in the suite fails loudly instead of silently
        # falling back to the msgid.
        LANGUAGES=[
            ('en', 'English'),
            ('pt-br', 'Portuguese (Brazilian)'),
            ('ru', 'Russian'),
        ],
        STATIC_URL='/static/',
        SECRET_KEY='django-password-strength-test-suite',
    )
    django.setup()


# What Django's BoundField always hands to a widget: never None, always carrying the
# auto id. Tests take a fresh copy because `render()` mutates the dict it is given.
BOUND_FIELD_ATTRS = {'id': 'id_passphrase'}


@pytest.fixture
def attrs():
    """A throwaway copy of the attrs a BoundField would pass in."""
    return dict(BOUND_FIELD_ATTRS)
