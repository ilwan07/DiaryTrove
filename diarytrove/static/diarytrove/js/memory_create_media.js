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
        li.dataset.id = item.id;

        // Load previews
        const previewWrap = document.createElement("div");
        previewWrap.className = "media-preview";

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
            const file_box = document.createElement("img");
            file_box.className = "preview-file";
            file_box.src = file_asset_path;
            previewWrap.appendChild(file_box);
        }

        const meta = document.createElement("div");
        meta.className = "metadata";
        const name = document.createElement("p");
        name.textContent = item.file.name;
        const size = document.createElement("p");
        size.textContent = Math.round(item.file.size*1000 / (2**20)) / 1000 + " " + gettext("MiB");
        meta.appendChild(name);
        meta.appendChild(size);

        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className = "remove-btn";
        removeBtn.textContent = "✖";
        removeBtn.title = gettext("Remove");
        removeBtn.onclick = () => {
            removeFile(item.id);
        };

        li.appendChild(removeBtn);
        li.appendChild(previewWrap);
        li.appendChild(meta);
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
        progressWrap.style.display = "none";
        progressBar.value = 0;
        progressText.textContent = "0%";
        return;
    }

    // Build FormData from the form
    const fd = new FormData(form);

    // Append the files we stored in selectedFiles
    selectedFiles.forEach(item => fd.append("files[]", item.file));
    
    // Disable UI while uploading
    submitBtn.disabled = true;
    addBtn.disabled = true;

    const xhr = new XMLHttpRequest();
    xhr.open("POST", form.action, true);

    xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");

    // Progress for upload
    xhr.upload.onprogress = function (e) {
        if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            progressWrap.style.display = "";
            progressBar.value = percent;
            progressText.textContent = percent + "%";
        }
    };

    xhr.onload = function () {
        submitBtn.disabled = false;
        addBtn.disabled = false;

        if (xhr.status >= 200 && xhr.status < 300) {
            try {
            const data = JSON.parse(xhr.responseText);
            if (data && data.success) {
                // Revoke created object URLs to free memory
                for (const it of selectedFiles) {
                if (it._objectUrl) try { URL.revokeObjectURL(it._objectUrl); } catch(e) {}
                }
                // Redirect if server asked for it after confirming success to the user
                if (data.redirect) {
                    can_exit = true;
                    document.querySelector("main").innerHTML = "<h1>" + gettext("Memory created successfully! You will be redirected shortly...") + "</h1>";
                    setTimeout(() => {
                        window.location = data.redirect;
                    }, 2000);
                return;
                }
                // Else reload
                window.location.reload();
                return;
            } else {
                errorbold.textContent = data && data.error ? data.error : gettext("Upload failed.");
                error.style.display = "";
                errorbr.style.display = "";
                progressWrap.style.display = "none";
                progressBar.value = 0;
                progressText.textContent = "0%";
            }
            } catch (e) {
            errorbold.textContent = gettext("Server returned an unexpected response.");
            error.style.display = "";
            errorbr.style.display = "";
            progressWrap.style.display = "none";
            progressBar.value = 0;
            progressText.textContent = "0%";
            }
        } else {
            // Try parse JSON error
            try {
                const data = JSON.parse(xhr.responseText);
                errorbold.textContent = gettext("Upload failed: ") + data.error;
                error.style.display = "";
                errorbr.style.display = "";
                progressWrap.style.display = "none";
                progressBar.value = 0;
                progressText.textContent = "0%";
            } catch (e) {
                errorbold.textContent = gettext("Upload failed (status ") + xhr.status + ").";
                error.style.display = "";
                errorbr.style.display = "";
                progressWrap.style.display = "none";
                progressBar.value = 0;
                progressText.textContent = "0%";
            }
        }
    };

    xhr.onerror = function () {
        submitBtn.disabled = false;
        addBtn.disabled = false;
        errorbold.textContent = gettext("Network or server error during upload.");
        error.style.display = "";
        errorbr.style.display = "";
        progressWrap.style.display = "none";
        progressBar.value = 0;
        progressText.textContent = "0%";
    };

    // Send
    xhr.send(fd);
});

// Initial render
renderList();
})();
