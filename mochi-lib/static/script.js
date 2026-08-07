let pdfDoc = null;
let pageNum = 1;
let timer = 0;
let interval = null;

const canvas = document.getElementById("pdf-render");

if (canvas) {

    const ctx = canvas.getContext("2d");

    const BOOK_KEY = window.PDF_FILE;
    const BOOKMARK_KEY = "bookmark_" + BOOK_KEY;

    let bookmarks = JSON.parse(localStorage.getItem(BOOKMARK_KEY)) || [];

    pdfjsLib.getDocument(window.PDF_FILE).promise.then(pdf => {
        pdfDoc = pdf;

        const saved = localStorage.getItem(BOOK_KEY);
        if (saved) pageNum = parseInt(saved);

        renderPage(pageNum);
    });

    function renderPage(num) {

        // fade out
        canvas.classList.add("canvas-fade");
    
        pdfDoc.getPage(num).then(page => {
    
            const viewport = page.getViewport({ scale: 1.6 });
    
            canvas.height = viewport.height;
            canvas.width = viewport.width;
    
            page.render({
                canvasContext: ctx,
                viewport: viewport
            }).promise.then(() => {
    
                // fade in after render
                setTimeout(() => {
                    canvas.classList.remove("canvas-fade");
                }, 50);
    
            });
    
            document.getElementById("page").innerText =
                `${num} / ${pdfDoc.numPages}`;
    
            localStorage.setItem(BOOK_KEY, num);
    
            updateUI();
        });
    }

    function updateUI() {
        updateBookmarks();
        updateStats();
    }

    function updateBookmarks() {
        const list = document.getElementById("bookmarkList");
        list.innerHTML = "";

        bookmarks.forEach(p => {
            const div = document.createElement("div");
            div.className = "bookmark-item";
            div.innerText = "Page " + p;
            div.onclick = () => {
                pageNum = p;
                renderPage(pageNum);
            };
            list.appendChild(div);
        });
    }

    function updateStats() {
        const progress = Math.round((pageNum / pdfDoc.numPages) * 100);

        document.getElementById("progressStat").innerText =
            "Progress: " + progress + "%";

        document.getElementById("timeStat").innerText =
            "Reading Time: " + timer + "s";
    }

    document.getElementById("bookmarkBtn").onclick = () => {
        if (bookmarks.includes(pageNum)) {
            bookmarks = bookmarks.filter(p => p !== pageNum);
        } else {
            bookmarks.push(pageNum);
        }

        localStorage.setItem(BOOKMARK_KEY, JSON.stringify(bookmarks));
        updateUI();
    };

    document.getElementById("next").onclick = () => {
        if (pageNum < pdfDoc.numPages) {
            pageNum++;
            renderPage(pageNum);
        }
    };

    document.getElementById("prev").onclick = () => {
        if (pageNum > 1) {
            pageNum--;
            renderPage(pageNum);
        }
    };

    document.getElementById("startTimer").onclick = () => {
        if (!interval) {
            interval = setInterval(() => {
                timer++;
                document.getElementById("time").innerText = timer + "s";
                updateStats();
            }, 1000);
        }
    };

    document.getElementById("stopTimer").onclick = () => {
        clearInterval(interval);
        interval = null;
    };

}