"""Shared readers for the markup the widgets emit.

Both the widget tests and the form-level tests need to look at the rendered `<input>`
and at the policy it publishes, so the two readers live here rather than in either
module.
"""
import json
import re
from html import unescape


def input_tag(html):
    """Just the `<input>` element, so assertions about the field itself are not
    satisfied by a coincidental match in the surrounding markup."""
    match = re.search(r'<input[^>]*>', html)
    assert match, f'no <input> found in: {html!r}'
    return match.group(0)


def rules_payload(html):
    """The client-side policy, parsed back out of the `<input>`.

    Django escapes attribute values, so the JSON arrives HTML-encoded. Unescaping here
    is exactly what the browser's HTML parser does before `jQuery.fn.data` sees it --
    which is why callers assert against the decoded object instead of matching raw JSON
    substrings against the markup.
    """
    tag = input_tag(html)
    match = re.search(r'data-password-rules="([^"]*)"', tag)
    assert match, f'no data-password-rules on the input: {tag!r}'
    return json.loads(unescape(match.group(1)))
