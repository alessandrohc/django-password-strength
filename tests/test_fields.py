"""Form fields, including the whole-form path the consuming project actually uses.

`PasswordField` wires three things together: it picks a widget from `strength_view`,
turns the `*_length` keywords into policy validators, and copies each validator's
`js_requirement()` into `widget.attrs` so the rules script can be rendered. The form
level tests at the bottom mirror how the project declares these fields -- as class
attributes on a Form, which is the path that goes through Django's per-instance
`deepcopy` of `base_fields`.
"""
import pytest
from django import forms
from django.core.exceptions import ValidationError

from django_password_strength.fields import (
    PasswordConfirmationField,
    PasswordField,
)
from django_password_strength.validators import (
    PolicyContainLowercaseValidator,
    PolicyContainNumbersValidator,
    PolicyContainSpecialCharsValidator,
    PolicyContainUppercaseValidator,
    PolicyMinLengthValidator,
)
from django_password_strength.widgets import (
    PasswordConfirmationInput,
    PasswordMutedInput,
    PasswordStrengthInput,
)


class TestWidgetSelection:
    def test_defaults_to_the_strength_widget(self):
        assert isinstance(PasswordField().widget, PasswordStrengthInput)

    def test_strength_view_false_switches_to_the_muted_widget(self):
        field = PasswordField(strength_view=False)

        assert isinstance(field.widget, PasswordMutedInput)

    def test_an_explicit_widget_survives_strength_view_false(self):
        field = PasswordField(strength_view=False, widget=PasswordStrengthInput)

        assert isinstance(field.widget, PasswordStrengthInput)


class TestPolicyWiring:
    KEYWORD_TO_VALIDATOR = [
        ('min_length', PolicyMinLengthValidator),
        ('special_length', PolicyContainSpecialCharsValidator),
        ('lowercase_length', PolicyContainLowercaseValidator),
        ('uppercase_length', PolicyContainUppercaseValidator),
        ('numbers_length', PolicyContainNumbersValidator),
    ]

    @pytest.mark.parametrize('keyword,validator_class', KEYWORD_TO_VALIDATOR)
    def test_keyword_appends_its_validator(self, keyword, validator_class):
        field = PasswordField(**{keyword: 2})

        assert any(isinstance(v, validator_class) for v in field.validators)

    @pytest.mark.parametrize('keyword,validator_class', KEYWORD_TO_VALIDATOR)
    def test_omitting_the_keyword_appends_nothing(self, keyword, validator_class):
        field = PasswordField()

        assert not any(isinstance(v, validator_class) for v in field.validators)

    def test_min_length_is_enforced_on_clean(self):
        field = PasswordField(min_length=8)

        with pytest.raises(ValidationError):
            field.clean('abc')

    def test_a_compliant_password_cleans_through(self):
        field = PasswordField(min_length=8, numbers_length=1, uppercase_length=1)

        assert field.clean('Abcdefg1') == 'Abcdefg1'

    def test_min_length_does_not_also_install_charfields_own_validator(self):
        """CharField's `min_length` is deliberately suppressed in favour of the policy
        one, so a rejected password produces a single error, not two."""
        field = PasswordField(min_length=8)

        with pytest.raises(ValidationError) as exc:
            field.clean('abc')

        assert len(exc.value.messages) == 1

    def test_requirements_are_published_to_the_widget(self):
        field = PasswordField(min_length=8)

        requirements = field.widget.attrs['validators']

        assert {'minlength'} == set().union(*(r.keys() for r in requirements))

    def test_validators_defaults_is_published_to_the_widget(self):
        field = PasswordField(validators_defaults=False)

        assert field.widget.attrs['validators_defaults'] is False

    def test_show_progressbar_info_is_published_to_the_widget(self):
        field = PasswordField(show_progressbar_info=False)

        assert field.widget.attrs['show_progressbar_info'] is False


class TestPasswordConfirmationField:
    def test_defaults_to_the_confirmation_widget(self):
        assert isinstance(
            PasswordConfirmationField().widget, PasswordConfirmationInput)

    def test_confirm_with_becomes_a_widget_attr(self):
        field = PasswordConfirmationField(confirm_with='passphrase')

        assert field.widget.attrs['data-confirm-with'] == 'id_passphrase'

    def test_without_confirm_with_the_attr_is_absent(self):
        field = PasswordConfirmationField()

        assert 'data-confirm-with' not in field.widget.attrs


class SignupForm(forms.Form):
    """The shape the project declares: policy keywords straight off settings."""

    passphrase = PasswordField(
        min_length=8,
        numbers_length=1,
        uppercase_length=1,
        validators_defaults=False,
    )
    confirm_passphrase = PasswordConfirmationField(confirm_with='passphrase')


class TestFormIntegration:
    def test_bound_field_renders_the_full_strength_markup(self):
        html = str(SignupForm()['passphrase'])

        assert 'password_strength_bar_wrap' in html
        assert '$("#id_passphrase")' in html
        assert '"minLength": 8' in html
        assert 'defaults: false' in html

    def test_confirmation_field_points_back_at_the_password(self):
        html = str(SignupForm()['confirm_passphrase'])

        assert 'data-confirm-with="id_passphrase"' in html

    def test_form_media_bundles_the_widget_assets(self):
        media = str(SignupForm().media)

        assert 'zxcvbn.js' in media
        assert 'password-strength.css' in media

    def test_validation_rejects_a_weak_password(self):
        form = SignupForm(data={'passphrase': 'abc', 'confirm_passphrase': 'abc'})

        assert not form.is_valid()
        assert 'passphrase' in form.errors

    def test_validation_accepts_a_compliant_password(self):
        form = SignupForm(
            data={'passphrase': 'Abcdefg1', 'confirm_passphrase': 'Abcdefg1'})

        assert form.is_valid(), form.errors

    def test_two_form_instances_do_not_share_widget_state(self):
        """Django deepcopies `base_fields` per instance, so the policy that
        `render()` consumes off `widget.attrs` is restored for the next form."""
        first = str(SignupForm()['passphrase'])
        second = str(SignupForm()['passphrase'])

        assert '"minLength": 8' in first
        assert '"minLength": 8' in second

    def test_invalid_form_redisplay_keeps_the_policy(self):
        """The realistic re-render: a fresh form is built from POST data after a
        failed submit, and the rules script has to come back with it."""
        form = SignupForm(data={'passphrase': 'abc', 'confirm_passphrase': 'abc'})
        assert not form.is_valid()

        html = str(form['passphrase'])

        assert '"minLength": 8' in html
