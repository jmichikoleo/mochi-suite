function toggleExplanation(id, button) {
    const el = document.getElementById(id);

    if (el.style.display === "none" || el.style.display === "") {
        el.style.display = "block";
        button.innerText = "🙈 Hide Explanation";
    } else {
        el.style.display = "none";
        button.innerText = "💡 Show Explanation";
    }
}