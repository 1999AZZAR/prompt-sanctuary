function openEditPopup(randomVal, title, prompt) {
    var editPopup = document.getElementById('editPopup');
    var backdrop = document.getElementById('backdrop');

    // Set the title and prompt values
    document.getElementById('editRandomVal').value = randomVal;
    document.getElementById('editTitle').value = title;
    document.getElementById('editPrompt').value = prompt;

    // Show the edit popup and backdrop
    editPopup.style.display = 'block';
    backdrop.style.display = 'block';

    // Cancel function
    document.getElementById('cancelEdit').onclick = function() {
        // Close the edit popup and backdrop without saving
        editPopup.style.display = 'none';
        backdrop.style.display = 'none';
    };

    // Save function
    document.getElementById('saveEdit').onclick = function() {
        var newRandomVal = document.getElementById('editRandomVal').value;
        var newTitle = document.getElementById('editTitle').value;
        var newPrompt = document.getElementById('editPrompt').value;

        saveEditedPrompt(newRandomVal, newTitle, newPrompt);

        // Close the edit popup and backdrop
        editPopup.style.display = 'none';
        backdrop.style.display = 'none';
    };
}

function saveEditedPrompt(randomVal, title, prompt) {
    // Implement the logic to save the edited prompt
    console.log('Saving edited prompt:', randomVal, title, prompt);
    // Example: Send data to server using fetch
    fetch('/update-prompt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ randomVal, title, prompt }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        // Optionally, refresh the prompt list or update the UI
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}
