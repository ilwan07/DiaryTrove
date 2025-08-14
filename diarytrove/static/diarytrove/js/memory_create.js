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


// Handle the media upload and submit process
(function () {
// Keep selected files in an array so we can add or remove before submit
const fileInput = document.getElementById("file-input");
const addBtn = document.getElementById("add-files-btn");
const fileList = document.getElementById("file-list");
const selectedCount = document.getElementById("selected-count");
const form = document.getElementById("upload-form");
const progressWrap = document.getElementById("progress-wrap");
const progressBar = document.getElementById("upload-progress");
const progressText = document.getElementById("progress-text");
const submitBtn = document.getElementById("submit-btn");
const error = document.getElementById("error");
const errorbold = document.getElementById("errorbold");
const errorbr = document.getElementById("errorbr");

const MAX_TOTAL_BYTES = document.getElementById("max-bytes").innerText;
var selectedFiles = [];

function uid() {
    // Generate a random uid, very collision unlikely
    if (typeof crypto !== "undefined") {
        if (typeof crypto.randomUUID === "function") {
            return crypto.randomUUID();  // Supported in modern browsers
        }
        // Fallback: 16 random bytes to hex string
        const bytes = new Uint8Array(16);
        crypto.getRandomValues(bytes);
        return Array.from(bytes).map(b => b.toString(16).padStart(2, "0")).join("");
    }
    // Very old fallback: time + random
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

        // Load previews
        const previewWrap = document.createElement("div");

        if (item.file.type.startsWith("image/")) {
            const img = document.createElement("img");
            img.className = "preview-image";
            // Use FileReader for images for maximum compatibility
            const reader = new FileReader();
            reader.onload = (e) => img.src = e.target.result;
            reader.readAsDataURL(item.file);
            previewWrap.appendChild(img);
        }

        else if (item.file.type.startsWith("video/")) {
            const vid = document.createElement("video");
            vid.className = "preview-video";
            vid.src = URL.createObjectURL(item.file);
            vid.controls = true;
            vid.muted = true;
            vid.preload = "metadata";
            // Store object URL so we can revoke later
            item._objectUrl = vid.src;
            previewWrap.appendChild(vid);
        }

        else if (item.file.type.startsWith("audio/")) {
            const aud = document.createElement("audio");
            aud.className = "preview-audio";
            aud.src = URL.createObjectURL(item.file);
            aud.controls = true;
            item._objectUrl = aud.src;
            previewWrap.appendChild(aud);
        }

        else {
            // Generic icon placeholder
            //TODO: Use placeholder image
            const box = document.createElement("div");
            box.textContent = "FILE";
            box.style.width = "80px";
            box.style.height = "48px";
            box.style.display = "flex";
            box.style.alignItems = "center";
            box.style.justifyContent = "center";
            box.style.border = "1px solid #ddd";
            previewWrap.appendChild(box);
        }

        const meta = document.createElement("div");
        meta.className = "meta";
        const name = document.createElement("div");
        name.textContent = item.file.name;
        const size = document.createElement("div");
        size.textContent = Math.round(item.file.size*1000 / (2**20)) / 1000 + " " + gettext("MiB");
        meta.appendChild(name);
        meta.appendChild(size);

        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className = "remove-btn";
        removeBtn.textContent = gettext("Remove");
        removeBtn.onclick = () => {
            removeFile(item.id);
        };

        li.appendChild(previewWrap);
        li.appendChild(meta);
        li.appendChild(removeBtn);
        fileList.appendChild(li);
    });
}

function removeFile(id) {
    const idx = selectedFiles.findIndex(x => x.id === id);
    if (idx === -1) return;
    // Revoke any created object URL
    const item = selectedFiles[idx];
    if (item._objectUrl) {
        try { URL.revokeObjectURL(item._objectUrl); } catch (e) {}
    }
    selectedFiles.splice(idx, 1);
    renderList();
}

addBtn.addEventListener("click", () => {
    // Open the file picker
    fileInput.click();
});

fileInput.addEventListener("change", (ev) => {
    const files = Array.from(ev.target.files || []);
    files.forEach(f => {
        // Skip duplicates by comparing attributes
        const duplicate = selectedFiles.some(x => x.file.name === f.name && x.file.size === f.size && x.file.lastModified === f.lastModified);
        if (!duplicate) {
            selectedFiles.push({ id: uid(), file: f });
        }
    });
    fileInput.value = "";
    renderList();
    errorbold.textContent = "";
    error.style.display = "none";
    errorbr.style.display = "none";
});

function totalSelectedBytes() {
    return selectedFiles.reduce((s, i) => s + (i.file.size || 0), 0);
}

form.addEventListener("submit", (ev) => {
    ev.preventDefault();
    errorbold.textContent = "";
    error.style.display = "none";
    errorbr.style.display = "none";

    // Client-side total size check before upload
    const totalBytes = totalSelectedBytes();
    if (totalBytes > MAX_TOTAL_BYTES) {
        let total_mib = Math.round(totalBytes*1000 / (2**20)) / 1000;
        let max_total_mib = Math.round(MAX_TOTAL_BYTES*1000 / (2**20)) / 1000;
        errorbold.textContent = "The uploaded files are too large. The maximum is " + max_total_mib + " MiB total, you uploaded " + total_mib + " Mib.";
        error.style.display = "";
        errorbr.style.display = "";
        return;
    }

    // Build FormData from the form
    const fd = new FormData(form);

    // Append the files we stored in selectedFiles
    selectedFiles.forEach(item => fd.append("files[]", item.file));
    
    // Disable UI while uploading
    submitBtn.disabled = true;
    addBtn.disabled = true;

    //TODO: Progress

    // Send via fetch, include credentials for session
    fetch(form.action, {
        method: "POST",
        body: fd,
        credentials: "same-origin",  // Keep session cookies
        headers: {
            "X-Requested-With": "XMLHttpRequest"  // Allow server to know it's AJAX
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
