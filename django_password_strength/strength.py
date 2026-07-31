"""Character statistics for the server-side password policy.

Absorbed from the ``password-strength`` distribution by Mark Vartanyan, whose upstream
(kolypto/py-password-strength) is archived: read-only since 2020, last released in 2019.
Keeping it as a dependency meant carrying an abandoned package for five counters, and its
2015 releases are published under version strings that are not PEP 440 -- so pip parses
filenames like ``password_strength-0.0.1_1-py2-none-any.whl`` off the index and now
rejects them.

Only what the validators actually read was taken: the five counters below and the two
category tallies they share. ``PasswordPolicy``, the test-registry metaclass and the
entropy/strength estimators were left behind, having no consumer here.

Retained under the original BSD licence -- see the notice in ``LICENSE.md``.
"""
import unicodedata
from collections import Counter
from functools import cached_property


class PasswordStats:
    """Counts of a password's characters, by unicode general category.

    Counting by category rather than with ``str.isupper()``/``str.isdigit()`` is what
    makes the counts meaningful for non-ASCII passwords, and it has consequences worth
    knowing before touching this: CJK and titlecase letters are neither uppercase nor
    lowercase; roman numerals and superscript digits are numbers; whitespace and
    combining marks are "special". See
    https://www.unicode.org/reports/tr44/#GC_Values_Table.

    Every counter is a cached property, so a password is walked at most twice regardless
    of how many counters a caller reads.
    """

    def __init__(self, password):
        # Coerced rather than required as text: the original accepted anything a caller
        # handed it, and a policy check is the wrong place to raise a type error.
        self.password = str(password)

    @cached_property
    def char_categories_detailed(self):
        """Character count per full unicode category, e.g. ``Counter({'Ll': 3})``.

        A ``Counter`` rather than a plain dict, so a missing category reads as 0 instead
        of raising -- which is what the counters below rely on.
        """
        return Counter(map(unicodedata.category, self.password))

    @cached_property
    def char_categories(self):
        """Character count per top-level category: L, M, N, P, S, Z, C."""
        totals = Counter()
        for category, count in self.char_categories_detailed.items():
            totals[category[0]] += count
        return totals

    def count_except(self, *categories):
        """Number of characters outside the given top-level categories."""
        return sum(count for category, count in self.char_categories.items()
                   if category not in categories)

    @cached_property
    def length(self):
        return len(self.password)

    @cached_property
    def letters_uppercase(self):
        return self.char_categories_detailed['Lu']

    @cached_property
    def letters_lowercase(self):
        return self.char_categories_detailed['Ll']

    @cached_property
    def numbers(self):
        return self.char_categories['N']

    @cached_property
    def special_characters(self):
        """Everything that is neither a letter nor a number."""
        return self.count_except('L', 'N')
