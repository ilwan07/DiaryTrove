const editable_lock_time_input = document.getElementById("id_editable_lock_time");
const editable_lock_time_div = editable_lock_time_input.parentElement;
const lock_time_input = document.getElementById("id_lock_time");
const email_reminder_label = document.querySelector("label[for='id_mail_reminder']");
const form = document.querySelector("form");

editable_lock_time_input.setAttribute("onchange", "editable()");

// Add a precision in the email reminder label
email_reminder_label.innerHTML += "<br>" + gettext("(0 to disable)");

// Make sure to check the box if it should be editable
if (editable) {
    editable_lock_time_input.checked = true;
}

// Prevent from checking the box again later and from changing the lock time if not allowed
if (!editable_lock_time_input.checked) {
    editable_lock_time_input.setAttribute("disabled", "disabled");
    editable_lock_time_div.style.display = "none";
    lock_time_input.setAttribute("disabled", "disabled");
}

// Warn before making the lock time permanent
if (form && editable_lock_time_input) {
    form.addEventListener("submit", function(e) {
        if (!editable_lock_time_input.checked && !confirm(gettext("You won't ever be able to change the lock time again.\nAre you sure you want to continue?"))) {
            e.preventDefault();
        }
    });
}
