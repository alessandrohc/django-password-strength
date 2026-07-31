if (typeof jQuery === 'undefined') {
    throw new Error('password-strength-rules.js requires jQuery')
}

(function ($) {
    // Each password input carries its own policy in this attribute. It used to arrive in
    // an inline <script> that defined a jQuery plugin, which a Content-Security-Policy
    // carrying 'strict-dynamic' blocks outright when it has no nonce -- and since the
    // initialiser only ran when that plugin existed, the requirement popover just never
    // appeared. Reading an attribute cannot be blocked by any script-src.
    var POLICY_ATTR = 'data-password-rules';

    // jQuery.fn.data parses a JSON-shaped attribute on its own, so this is usually
    // already an object; a string means it declined to, and PassRequirements needs the
    // parsed form either way.
    function readPolicy($el) {
        var policy = $el.data('password-rules');

        if (typeof policy !== 'string') {
            return policy;
        }

        try {
            return JSON.parse(policy);
        } catch (exc) {
            return null;
        }
    }

    $(function () {
        var $fields = $('[' + POLICY_ATTR + ']');

        // Nothing to bind: a page with no password field, or one whose only field is a
        // confirmation input.
        if (!$fields.length) {
            return;
        }

        // Loud on a broken asset bundle. Failing silently is what made the original bug
        // so hard to spot, so a missing dependency says so instead of doing nothing --
        // but it reports rather than throws: this runs in a jQuery ready callback, and an
        // exception here would take the page's other ready handlers down with it.
        if (typeof $.fn.PassRequirements !== 'function') {
            console.error(
                'password-strength-rules.js requires password-requirements.js');
            return;
        }

        $fields.each(function () {
            var $el = $(this), policy = readPolicy($el);

            if (!policy) {
                console.error(
                    'Unreadable ' + POLICY_ATTR + ' on input with id:[' + this.id + ']');
                return;
            }

            $el.PassRequirements({rules: policy.rules, defaults: policy.defaults});
        });
    });
}(jQuery));
