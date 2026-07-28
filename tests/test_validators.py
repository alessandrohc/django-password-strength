"""Policy validators.

Each validator is a `django.core.validators.BaseValidator` subclass, so it inherits
`__call__`'s clean/compare/raise cycle and the `%(limit_value)d` / `%(show_value)d`
interpolation. These tests pin both halves: the accept/reject decision and the
`js_requirement()` payload that feeds the client-side rules.
"""
import pytest
from django.core.exceptions import ValidationError

from django_password_strength.validators import (
    PolicyBaseValidator,
    PolicyContainLowercaseValidator,
    PolicyContainNumbersValidator,
    PolicyContainSpecialCharsValidator,
    PolicyContainUppercaseValidator,
    PolicyMinLengthValidator,
)

# validator class, limit, a password that passes, a password that fails
CASES = [
    (PolicyMinLengthValidator, 8, 'abcdefghij', 'abc'),
    (PolicyContainSpecialCharsValidator, 1, 'abc!def', 'abcdef'),
    (PolicyContainLowercaseValidator, 2, 'abcDEF', 'ABCDEF'),
    (PolicyContainUppercaseValidator, 2, 'ABCdef', 'abcdef'),
    (PolicyContainNumbersValidator, 2, 'abc12', 'abc1'),
]


@pytest.mark.parametrize('validator_class,limit,passing,failing', CASES)
def test_accepts_a_compliant_password(validator_class, limit, passing, failing):
    validator_class(limit)(passing)  # must not raise


@pytest.mark.parametrize('validator_class,limit,passing,failing', CASES)
def test_rejects_a_non_compliant_password(validator_class, limit, passing, failing):
    with pytest.raises(ValidationError):
        validator_class(limit)(failing)


@pytest.mark.parametrize('validator_class,limit,passing,failing', CASES)
def test_error_carries_the_declared_code(validator_class, limit, passing, failing):
    with pytest.raises(ValidationError) as exc:
        validator_class(limit)(failing)

    assert exc.value.code == validator_class.code


@pytest.mark.parametrize('validator_class,limit,passing,failing', CASES)
def test_error_message_interpolates_limit_and_actual(
        validator_class, limit, passing, failing):
    """`show_value` comes from `clean()`, so the message states what was measured."""
    with pytest.raises(ValidationError) as exc:
        validator_class(limit)(failing)

    message = exc.value.messages[0]
    assert str(limit) in message
    assert 'at least' in message


@pytest.mark.parametrize('validator_class,limit,passing,failing', CASES)
def test_js_requirement_exposes_the_limit(validator_class, limit, passing, failing):
    requirement = validator_class(limit).js_requirement()

    assert len(requirement) == 1
    (rule,) = requirement.values()
    assert rule['minLength'] == limit
    assert rule['text']


def test_min_length_counts_characters():
    assert PolicyMinLengthValidator(1).clean('abcd') == 4


def test_special_chars_counts_only_specials():
    assert PolicyContainSpecialCharsValidator(1).clean('ab!@') == 2


def test_numbers_counts_only_digits():
    assert PolicyContainNumbersValidator(1).clean('a1b2c3') == 3


def test_case_validators_count_per_case():
    assert PolicyContainLowercaseValidator(1).clean('aBcD') == 2
    assert PolicyContainUppercaseValidator(1).clean('aBcD') == 2


def test_base_validator_has_an_empty_requirement():
    """The base class contributes no client-side rule of its own."""
    assert PolicyBaseValidator(1).js_requirement() == {}


@pytest.mark.parametrize('validator_class,limit,passing,failing', CASES)
def test_every_policy_validator_is_a_policy_base_validator(
        validator_class, limit, passing, failing):
    """`PasswordField` collects requirements by isinstance check on this base."""
    assert isinstance(validator_class(limit), PolicyBaseValidator)
