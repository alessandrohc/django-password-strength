"""Rendering contract of the three widgets.

These assert the markup each widget is responsible for emitting, which is what pins
the widget API down across Django versions: `Widget.render`, `Widget.build_attrs` and
`PasswordInput.get_context` are the three framework hooks the package overrides or
depends on, and a signature change in any of them shows up here as a failure.
"""
import re

import pytest

from django_password_strength.validators import PolicyMinLengthValidator
from django_password_strength.widgets import (
    PasswordConfirmationInput,
    PasswordInputBase,
    PasswordInputCompat,
    PasswordMutedInput,
    PasswordStrengthInput,
)

ALL_WIDGETS = [PasswordStrengthInput, PasswordMutedInput, PasswordConfirmationInput]


def input_tag(html):
    """Just the `<input>` element, so assertions about the field itself are not
    satisfied by a coincidental match in the surrounding markup or script block."""
    match = re.search(r'<input[^>]*>', html)
    assert match, f'no <input> found in: {html!r}'
    return match.group(0)


class TestPasswordStrengthInput:
    def test_renders_bar_input_info_and_rules(self, attrs):
        html = PasswordStrengthInput().render('passphrase', None, attrs)

        assert 'password_strength_bar_wrap' in html
        assert '<input type="password"' in html
        assert 'password_strength_info' in html
        assert 'password_strength_rules' in html

    def test_input_carries_the_strength_class(self, attrs):
        html = PasswordStrengthInput().render('passphrase', None, attrs)

        assert 'password_strength' in html
        # The class lands on the input itself, not only on the surrounding markup.
        assert 'class="password_strength"' in html

    def test_never_echoes_the_submitted_password(self, attrs):
        """`render_value` defaults to False -- PasswordInput.get_context drops it."""
        html = PasswordStrengthInput().render('passphrase', 'sup3r-s3cret', attrs)

        assert 'sup3r-s3cret' not in html

    def test_show_progressbar_info_false_drops_the_crack_time_paragraph(self, attrs):
        widget = PasswordStrengthInput()
        widget.attrs['show_progressbar_info'] = False

        html = widget.render('passphrase', None, attrs)

        assert 'password_strength_bar_wrap' in html
        assert 'password_strength_info' not in html

    def test_defaults_autocomplete_to_new_password(self, attrs):
        html = PasswordStrengthInput().render('passphrase', None, attrs)

        assert 'autocomplete="new-password"' in html

    def test_caller_supplied_autocomplete_wins(self, attrs):
        attrs['autocomplete'] = 'current-password'

        html = PasswordStrengthInput().render('passphrase', None, attrs)

        assert 'autocomplete="current-password"' in html
        assert 'new-password' not in html

    def test_rules_script_targets_the_field_id(self, attrs):
        html = PasswordStrengthInput().render('passphrase', None, attrs)

        # The generated script hooks the element by auto id; losing `id` from the
        # attrs that reach the template silently disables the client-side rules.
        assert '$("#id_passphrase")' in html

    def test_validators_are_serialised_into_the_rules_script(self, attrs):
        widget = PasswordStrengthInput()
        widget.attrs['validators'] = [PolicyMinLengthValidator(8).js_requirement()]

        html = widget.render('passphrase', None, attrs)

        assert '"minlength"' in html
        assert '"minLength": 8' in html

    def test_validators_defaults_reaches_the_rules_script(self, attrs):
        widget = PasswordStrengthInput()
        widget.attrs['validators_defaults'] = False

        html = widget.render('passphrase', None, attrs)

        assert 'defaults: false' in html

    def test_media_bundles_zxcvbn_and_the_stylesheet(self):
        media = str(PasswordStrengthInput().media)

        assert 'django_password_strength/js/zxcvbn.js' in media
        assert 'django_password_strength/js/password-strength.js' in media
        assert 'django_password_strength/css/password-strength.css' in media


class TestPasswordMutedInput:
    def test_renders_input_and_rules_without_the_progressbar(self, attrs):
        html = PasswordMutedInput().render('passphrase', None, attrs)

        assert '<input type="password"' in html
        assert 'password_strength_rules' in html
        # This is the whole point of the muted variant.
        assert 'password_strength_bar_wrap' not in html
        assert 'password_strength_info' not in html

    def test_defaults_autocomplete_to_new_password(self, attrs):
        html = PasswordMutedInput().render('passphrase', None, attrs)

        assert 'autocomplete="new-password"' in html

    def test_media_omits_zxcvbn(self):
        """No strength meter means no need to ship the estimator."""
        media = str(PasswordMutedInput().media)

        assert 'zxcvbn' not in media
        assert 'django_password_strength/js/password-requirements.js' in media


class TestPasswordConfirmationInput:
    def test_renders_input_and_the_mismatch_warning(self, attrs):
        html = PasswordConfirmationInput().render('confirm', None, attrs)

        assert '<input type="password"' in html
        assert 'password_strength_info' in html

    def test_input_carries_the_confirmation_class(self, attrs):
        html = PasswordConfirmationInput().render('confirm', None, attrs)

        assert 'class="password_confirmation"' in html

    def test_confirm_with_becomes_the_data_attribute(self, attrs):
        widget = PasswordConfirmationInput(confirm_with='passphrase')

        html = widget.render('confirm', None, attrs)

        assert 'data-confirm-with="id_passphrase"' in html

    def test_without_confirm_with_no_data_attribute_is_emitted(self, attrs):
        html = PasswordConfirmationInput().render('confirm', None, attrs)

        assert 'data-confirm-with' not in html

    def test_never_echoes_the_submitted_password(self, attrs):
        html = PasswordConfirmationInput().render('confirm', 'sup3r-s3cret', attrs)

        assert 'sup3r-s3cret' not in html


