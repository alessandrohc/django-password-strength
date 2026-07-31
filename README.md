# Django Password Strength

An extension of the Django password widget including a password strength meter and crack time powered by [zxcvbn](https://github.com/lowe/zxcvbn).

Maintained by [Alessandro Hecht](https://github.com/alessandrohc) at
[alessandrohc/django-password-strength](https://github.com/alessandrohc/django-password-strength).
See [Credits](#credits) for the upstream history.

### Requirements:

Python **3.10 – 3.13**, Django **4.2 – 5.2**. Every combination in that range is exercised
in CI, except the two Django releases that predate Python 3.13 support (4.2 and 5.0).

Django is the only runtime dependency. The `password-strength` package it used to require
was absorbed in 1.6.0: only five character counters were ever used, its upstream is
archived, and its 2015 releases carry version strings that predate PEP 440 — which pip
reads off the index and, from 25.3, rejects. The counters now live in
`django_password_strength/strength.py`, built on `unicodedata` alone.

### Install:

    pip install git+https://github.com/alessandrohc/django-password-strength.git@1.5.0

Or pin it in `requirements.txt`:

    django-password-strength @ git+https://github.com/alessandrohc/django-password-strength.git@1.5.0

### Usage:

* Add `django_password_strength` to the installed apps of your Django Project
* Instead of using the django `PasswordInput` widget use the `PasswordStrengthInput`
* Be sure to include the form's required media in the template. _ie._ `{{ form.media }}`
* If you bundle your js yourself, take the files from `django_password_strength/js/` instead of relying on `{{ form.media }}`, keeping them in this order:
  * `zxcvbn.js` (or `zxcvbn-async.js`) -- the strength estimator, needed only by `PasswordStrengthInput`
  * `password-strength.js` -- the meter and the confirmation match
  * `password-requirements.js` -- the requirement popover
  * `password-strength-rules.js` -- binds each field's policy to that popover, and so must come after it
* For easiest integration also include [Twitter Bootstrap](http://getbootstrap.com/)

### Content Security Policy:

The widgets emit no inline `<script>`. A field's password policy is serialised to JSON and
published on the `<input>` itself, in a `data-password-rules` attribute that
`password-strength-rules.js` reads on load. That keeps the package working under a strict
policy without any nonce or hash plumbing on your side -- in particular under a
`script-src` carrying `'strict-dynamic'`, which cancels `'self'` for scripts and so blocks
any inline block that lacks a nonce.

Only the bundled `.js` files need to be allowed, and `{{ form.media }}` already emits them
as ordinary `<script src>` tags.

### Translations:

Catalogs are bundled for **Brazilian Portuguese (`pt_BR`)** and **Russian (`ru`)**. Every
user-facing string is translatable, so adding another language only means shipping a new
catalog under `django_password_strength/locale/`.

For the javascript translations be sure to add the javascript translation catalog [provided by django](https://docs.djangoproject.com/en/stable/topics/i18n/translation/#using-the-javascript-translation-catalog) or use something like [django-statici18n](https://github.com/zyegfryed/django-statici18n) for a static version of the catalog. If you don't want translations you don't have to add the catalog to your page.

### Example:

_forms.py_

    from django import forms
    from django_password_strength.fields import PasswordField, PasswordConfirmationField
    
    class SignupForm(forms.Form):
        username = forms.CharField()
        passphrase = PasswordField(
            # optional options
            # min_length=5,
            # special_length=2,
            # lowercase_length=3,
            # uppercase_length=6,
            # numbers_length=2,
            # the password strength bar is displayed
            strength_view=True,
            # if information (text) strength bar appears
            show_progressbar_info=True
        )
        confirm_passphrase = PasswordConfirmationField()

### Example using multiple password fields:

_forms.py_

    from django import forms
    from django_password_strength.widgets import PasswordStrengthInput, PasswordConfirmationInput
    
    class SignupForm(forms.Form):
        username = forms.CharField()
        passphrase = forms.CharField(
            widget=PasswordStrengthInput()
        )
        confirm_passphrase = forms.CharField(
            widget=PasswordConfirmationInput(confirm_with='passphrase')
        )

        passphrase2 = forms.CharField(
            widget=PasswordStrengthInput()
        )
        confirm_passphrase2 = forms.CharField(
            widget=PasswordConfirmationInput(confirm_with='passphrase2')
        )

### Running the tests:

The suite is offline and needs no database. Install the package with its test extra and
run pytest:

    pip install -e ".[test]"
    pytest -q

`tests/test_locale.py` recompiles the `.po` sources to check them against the committed
`.mo` files; that check skips itself when `msgfmt` (GNU gettext) is not on `PATH`.

To reproduce a single matrix cell locally, pin Django in a throwaway environment:

    uv venv --python 3.13 .venv
    uv pip install --python .venv/bin/python "Django~=5.2.0" -e ".[test]"
    .venv/bin/python -m pytest -q

Deprecation warnings are promoted to errors (see `filterwarnings` in `pyproject.toml`), so
a `RemovedInDjangoXXWarning` raised anywhere in the suite fails the run. That is the early
signal for the next Django release, and it is deliberately not scoped to this package.

### Credits:

Originally created by A.J. May ([aj-may/django-password-strength](https://github.com/aj-may/django-password-strength)),
with Python 3 / modern Django work by Alex Silva ([alexsilva/django-password-strength](https://github.com/alexsilva/django-password-strength)).

Released under the BSD 3-Clause license — see [LICENSE.md](LICENSE.md) and [AUTHORS.md](AUTHORS.md).
