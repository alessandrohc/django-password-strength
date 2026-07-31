"""Character statistics behind the server-side password policy.

`PasswordStats` used to come from the `password-strength` distribution on PyPI, whose
upstream (kolypto/py-password-strength) is archived: last release 2019, repository
read-only. The five counters the validators rely on were absorbed here so the package
stops depending on it -- see `django_password_strength/strength.py`.

These are characterisation tests: every expected value below was measured against the
original implementation before it was dropped, not derived from reading the code. The
point is the unicode semantics, which are counted by category
(https://www.unicode.org/reports/tr44/#GC_Values_Table) rather than by `str.isupper()` and
friends. Several of them are counter-intuitive and are exactly what a naive rewrite gets
wrong, so they are pinned explicitly:

* CJK and titlecase letters are neither uppercase nor lowercase, and -- being category
  `L*` -- are not "special" either;
* roman numerals and superscript digits count as numbers, being category `N*`;
* whitespace and combining marks count as special, being neither `L*` nor `N*`.
"""
import pytest

from django_password_strength.strength import PasswordStats

#: (password, note, length, uppercase, lowercase, numbers, special)
CORPUS = [
    ('', 'empty', 0, 0, 0, 0, 0),
    ('abc', 'lowercase ascii', 3, 0, 3, 0, 0),
    ('ABC', 'uppercase ascii', 3, 3, 0, 0, 0),
    ('123', 'ascii digits', 3, 0, 0, 3, 0),
    ('!@#', 'punctuation and symbols', 3, 0, 0, 0, 3),
    ('Abcdefg1!', 'a realistic passphrase', 9, 1, 6, 1, 1),
    ('café', 'accented lowercase (Ll)', 4, 0, 4, 0, 0),
    ('CAFÉ', 'accented uppercase (Lu)', 4, 4, 0, 0, 0),
    ('日本語', 'CJK: category Lo, so neither cased nor special', 3, 0, 0, 0, 0),
    ('ǅ', 'titlecase (Lt): neither upper nor lower, not special', 1, 0, 0, 0, 0),
    ('🎉', 'emoji (So): special', 1, 0, 0, 0, 1),
    ('á', 'a + combining acute (Mn): the mark counts as special', 2, 0, 1, 0, 1),
    ('Ⅷ', 'roman numeral (Nl): counts as a number', 1, 0, 0, 1, 0),
    ('²', 'superscript two (No): counts as a number', 1, 0, 0, 1, 0),
    ('  ', 'spaces (Zs): count as special', 2, 0, 0, 0, 2),
]

#: Readable ids so a failure names the case instead of dumping the password.
CORPUS_IDS = [note for _, note, *_ in CORPUS]


@pytest.mark.parametrize(
    'password,length,uppercase,lowercase,numbers,special',
    [(p, ln, up, lo, nu, sp) for p, _, ln, up, lo, nu, sp in CORPUS],
    ids=CORPUS_IDS)
def test_counters_match_the_original_implementation(
        password, length, uppercase, lowercase, numbers, special):
    stats = PasswordStats(password)

    assert stats.length == length
    assert stats.letters_uppercase == uppercase
    assert stats.letters_lowercase == lowercase
    assert stats.numbers == numbers
    assert stats.special_characters == special


class TestSpecialCharacters:
    """`special_characters` is "everything that is not a letter or a number", by unicode
    top-level category -- not a fixed punctuation set. These pin that definition, since
    it is the counter the special-character policy validator reads."""

    def test_letters_and_numbers_are_never_special(self):
        assert PasswordStats('abcABC123').special_characters == 0

    def test_counts_every_non_letter_non_number(self):
        # pontuação, símbolo, separador e marca -- uma de cada categoria não-L/N
        assert PasswordStats('.+ ́').special_characters == 4


class TestPasswordAttribute:
    def test_the_password_is_kept_as_text(self):
        assert PasswordStats('Abc1!').password == 'Abc1!'

    @pytest.mark.parametrize('value,expected', [(12345, '12345'), (None, 'None')])
    def test_a_non_string_is_coerced(self, value, expected):
        """The original coerced through `six.text_type`; a caller passing something that
        is not a string still gets counted rather than crashing."""
        assert PasswordStats(value).password == expected
        assert PasswordStats(value).length == len(expected)


class TestRepeatedAccess:
    """The counters are cached properties. Reading one twice must give the same answer --
    a cache keyed on the wrong name would silently return another property's value."""

    def test_every_counter_is_stable_across_reads(self):
        stats = PasswordStats('Abcdefg1!')

        first = (stats.length, stats.letters_uppercase, stats.letters_lowercase,
                 stats.numbers, stats.special_characters)
        second = (stats.length, stats.letters_uppercase, stats.letters_lowercase,
                  stats.numbers, stats.special_characters)

        assert first == second == (9, 1, 6, 1, 1)
