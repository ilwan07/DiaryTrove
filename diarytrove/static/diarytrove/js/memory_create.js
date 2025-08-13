const checkbox_input = document.querySelector("#checkboxdiv input");
const locktime_div = document.getElementById("locktimediv");
const locktime_input = document.querySelector("#locktimediv input");

function checkbox_update() {
    if (checkbox_input.checked) {
        locktime_div.style.display = "none";
        locktime_input.setAttribute("min", 0);
        locktime_input.value = 0; // Set to 0 if default lock time is used
    } else {
        locktime_div.style.display = "";
        locktime_input.setAttribute("min", 1);
        locktime_input.value = 365;
    }
}

checkbox_update();
checkbox_input.addEventListener("change", checkbox_update);


(function () {  // Handle the media upload and submit process
// Keep selected files in an array so we can add or remove before submit
var selectedFiles = [];
const fileInput = document.getElementById("file-input");
const addBtn = document.getElementById("add-files-btn");
const fileList = document.getElementById("file-list");
const selectedCount = document.getElementById("selected-count");
const form = document.getElementById("upload-form");
const error = document.getElementById("error");
const errorbold = document.getElementById("errorbold");
const errorbr = document.getElementById("errorbr");

function uid() {
    // Generate a random uid, very collision unlikely
    if (typeof crypto !== "undefined") {
    if (typeof crypto.randomUUID === "function") {
        return crypto.randomUUID(); // best, supported in modern browsers
    }
    // fallback: 16 random bytes to hex string
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    return Array.from(bytes).map(b => b.toString(16).padStart(2, "0")).join("");
}
// very old fallback: time + random
return Date.now().toString(36) + Math.random().toString(36).slice(2,8);
}

function renderList() {
    fileList.innerHTML = "";
    if (selectedFiles.length === 0) {
        selectedCount.textContent = gettext("No files selected");
        return;
    }
    selectedCount.textContent = selectedFiles.length + gettext(" file(s) selected");
    selectedFiles.forEach(item => {
        const li = document.createElement("li");
        li.className = "file-item";
        li.dataset.id = item.id;

        const nameSpan = document.createElement("span");
        nameSpan.className = "file-name";
        nameSpan.textContent = item.file.name + " (" + Math.round(item.file.size/1024) + " KiB)";

        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.textContent = "✖";
        removeBtn.title = gettext("Remove");
        removeBtn.onclick = () => {
            removeFile(item.id);
        };

        li.appendChild(nameSpan);
        li.appendChild(removeBtn);
        fileList.appendChild(li);
    });
}

function removeFile(id) {
    selectedFiles = selectedFiles.filter(i => i.id !== id);
    renderList();
}

addBtn.addEventListener("click", () => {
    // Open the file picker
    fileInput.click();
});

fileInput.addEventListener("change", (event) => {
    const files = Array.from(event.target.files || []);
    files.forEach(f => {
        // Skip duplicates by comparing attributes
        const duplicate = selectedFiles.some(x => x.file.name === f.name && x.file.size === f.size && x.file.lastModified === f.lastModified);
        if (!duplicate) {
            selectedFiles.push({ id: uid(), file: f });
        }
    });
    fileInput.value = "";
    renderList();
});

form.addEventListener("submit", (ev) => {
    ev.preventDefault();

    // Build FormData from the form
    const fd = new FormData(form);

    // Append the files we stored in selectedFiles
    selectedFiles.forEach(item => fd.append("files[]", item.file));

    // Send via fetch, include credentials for session
    fetch(form.action, {
        method: "POST",
        body: fd,
        credentials: "same-origin", // Keep session cookies
        headers: {
            "X-Requested-With": "XMLHttpRequest" // Allow server to know it's AJAX
        }
    }).then(async response => {
        if (!response.ok) {
            const text = await response.json().catch(()=>gettext("(no body)"));
            errorbold.textContent = gettext("Upload failed: ") + text.error;
            error.style.display = "";
            errorbr.style.display = "";
            return;
        }
        const data = await response.json().catch(()=>null);
        if (data && data.redirect) {
            // Server suggests a redirect
            window.location = data.redirect;
        } else {
            window.location.reload();
        }
    }).catch(err => {
        errorbold.textContent = gettext("Upload error: ") + err.message;
        error.style.display = "";
        errorbr.style.display = "";
    });
});

// Initial render
renderList();
})();
