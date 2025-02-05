const textarea = document.getElementById("text-input");
const correctButton = document.getElementById("correct-button");
const outputSection = document.querySelector(".output-section");

const tabs = document.querySelectorAll(".tab");
const correctionsList = document.getElementById("corrections-list");

let allCorrections = [];
let capitalizationCorrections = [];  
let grammarCorrections = []; 
let spellingCorrections = [];
let punctuationCorrections = [];

textarea.addEventListener("input", () => {
    outputSection.classList.add("blur");
    resetTabs();
    resetCorrections();
});

correctButton.addEventListener("click", () => {
    const textInput = textarea.value;

    // Show loader
    document.getElementById("loader").style.display = "block";

    fetch("/correct", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `text=${encodeURIComponent(textInput)}`,
    })
        .then((response) => response.json())
        .then((data) => {
            const corrections = data.corrections;
            const counts = data.counts;

            allCorrections = corrections.all;
            capitalizationCorrections = corrections.capitalization;
            grammarCorrections = corrections.grammar;
            spellingCorrections = corrections.spelling;
            punctuationCorrections = corrections.punctuation;

            document.getElementById("all-count").textContent = counts.all; // allCorrections.length > 0 ? 1 : 0
            document.getElementById("capitalization-count").textContent = capitalizationCorrections.length > 0 ? 1 : 0;
            document.getElementById("grammar-count").textContent = grammarCorrections.length > 0 ? 1 : 0;
            document.getElementById("spelling-count").textContent = spellingCorrections.length > 0 ? 1 : 0;
            document.getElementById("punctuation-count").textContent = punctuationCorrections.length > 0 ? 1 : 0;

            document.getElementById("corrected-text").textContent = data.corrected_text;
        
            updateCorrections("all", allCorrections);

            outputSection.classList.remove("blur");

            document.getElementById("loader").style.display = "none";

            document.getElementById("corrected-text").textContent = data.corrected_text;
        })
        .catch((error) => {
            document.getElementById("loader").style.display = "none";
            console.error("Error:", error);
        });
});
 
tabs.forEach(tab => {
    tab.addEventListener("click", () => {
        tabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");

        const tabName = tab.getAttribute("data-tab");
        
        switch (tabName) {
            case "all":
                updateCorrections("all", allCorrections);
                break;
            case "capitalization":
                updateCorrections("capitalization", capitalizationCorrections);
                break;
            case "grammar":
                updateCorrections("grammar", grammarCorrections);
                break;
            case "spelling":
                updateCorrections("spelling", spellingCorrections);
                break;
            case "punctuation":
                updateCorrections("punctuation", punctuationCorrections);
                break;
        }
    });
});

function updateCorrections(tabName, corrections) {
    correctionsList.innerHTML = "";

    corrections.forEach(([incorrect, corrected]) => {
        const li = document.createElement("li");
        if (incorrect === " ") {
            li.innerHTML = `<span class="inserted-word">[Added]</span> → <span class="corrected-word">${corrected}</span>`;
        } else if (corrected === " ") {
            li.innerHTML = `<span class="error-word">${incorrect}</span> → <span class="removed-word">[Removed]</span>`;
        } else {
            li.innerHTML = `<span class="error-word">${incorrect}</span> → <span class="corrected-word">${corrected}</span>`;
        }
        correctionsList.appendChild(li);
    });
}

function resetTabs() {
    tabs.forEach(tab => tab.classList.remove("active"));
    document.querySelector(".tab[data-tab='all']").classList.add("active");
}

function resetCorrections() {
    correctionsList.innerHTML = "";
    document.getElementById("corrected-text").innerText = "";
}
