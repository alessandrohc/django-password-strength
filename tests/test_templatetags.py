"""The `jsonify` filter.

`strength-rules.html` pipes every requirement through `jsonify|safe` straight into a
`<script>` block, so this filter is the only thing standing between a policy dict and
executable page content.
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
