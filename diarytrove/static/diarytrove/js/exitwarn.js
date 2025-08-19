const form = document.querySelector("form");
const form_item = document.querySelector("form");
const inputs = form.querySelectorAll("input:not([type='submit']):not([type='hidden'])");
var modified = false;

// Make each input trigger the modify function on change
inputs.forEach(function(input) {
    let oldattr = input.getAttribute("onchange");
    input.setAttribute("onchange", "modify(); " + (oldattr ? oldattr : ""));
});

function modify() {
    modified = true;
}

// When submitting the form, clear the modified flag and then restore it if the form stays
if (form_item) {
    form_item.addEventListener("submit", function(e) {
        var wasModified = modified;
        modified = false;
        setTimeout(function() {
            // If the form is still in the document and had modifications then restore the flag
            if (document.contains(form_item) && wasModified) {
                modified = true;
            }
        }, 0);
    });
}

// Warn the user before leaving the page if unsaved data exists
window.addEventListener("beforeunload", function(e) {
    if (can_exit) {
        return;
    }
    if (modified) {
        e.preventDefault();
        return "";
    }
});
