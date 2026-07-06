// Our Content-Security-Policy blocks inline "onsubmit" attributes, so
// confirmation prompts for destructive actions are wired up from here
// instead, using a data-confirm attribute on the form.
document.addEventListener('DOMContentLoaded', function () {
    var forms = document.querySelectorAll('form[data-confirm]');

    forms.forEach(function (form) {
        form.addEventListener('submit', function (event) {
            var message = form.getAttribute('data-confirm');

            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });
});
