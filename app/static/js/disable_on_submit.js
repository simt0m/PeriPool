// Disables a form's submit button once it's been submitted, so a slow
// connection or an accidental double-click can't fire the same borrow,
// return, or admin action twice.
document.addEventListener('DOMContentLoaded', function () {
    var forms = document.querySelectorAll('form');

    forms.forEach(function (form) {
        form.addEventListener('submit', function () {
            var button = form.querySelector('button[type="submit"]');

            if (button) {
                button.disabled = true;
            }
        });
    });
});
