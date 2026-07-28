"""Bundled catalogs: pt_BR and ru.

Two separate concerns here. First, that the catalogs actually resolve through Django's
translation machinery -- app-level `locale/` directories are only picked up for apps in
`INSTALLED_APPS`, so this doubles as a check that the package stays a proper Django app.
Second, that the committed `.mo` files match the `.po` sources, since only the binaries
are read at runtime and a stale pair fails silently by falling back to the msgid.
"""
import gettext
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from django.utils import translation

import django_password_strength

LOCALE_DIR = Path(django_password_strength.__file__).parent / 'locale'
PO_FILES = sorted(LOCALE_DIR.glob('*/LC_MESSAGES/*.po'))

needs_msgfmt = pytest.mark.skipif(
    shutil.which('msgfmt') is None,
    reason='gettext tooling not available to recompile the catalogs',
)


def test_the_expected_locales_are_shipped():
    assert {p.name for p in LOCALE_DIR.iterdir() if p.is_dir()} == {'pt_BR', 'ru'}


def test_po_files_were_found():
    """Guards the discovery above -- an empty glob would make the suite vacuous."""
    assert len(PO_FILES) == 4


@pytest.mark.parametrize('po', PO_FILES, ids=lambda p: f'{p.parts[-3]}/{p.stem}')
def test_every_po_has_a_compiled_mo(po):
    assert po.with_suffix('.mo').exists()


def _load_catalog(mo_path):
    with mo_path.open('rb') as handle:
        return gettext.GNUTranslations(handle)._catalog


def _messages(catalog):
    """Every translation, minus the metadata header stored under the empty msgid."""
    return {key: value for key, value in catalog.items() if key != ''}


def _plural_forms(catalog):
    """The one header field with runtime meaning: gettext compiles it into the plural
    selector when the catalog loads, so a stale rule picks the wrong plural form."""
    for line in catalog.get('', '').splitlines():
        if line.startswith('Plural-Forms:'):
            return line
    return None


@needs_msgfmt
@pytest.mark.parametrize('po', PO_FILES, ids=lambda p: f'{p.parts[-3]}/{p.stem}')
def test_compiled_mo_is_in_sync_with_its_po(po):
    """Recompile the source and compare translations -- not bytes, not the header.

    Bytes are out because msgfmt embeds a hash table whose layout varies between
    gettext builds. The header is out because it carries build metadata: gettext >= 0.19
    strips `POT-Creation-Date` for reproducibility, so a catalog compiled by an older
    msgfmt (the committed `ru` pair, from 2016) differs there while every message
    matches. `Plural-Forms` is asserted separately because it does affect runtime.
    """
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp) / 'fresh.mo'
        subprocess.run(
            ['msgfmt', '--output-file', str(fresh), str(po)],
            check=True, capture_output=True,
        )
        expected = _load_catalog(fresh)

    committed = _load_catalog(po.with_suffix('.mo'))

    assert _messages(committed) == _messages(expected)
    assert _plural_forms(committed) == _plural_forms(expected)


class TestBrazilianPortuguese:
    def test_validator_message_is_translated(self):
        from django_password_strength.validators import PolicyMinLengthValidator

        with translation.override('pt-br'):
            text = PolicyMinLengthValidator(8).js_requirement()['minlength']['text']

        assert text == 'Deve ter pelo menos minLength letra(s)'

    def test_widget_template_strings_are_translated(self, attrs):
        from django_password_strength.widgets import PasswordStrengthInput

        with translation.override('pt-br'):
            html = PasswordStrengthInput().render('passphrase', None, attrs)

        assert 'Atenção:' in html
        assert 'Essa senha levaria' in html

    def test_confirmation_warning_is_translated(self, attrs):
        from django_password_strength.widgets import PasswordConfirmationInput

        with translation.override('pt-br'):
            html = PasswordConfirmationInput().render('confirm', None, attrs)

        assert 'As duas senhas não combinam.' in html


class TestRussian:
    def test_warning_label_is_translated(self, attrs):
        """The catalog carried msgid "Warning" from when the string still lived in
        widgets.py, while the template emits "Warning:" -- so this one fell through to
        English until the msgid was realigned."""
        from django_password_strength.widgets import PasswordStrengthInput

        with translation.override('ru'):
            html = PasswordStrengthInput().render('passphrase', None, attrs)

        assert 'Внимание!' in html

    def test_confirmation_warning_is_translated(self, attrs):
        from django_password_strength.widgets import PasswordConfirmationInput

        with translation.override('ru'):
            html = PasswordConfirmationInput().render('confirm', None, attrs)

        assert 'Пароли не совпадают.' in html

    def test_crack_time_warning_is_translated(self, attrs):
        from django_password_strength.widgets import PasswordStrengthInput

        with translation.override('ru'):
            html = PasswordStrengthInput().render('passphrase', None, attrs)

        assert 'на взлом' in html


class TestEnglishFallback:
    def test_untranslated_language_falls_back_to_the_msgid(self, attrs):
        from django_password_strength.widgets import PasswordStrengthInput

        with translation.override('en'):
            html = PasswordStrengthInput().render('passphrase', None, attrs)

        assert 'Warning:' in html
