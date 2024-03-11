// Function to copy code to the clipboard
function copyCode() {
    var clickedButton = event.target;
    var codeContainer = clickedButton.parentElement.querySelector('article');

    if (codeContainer) {
        var textToCopy = codeContainer.textContent;
        var dummyTextArea = document.createElement('textarea');
        dummyTextArea.value = textToCopy;
        document.body.appendChild(dummyTextArea);
        dummyTextArea.select();
        document.execCommand('copy');
        document.body.removeChild(dummyTextArea);
        alert("Prompt copied to clipboard!");
    }
}

function promptForTitle(clickedButton) {
    var title = prompt("Enter a title for your prompt:");
    if (title !== null && title.trim() !== "") {
        var codeContainer = clickedButton.parentElement.querySelector('article');

        if (codeContainer) {
            var textToCopy = codeContainer.textContent;
            var dummyTextArea = document.createElement('textarea');
            dummyTextArea.value = textToCopy;
            document.body.appendChild(dummyTextArea);
            dummyTextArea.select();
            saveToLibrary(title, dummyTextArea.value); // Pass the correct parameter to saveToLibrary
            document.body.removeChild(dummyTextArea);
        }
    }
}

function saveToLibrary(title, prompt) {
    fetch('/advance/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'title=' + encodeURIComponent(title) + '&prompt=' + encodeURIComponent(prompt),
    })
        .then(response => response.text())
        .then(data => alert(data))
        .catch(error => console.error('Error:', error));
}
