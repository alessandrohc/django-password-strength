"""The `jsonify` filter.

No template in the package uses it any more -- the widgets serialise their policy in
Python and publish it as a data attribute. It stays part of the public template library
because a consuming project may well have loaded it, so it keeps its tests.
"""
from django.template import Context, Template

from django_password_strength.templatetags.djpassword_strength_tags import jsonify


def test_serialises_a_requirement_dict():
    assert jsonify({'minlength': {'minLength': 8}}) == '{"minlength": {"minLength": 8}}'


def test_serialises_booleans_as_json_not_python():
    """`defaults: True` would be a JavaScript syntax error."""
    assert jsonify(True) == 'true'
    assert jsonify(False) == 'false'


def test_serialises_an_empty_requirement_list():
    assert jsonify([]) == '[]'


def test_is_registered_as_a_template_filter():
    template = Template(
        '{% load djpassword_strength_tags %}{{ value|jsonify }}')

    assert template.render(Context({'value': [1, 2]})) == '[1, 2]'
