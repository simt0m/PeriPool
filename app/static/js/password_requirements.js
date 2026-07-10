// Mirrors the server-side password rules in RegisterForm (app/forms.py) so
// the live feedback never promises something the backend doesn't enforce.
document.addEventListener('DOMContentLoaded', function () {
    var password = document.getElementById('password');
    var confirmPassword = document.getElementById('confirm_password');
    var lengthItem = document.querySelector('[data-requirement="length"]');
    var uppercaseItem = document.querySelector('[data-requirement="uppercase"]');
    var digitItem = document.querySelector('[data-requirement="digit"]');
    var symbolItem = document.querySelector('[data-requirement="symbol"]');
    var matchItem = document.querySelector('[data-requirement="match"]');

    function setMet(item, met) {
        if (!item) return;
        item.classList.toggle('requirement-met', met);
        item.classList.toggle('requirement-unmet', !met);
    }

    function checkPassword() {
        var value = password ? password.value : '';

        setMet(lengthItem, value.length >= 8);
        setMet(uppercaseItem, /[A-Z]/.test(value));
        setMet(digitItem, /[0-9]/.test(value));
        setMet(symbolItem, /[^A-Za-z0-9]/.test(value));
    }

    function checkMatch() {
        setMet(
            matchItem,
            !!password && !!confirmPassword &&
            confirmPassword.value.length > 0 &&
            confirmPassword.value === password.value
        );
    }

    if (password) {
        password.addEventListener('input', function () {
            checkPassword();
            checkMatch();
        });
    }

    if (confirmPassword) {
        confirmPassword.addEventListener('input', checkMatch);
    }
});
