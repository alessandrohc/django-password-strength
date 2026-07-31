"""Rendering contract of the three widgets.

These assert the markup each widget is responsible for emitting, which is what pins
the widget API down across Django versions: `Widget.render`, `Widget.build_attrs` and
`PasswordInput.get_context` are the three framework hooks the package overrides or
depends on, and a signature change in any of them shows up here as a failure.
"""
import pytest

from django_password_strength.validators import (
    PolicyContainSpecialCharsValidator,
    PolicyMinLengthValidator,
)
from django_password_strength.widgets import (
    PasswordConfirmationInput,
    PasswordInputBase,
    PasswordInputCompat,
    PasswordMutedInput,
    PasswordStrengthInput,
)
from tests.helpers import input_tag, rules_payload

ALL_WIDGETS = [PasswordStrengthInput, PasswordMutedInput, PasswordConfirmationInput]

#: The widgets that publish a client-side policy. The confirmation widget has none.
RULES_WIDGETS = [PasswordStrengthInput, PasswordMutedInput]


class TestPasswordStrengthInput:
    def test_renders_bar_input_info_and_rules(self, attrs):
        html = PasswordStrengthInput().render('passphrase', None, attrs)

        assert 'password_strength_bar_wrap' in html
        assert '<input type="password"' in html
        assert 'password_strength_info' in html
        assert 'data-password-rules' in html

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

    def test_validators_are_serialised_into_the_payload(self, attrs):
        widget = PasswordStrengthInput()
        widget.attrs['validators'] = [PolicyMinLengthValidator(8).js_requirement()]

        payload = rules_payload(widget.render('passphrase', None, attrs))

        assert payload['rules']['minlength']['minLength'] == 8

    def test_validators_defaults_reaches_the_payload(self, attrs):
        widget = PasswordStrengthInput()
        widget.attrs['validators_defaults'] = False

        payload = rules_payload(widget.render('passphrase', None, attrs))

        assert payload['defaults'] is False

    def test_media_bundles_zxcvbn_and_the_stylesheet(self):
        media = str(PasswordStrengthInput().media)

        assert 'django_password_strength/js/zxcvbn.js' in media
        assert 'django_password_strength/js/password-strength.js' in media
        assert 'django_password_strength/css/password-strength.css' in media


class TestPasswordMutedInput:
    def test_renders_input_and_rules_without_the_progressbar(self, attrs):
        html = PasswordMutedInput().render('passphrase', None, attrs)

        assert '<input type="password"' in html
        assert 'data-password-rules' in html
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
        """Stripping must happen on the way to the HTML, not before the markup is built.

        The policy is read off the very attrs the keys are stripped from, so the order
        of those two steps is load-bearing: strip first and the payload comes out empty.
        """
        widget = PasswordStrengthInput()
        widget.attrs['validators'] = [PolicyMinLengthValidator(8).js_requirement()]

        payload = rules_payload(widget.render('passphrase', None, attrs))

        assert payload['rules']['minlength']['minLength'] == 8

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

        assert rules_payload(first)['rules']['minlength']['minLength'] == 8
        assert rules_payload(second)['rules']['minlength']['minLength'] == 8

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


class TestClientPolicyPayload:
    """The client-side policy travels on the `<input>` as data, never as inline script.

    It used to be emitted as a bare inline `<script>` defining a jQuery plugin. Under a
    Content-Security-Policy carrying `'strict-dynamic'` -- which cancels `'self'` for
    scripts, so "no nonce" means blocked -- that script never executed, and because the
    bundled initialiser guards on the plugin existing, the requirement popover simply
    never appeared, with nothing in the console but the CSP violation itself.

    An HTML attribute is not a script and cannot be blocked by any `script-src`, so
    these tests pin the payload to the input rather than to any nonce plumbing.
    """

    @pytest.mark.parametrize('widget_class', ALL_WIDGETS)
    def test_no_widget_emits_a_script_element(self, widget_class, attrs):
        html = widget_class().render('passphrase', None, attrs)

        assert '<script' not in html

    @pytest.mark.parametrize('widget_class', RULES_WIDGETS)
    def test_payload_is_valid_json_with_rules_and_defaults(self, widget_class, attrs):
        payload = rules_payload(widget_class().render('passphrase', None, attrs))

        # The two keys `PassRequirements` reads off its options argument.
        assert set(payload) == {'rules', 'defaults'}

    @pytest.mark.parametrize('widget_class', RULES_WIDGETS)
    def test_payload_defaults_to_the_builtin_rules(self, widget_class, attrs):
        """With no policy configured, the client falls back to its own default rules."""
        payload = rules_payload(widget_class().render('passphrase', None, attrs))

        assert payload['rules'] == {}
        assert payload['defaults'] is True

    def test_several_validators_merge_into_one_rules_object(self, attrs):
        """Each validator contributes a single requirement, keyed by its own name."""
        widget = PasswordStrengthInput()
        widget.attrs['validators'] = [
            PolicyMinLengthValidator(10).js_requirement(),
            PolicyContainSpecialCharsValidator(2).js_requirement(),
        ]

        payload = rules_payload(widget.render('passphrase', None, attrs))

        assert set(payload['rules']) == {'minlength', 'containSpecialChars'}
        assert payload['rules']['minlength']['minLength'] == 10
        assert payload['rules']['containSpecialChars']['minLength'] == 2

    def test_regex_requirements_survive_as_strings(self, attrs):
        """`PassRequirements` compiles a string `regex` itself, which is what makes the
        policy JSON-serialisable at all -- a compiled pattern could not cross the wire."""
        widget = PasswordStrengthInput()
        widget.attrs['validators'] = [
            PolicyContainSpecialCharsValidator(1).js_requirement()]

        rules = rules_payload(widget.render('passphrase', None, attrs))['rules']

        assert rules['containSpecialChars']['regex'] == '([^!%&@#$^*?_~])'
        assert rules['containSpecialChars']['regex_flags'] == 'g'

    def test_requirement_text_is_included_for_the_popover(self, attrs):
        widget = PasswordStrengthInput()
        widget.attrs['validators'] = [PolicyMinLengthValidator(8).js_requirement()]

        rules = rules_payload(widget.render('passphrase', None, attrs))['rules']

        assert rules['minlength']['text']

    def test_the_confirmation_widget_publishes_no_policy(self, attrs):
        """It has no requirement list of its own -- only the mismatch warning."""
        tag = input_tag(PasswordConfirmationInput().render('confirm', None, attrs))

        assert 'data-password-rules' not in tag

    def test_two_fields_get_independent_payloads(self, attrs):
        """Two password fields on one page must each carry their own policy.

        The inline script this replaced defined a single `$.fn.password_strength_rules`
        with the target id baked into its body, so every render overwrote the previous
        one: only the last field on the page kept a working popover.
        """
        strict = PasswordStrengthInput()
        strict.attrs['validators'] = [PolicyMinLengthValidator(12).js_requirement()]
        lax = PasswordStrengthInput()
        lax.attrs['validators'] = [PolicyMinLengthValidator(6).js_requirement()]

        first = strict.render('passphrase', None, {'id': 'id_passphrase'})
        second = lax.render('other', None, {'id': 'id_other'})

        assert rules_payload(first)['rules']['minlength']['minLength'] == 12
        assert rules_payload(second)['rules']['minlength']['minLength'] == 6


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