class TestConfigurationIsNotHtml:
    """`PasswordField` stores policy configuration on `widget.attrs` alongside real HTML
    attributes. It has to be stripped before the attrs become an `<input>`, or the page
    ends up with a serialised validator list in its markup."""

    def test_configuration_keys_never_reach_the_input(self, attrs):
        widget = PasswordStrengthInput()
        widget.attrs['validators'] = [PolicyMinLengthValidator(8).js_requirement()]
        widget.attrs['validators_defaults'] = False
        widget.attrs['show_progressbar_info'] = True

        tag = input_tag(widget.render('passphrase', None, attrs))

        assert 'validators' not in tag
        assert 'validators_defaults' not in tag
        assert 'show_progressbar_info' not in tag

    def test_configuration_still_drives_the_markup(self, attrs):
        """Stripping must happen on the way to the HTML, not before the markup is built."""
        widget = PasswordStrengthInput()
        widget.attrs['validators'] = [PolicyMinLengthValidator(8).js_requirement()]

        html = widget.render('passphrase', None, attrs)

        assert '"minLength": 8' in html

    def test_real_html_attributes_are_preserved(self, attrs):
        widget = PasswordStrengthInput()
        widget.attrs['data-testid'] = 'passphrase-field'

        tag = input_tag(widget.render('passphrase', None, attrs))

        assert 'data-testid="passphrase-field"' in tag


class TestRenderIsRepeatable:
    """A widget instance must survive being rendered more than once.

    Django deepcopies `base_fields` per form instance, so each form gets its own widget.
    A single bound field rendered twice in one template does not: it hits the same
    instance, which used to consume its own configuration on the first pass.
    """

    def test_policy_survives_a_second_render(self, attrs):
        widget = PasswordStrengthInput()
        widget.attrs['validators'] = [PolicyMinLengthValidator(8).js_requirement()]

        first = widget.render('passphrase', None, dict(attrs))
        second = widget.render('passphrase', None, dict(attrs))

        assert '"minLength": 8' in first
        assert '"minLength": 8' in second

    def test_progressbar_info_flag_survives_a_second_render(self, attrs):
        widget = PasswordStrengthInput()
        widget.attrs['show_progressbar_info'] = False

        widget.render('passphrase', None, dict(attrs))
        second = widget.render('passphrase', None, dict(attrs))

        assert 'password_strength_info' not in second

    @pytest.mark.parametrize(
        'widget_class,css_class',
        [(PasswordStrengthInput, 'password_strength'),
         (PasswordConfirmationInput, 'password_confirmation')])
    def test_css_class_is_not_duplicated(self, widget_class, css_class, attrs):
        widget = widget_class()

        widget.render('passphrase', None, dict(attrs))
        second = widget.render('passphrase', None, dict(attrs))

        assert input_tag(second).count(css_class) == 1


class TestCssClass:
    @pytest.mark.parametrize(
        'widget_class,css_class',
        [(PasswordStrengthInput, 'password_strength'),
         (PasswordConfirmationInput, 'password_confirmation')])
    def test_is_appended_to_a_caller_supplied_class(
            self, widget_class, css_class, attrs):
        """Crispy forms and the project's own templates set `form-control`; the widget
        adds to that rather than replacing it."""
        widget = widget_class()
        widget.attrs['class'] = 'form-control'

        tag = input_tag(widget.render('passphrase', None, attrs))

        assert 'form-control' in tag
        assert css_class in tag

    def test_the_muted_widget_adds_no_class(self, attrs):
        """It has no client-side strength behaviour to hook onto."""
        tag = input_tag(PasswordMutedInput().render('passphrase', None, attrs))

        assert 'class=' not in tag


class TestWidgetContract:
    """The parts of Django's widget API this package overrides or leans on."""

    @pytest.mark.parametrize('widget_class', ALL_WIDGETS)
    def test_attrs_is_optional(self, widget_class):
        """`Widget.render(self, name, value, attrs=None, renderer=None)` documents attrs
        as optional. BoundField always passes a dict, but nothing else has to."""
        html = widget_class().render('passphrase', None)

        assert '<input type="password"' in html

    @pytest.mark.parametrize('widget_class', ALL_WIDGETS)
    def test_the_callers_attrs_dict_is_not_mutated(self, widget_class):
        attrs = {'id': 'id_passphrase'}

        widget_class().render('passphrase', None, attrs)

        assert attrs == {'id': 'id_passphrase'}

    def test_build_attrs_is_djangos_own(self):
        """The Django < 1.11 compat shim is gone; this is the stock two-argument merge."""
        merged = PasswordStrengthInput().build_attrs({'id': 'x'}, {'class': 'y'})

        assert merged == {'id': 'x', 'class': 'y'}

    def test_the_compat_alias_still_resolves(self):
        """Kept so that an existing `PasswordInputCompat` import does not break."""
        assert PasswordInputCompat is PasswordInputBase
