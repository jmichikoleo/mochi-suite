const dropArea = document.getElementById("drop-area");
const fileInput = document.getElementById("file-input");
const previewCanvas = document.getElementById("pdf-preview");
const downloads = document.getElementById("downloads");

let ctx = previewCanvas.getContext("2d");


// ========================
// CLICK TO OPEN FILE PICKER
// ========================

dropArea.addEventListener("click", () => {
    fileInput.click();
});


// ========================
// FILE INPUT UPLOAD
// ========================

fileInput.addEventListener("change", () => {

    const file = fileInput.files[0];

    if (!file) return;

    handleFile(file);
});


// ========================
// DRAG & DROP
// ========================

dropArea.addEventListener("dragover", (e) => {

    e.preventDefault();
    dropArea.style.borderColor = "#ff3f8b";

});

dropArea.addEventListener("dragleave", () => {

    dropArea.style.borderColor = "#ff6fa8";

});

dropArea.addEventListener("drop", (e) => {

    e.preventDefault();

    dropArea.style.borderColor = "#ff6fa8";

    const file = e.dataTransfer.files[0];

    handleFile(file);

});


// ========================
// HANDLE FILE
// ========================

function handleFile(file) {

    if (file.type !== "application/pdf") {

        alert("Please upload a PDF file.");
        return;

    }

    previewPDF(file);

    uploadFile(file);

}


// ========================
// PDF PREVIEW
// ========================

function previewPDF(file) {

    const url = URL.createObjectURL(file);

    pdfjsLib.getDocument(url).promise.then(function(pdf) {

        pdf.getPage(1).then(function(page) {

            const viewport = page.getViewport({ scale: 1.5 });

            previewCanvas.height = viewport.height;
            previewCanvas.width = viewport.width;

            const renderContext = {
                canvasContext: ctx,
                viewport: viewport
            };

            page.render(renderContext);

        });

    });

}


// ========================
// FILE UPLOAD
// ========================

function uploadFile(file) {

    downloads.innerHTML = `
        <p>🍡 Uploading and converting...</p>
        <div class="progress-bar">
            <div id="progress"></div>
        </div>
    `;

    const formData = new FormData();

    formData.append("file", file);

    const xhr = new XMLHttpRequest();

    xhr.open("POST", "/upload", true);


    // ========================
    // PROGRESS BAR
    // ========================

    xhr.upload.onprogress = function(e) {

        if (e.lengthComputable) {

            const percent = (e.loaded / e.total) * 100;

            const progress = document.getElementById("progress");

            progress.style.width = percent + "%";

        }

    };


    // ========================
    // RESPONSE
    // ========================

    xhr.onload = function() {

        if (xhr.status === 200) {

            const data = JSON.parse(xhr.responseText);

            downloads.innerHTML = `
                <h3>✅ Conversion Complete</h3>

                <p>Download your files:</p>

                <a href="/download?file=${data.txt}">
                    <button>📄 TXT</button>
                </a>

                <a href="/download?file=${data.epub}">
                    <button>📚 EPUB</button>
                </a>

                <a href="/download?file=${data.audio}">
                    <button>🎧 Audiobook</button>
                </a>
            `;

        } else {

            downloads.innerHTML = `
                <p>❌ Conversion failed</p>
            `;

        }

    };

    xhr.send(formData);

}