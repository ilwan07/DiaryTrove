const checkbox_input = document.querySelector("#checkboxdiv input");
const locktime_div = document.getElementById("locktimediv");
const locktime_input = document.querySelector("#locktimediv input");

function checkbox_update() {
    if (checkbox_input.checked) {
        locktime_div.style.display = "none";
        locktime_input.setAttribute("min", 0);
        locktime_input.value = 0;  // Set to 0 if default lock time is used
    } else {
        locktime_div.style.display = "";
        locktime_input.setAttribute("min", 1);
        locktime_input.value = 365;
    }
}

checkbox_update();
checkbox_input.addEventListener("change", checkbox_update);
