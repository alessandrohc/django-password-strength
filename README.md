# Django Password Strength

An extension of the Django password widget including a password strength meter and crack time powered by [zxcvbn](https://github.com/lowe/zxcvbn).

Maintained by [Alessandro Hecht](https://github.com/alessandrohc) at
[alessandrohc/django-password-strength](https://github.com/alessandrohc/django-password-strength).
See [Credits](#credits) for the upstream history.

### Requirements:

Python **3.10 – 3.13**, Django **4.2 – 5.2**. Every combination in that range is exercised
in CI, except the two Django releases that predate Python 3.13 support (4.2 and 5.0).

### Install:

    pip install git+https://github.com/alessandrohc/django-password-strength.git@1.5.0

Or pin it in `requirements.txt`:

    django-password-strength @ git+https://github.com/alessandrohc/django-password-strength.git@1.5.0

### Usage:

* Add `django_password_strength` to the installed apps of your Django Project
* Instead of using the django `PasswordInput` widget use the `PasswordStrengthInput`
* Be sure to include the form's required media in the template. _ie._ `{{ form.media }}`
* If you bundle your js you can use `django_password_strength/js/zxcvbn.js` or `django_password_strength/js/zxcvbn-async.js` and `django_password_strength/js/password_strength.js` instead
* For easiest integration also include [Twitter Bootstrap](http://getbootstrap.com/)

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
