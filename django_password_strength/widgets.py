from django.forms import PasswordInput
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


class PasswordInputBase(PasswordInput):
    """Shared plumbing for the three password widgets.

    ``self.attrs`` carries two unrelated kinds of key: real HTML attributes, and
    configuration that only steers the surrounding markup (``validators`` and friends,
    put there by ``PasswordField``). The configuration must not reach the rendered
    ``<input>``.

    It is read non-destructively at render time and stripped in ``get_context`` -- the
    one hook Django guarantees runs on the attrs that are about to become HTML. Doing it
    there, rather than popping the keys off ``self.attrs``, is what makes a widget
    instance renderable more than once: a widget that consumed its own configuration
    silently lost the password policy on every render after the first.
    """

    #: Keys used to drive the markup, never emitted as HTML attributes.
    config_attrs = ('validators', 'validators_defaults', 'show_progressbar_info')

    #: CSS class the bundled JavaScript hooks onto. None for widgets with no behaviour.
    css_class = None

    def get_context(self, name, value, attrs):
        """Drop the configuration keys and apply ``css_class`` on the way to the HTML.

        ``Widget.render`` calls this with ``self.attrs`` already merged over the caller's
        attrs, which makes it the last point where the two kinds of key are still
        together -- and, unlike ``render``, one that every code path goes through.
        """
        context = super().get_context(name, value, attrs)
        widget_attrs = context['widget']['attrs']
        for key in self.config_attrs:
            widget_attrs.pop(key, None)
        if self.css_class:
            widget_attrs['class'] = self.css_classes(widget_attrs.get('class'))
        return context

    def css_classes(self, existing):
        """``css_class`` appended to whatever the caller already asked for, at most once."""
        classes = (existing or '').split()
        if self.css_class not in classes:
            classes.append(self.css_class)
        return ' '.join(classes)

    def markup_attrs(self, attrs):
        """The attrs handed to the surrounding templates, with the autocomplete default.

        Returns a copy: ``Widget.render`` documents ``attrs`` as optional, and a dict the
        caller owns is not ours to mutate.
        """
        attrs = {} if attrs is None else dict(attrs)
        attrs.setdefault('autocomplete', 'new-password')
        return attrs

    def strength_rules(self, attrs):
        """The script block binding the client-side policy to this field."""
        return render_to_string(
            "django_password_strength/widgets/strength-rules.html",
            context={
                'attrs': attrs,
                'validators': self.attrs.get('validators', []),
                'validators_defaults': self.attrs.get('validators_defaults', True),
            })


#: Deprecated alias. The Django < 1.11 ``build_attrs`` shim it used to carry is gone --
#: ``build_attrs`` is Django's own again. Subclass ``PasswordInputBase`` instead.
PasswordInputCompat = PasswordInputBase


class PasswordMutedInput(PasswordInputBase):
    """Password input with the requirement list but no strength meter."""

    class Media:
        js = (
            'django_password_strength/js/password-requirements.js',
            'django_password_strength/js/password-strength-rules.js',
        )
        css = {
            'screen': ('django_password_strength/css/password-strength.css',)
        }

    def render(self, name, value, attrs=None, renderer=None):
        attrs = self.markup_attrs(attrs)

        html = super().render(name, value, attrs, renderer)
        html += self.strength_rules(attrs)
        return mark_safe(html)


class PasswordStrengthInput(PasswordInputBase):
    """
    Form widget to show the user how strong his/her password is.
    """

    css_class = 'password_strength'

    def render(self, name, value, attrs=None, renderer=None):
        attrs = self.markup_attrs(attrs)

        # strength markup
        html = render_to_string(
            "django_password_strength/widgets/progressbar.html", context=attrs)
        html += super().render(name, value, attrs, renderer)
        if self.attrs.get('show_progressbar_info', True):
            html += render_to_string(
                "django_password_strength/widgets/progressbar-info.html", context=attrs)
        html += self.strength_rules(attrs)
        return mark_safe(html)

    class Media:
        js = (
            'django_password_strength/js/zxcvbn.js',
            'django_password_strength/js/password-strength.js',
            'django_password_strength/js/password-requirements.js',
            'django_password_strength/js/password-strength-rules.js',
        )
        css = {
            'screen': ('django_password_strength/css/password-strength.css',)
        }


class PasswordConfirmationInput(PasswordInputBase):
    """
    Form widget to confirm the users password by letting him/her type it again.
    """

    css_class = 'password_confirmation'

    def __init__(self, confirm_with=None, attrs=None, render_value=False):
        """``confirm_with`` is the *name* of the field to match, not its id: the widget
        prefixes it with ``id_`` to build the selector the JavaScript compares against.
        """
        super().__init__(attrs, render_value)
        self.confirm_with = confirm_with

    def render(self, name, value, attrs=None, renderer=None):
        if self.confirm_with:
            # Plain assignment, so rendering the same instance twice is idempotent --
            # unlike the class concatenation this widget used to do here.
            self.attrs['data-confirm-with'] = 'id_%s' % self.confirm_with

        attrs = self.markup_attrs(attrs)

        html = super().render(name, value, attrs, renderer)
        html += render_to_string(
            "django_password_strength/widgets/strength-info.html", context=attrs)
        return mark_safe(html)
