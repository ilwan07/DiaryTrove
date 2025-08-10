var form = document.querySelector("form");
var modified = false;
var inputs = form.querySelectorAll("input:not([type='submit']):not([type='hidden'])");

// Make each input trigger the modify function on change
inputs.forEach(function(input) {
    input.setAttribute("onchange", "modify()");
});

function modify() {
    modified = true;
}

// Disable the exit warning if the form is valid
if (form) {
    form.addEventListener("submit", function(e) {
        modified = false;
    });
}

// Warn the user before leaving the page if he started filling some data
window.addEventListener("beforeunload", function(e) {
    if (modified) {
        e.preventDefault();
        return "";
    }
});
