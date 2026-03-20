document.addEventListener("DOMContentLoaded", () => {

    // --- STATE ---
    let flashcards = [];
    let currentIndex = 0;
    let currentDeck = "";
    let library = JSON.parse(localStorage.getItem("mochiLibrary")) || {};
    let langFrontFirst = true;
    
    // --- ELEMENTS ---
    const wordEl = document.getElementById("word");
    const meaningEl = document.getElementById("meaning");
    
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
    const revealBtn = document.getElementById("revealBtn");
    
    const againBtn = document.getElementById("againBtn");
    const hardBtn = document.getElementById("hardBtn");
    const easyBtn = document.getElementById("easyBtn");
    
    const editCardBtn = document.getElementById("editCardBtn");
    const deleteCardBtn = document.getElementById("deleteCardBtn");
    const addCardBtn = document.getElementById("addCardBtn");
    
    const deckSelect = document.getElementById("deckSelect");
    const progressEl = document.getElementById("progress");
    const deckStatsEl = document.getElementById("deckStats");
    
    const searchInput = document.getElementById("searchInput");
    const searchResults = document.getElementById("searchResults");
    
    const newWord = document.getElementById("newWord");
    const newMeaning = document.getElementById("newMeaning");
    
    const langToggle = document.getElementById("langToggle");
    
    // --- SAVE ---
    function save(){
        localStorage.setItem("mochiLibrary", JSON.stringify(library));
    }
    
    // --- LOAD DECK ---
    function loadDeck(name){
        currentDeck = name;
        flashcards = library[name] || [];
        currentIndex = 0;
        showCard();
    }
    
    // --- SHOW CARD ---
    function showCard(){
        if(!flashcards.length){
            wordEl.textContent = "No cards";
            meaningEl.style.display = "none";
            progressEl.textContent = "0 / 0";
            deckStatsEl.textContent = "";
            return;
        }
    
        const c = flashcards[currentIndex];
    
        wordEl.textContent = langFrontFirst ? c.front : c.back;
        meaningEl.textContent = langFrontFirst ? c.back : c.front;
        meaningEl.style.display = "none";
    
        const known = flashcards.filter(c => c.known).length;
    
        progressEl.textContent = `${currentIndex + 1} / ${flashcards.length}`;
        deckStatsEl.textContent = `Known: ${known} / ${flashcards.length}`;
    }
    
    // --- NAVIGATION ---
    prevBtn.onclick = () => {
        if(!flashcards.length) return;
        currentIndex = (currentIndex - 1 + flashcards.length) % flashcards.length;
        showCard();
    };
    
    nextBtn.onclick = () => {
        if(!flashcards.length) return;
        currentIndex = (currentIndex + 1) % flashcards.length;
        showCard();
    };
    
    // --- KEYBOARD (SAFE) ---
    document.addEventListener("keydown", e => {
        if(e.target.tagName === "INPUT") return;
    
        if(e.key === "ArrowRight") nextBtn.click();
        if(e.key === "ArrowLeft") prevBtn.click();
        if(e.key === " ") meaningEl.style.display = "block";
    });
    
    // --- REVEAL ---
    revealBtn.onclick = () => {
        meaningEl.style.display = "block";
    };
    
    // --- DIFFICULTY ---
    function review(type){
        if(!flashcards.length) return;
    
        const c = flashcards[currentIndex];
    
        if(type === "again"){
            c.interval = 1;
            c.known = false;
        }
    
        if(type === "hard"){
            c.interval = (c.interval || 1) * 1.5;
        }
    
        if(type === "easy"){
            c.interval = (c.interval || 1) * 2;
            c.known = true;
        }
    
        c.lastReviewed = new Date().toISOString();
    
        save();
        nextBtn.click();
    }
    
    againBtn.onclick = () => review("again");
    hardBtn.onclick = () => review("hard");
    easyBtn.onclick = () => review("easy");
    
    // --- ADD CARD ---
    addCardBtn.onclick = () => {
        if(!currentDeck){
            alert("Please select a deck first!");
            return;
        }
    
        const front = newWord.value.trim();
        const back = newMeaning.value.trim();
    
        if(!front || !back){
            alert("Both fields are required!");
            return;
        }
    
        const newCard = {
            front,
            back,
            known: false,
            interval: 1
        };
    
        // ✅ ALWAYS update library directly
        library[currentDeck].push(newCard);
    
        // ✅ Sync flashcards
        flashcards = library[currentDeck];
    
        // Clear inputs
        newWord.value = "";
        newMeaning.value = "";
    
        save();
        showCard();
    };
    
    // --- EDIT CARD (FIXED) ---
    editCardBtn.onclick = () => {
        if(!flashcards.length) return;
    
        const card = flashcards[currentIndex];
    
        const newFront = prompt("Edit front:", card.front);
        if(newFront === null) return;
    
        const newBack = prompt("Edit back:", card.back);
        if(newBack === null) return;
    
        card.front = newFront.trim() || card.front;
        card.back = newBack.trim() || card.back;
    
        save();
        showCard();
    };
    
    // --- DELETE CARD (FIXED) ---
    deleteCardBtn.onclick = () => {
        if(!flashcards.length) return;
    
        if(confirm("Delete this card?")){
            flashcards.splice(currentIndex, 1);
    
            if(currentIndex >= flashcards.length){
                currentIndex = flashcards.length - 1;
            }
    
            save();
            showCard();
        }
    };
    
    // --- SEARCH ---
    searchInput.oninput = () => {
        const q = searchInput.value.toLowerCase();
        searchResults.innerHTML = "";
    
        if(!q) return;
    
        flashcards
            .filter(c =>
                c.front.toLowerCase().includes(q) ||
                c.back.toLowerCase().includes(q)
            )
            .slice(0, 10)
            .forEach(c => {
                const div = document.createElement("div");
                div.textContent = `${c.front} - ${c.back}`;
    
                div.onclick = () => {
                    currentIndex = flashcards.indexOf(c);
                    showCard();
                    searchResults.innerHTML = "";
                };
    
                searchResults.appendChild(div);
            });
    };
    
    // --- TOGGLE LANGUAGE ---
    langToggle.onchange = () => {
        langFrontFirst = !langFrontFirst;
        showCard();
    };
    
    // --- FILE INPUT (TXT) ---
    document.getElementById("fileInput").onchange = async e => {
        const file = e.target.files[0];
        if(!file) return;
    
        const text = await file.text();
    
        const cards = text.split("\n").map(line => {
            const parts = line.split(/\t|,/);
            if(parts.length < 2) return null;
    
            return {
                front: parts[0].trim(),
                back: parts[1].trim(),
                known: false,
                interval: 1
            };
        }).filter(Boolean);
    
        const name = file.name.replace(/\..+$/, "");
    
        library[name] = cards;
        save();
    
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        deckSelect.appendChild(option);
    };
    
    // --- SELECT DECK ---
    deckSelect.onchange = () => {
        loadDeck(deckSelect.value);
    };
    
    // --- INIT ---
    Object.keys(library).forEach(name => {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        deckSelect.appendChild(option);
    });
    
    });