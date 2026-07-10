// Mirrors the server-side password rules (Length(min=8) and EqualTo in
// app/forms.py) so the live feedback never promises something the backend
// doesn't actually enforce.
document.addEventListener('DOMContentLoaded', function () {
    var password = document.getElementById('password');
    var confirmPassword = document.getElementById('confirm_password');
    var lengthItem = document.querySelector('[data-requirement="length"]');
    var matchItem = document.querySelector('[data-requirement="match"]');

    function setMet(item, met) {
        if (!item) return;
        item.classList.toggle('requirement-met', met);
        item.classList.toggle('requirement-unmet', !met);
    }

    function checkLength() {
        setMet(lengthItem, !!password && password.value.length >= 8);
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
            checkLength();
            checkMatch();
        });
    }

    if (confirmPassword) {
        confirmPassword.addEventListener('input', checkMatch);
    }
});
