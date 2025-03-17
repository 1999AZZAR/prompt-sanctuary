// Function to show the custom popup
function showPopup(title, message) {
    const popup = document.createElement('div');
    popup.id = 'custom-popup';
    popup.className = 'fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50';

    const popupContent = document.createElement('div');
    popupContent.className = 'bg-gray-800 p-8 rounded-xl shadow-2xl w-11/12 md:w-1/2 lg:w-1/3';

    const popupTitle = document.createElement('h2');
    popupTitle.id = 'popup-title';
    popupTitle.className = 'text-2xl font-bold mb-4';
    popupTitle.textContent = title;

    const popupMessage = document.createElement('p');
    popupMessage.id = 'popup-message';
    popupMessage.className = 'text-lg text-gray-300 mb-6';
    popupMessage.textContent = message;

    const okButton = document.createElement('button');
    okButton.className = 'bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200';
    okButton.textContent = 'OK';
    okButton.onclick = () => closePopup('custom-popup');

    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'flex justify-end';
    buttonContainer.appendChild(okButton);

    popupContent.appendChild(popupTitle);
    popupContent.appendChild(popupMessage);
    popupContent.appendChild(buttonContainer);

    popup.appendChild(popupContent);
    document.body.appendChild(popup);
}

// Function to close the custom popup
function closePopup(popupId = 'custom-popup') {
    const popup = document.getElementById(popupId);
    if (popup) {
        popup.remove();
    } else {
        console.error('Popup element not found in the DOM');
    }
}

// Copy function on personal library
document.addEventListener('DOMContentLoaded', function () {
    new ClipboardJS('.copy-button', {
        text: function (trigger) {
            return trigger.getAttribute('data-clipboard-text');
        }
    }).on('success', function (e) {
        e.clearSelection();
        showPopup("Success", "Prompt copied to clipboard!");
    }).on('error', function (e) {
        showPopup("Error", "Failed to copy prompt to clipboard.");
    });
});

// Edit function
document.addEventListener('DOMContentLoaded', function () {
    const editButtons = document.querySelectorAll('.edit-button');
    editButtons.forEach(button => {
        button.addEventListener('click', function () {
            const randomVal = button.getAttribute('data-random-val');
            const title = button.getAttribute('data-title');
            const prompt = button.getAttribute('data-prompt');
            openEditPopup(randomVal, title, prompt);
        });
    });
});

// Function to open the edit popup
function openEditPopup(randomVal, title, prompt) {
    const popup = document.createElement('div');
    popup.id = 'edit-popup';
    popup.className = 'fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50';

    const popupContent = document.createElement('div');
    popupContent.className = 'bg-gray-800 p-8 rounded-xl shadow-2xl w-11/12 md:w-1/2 lg:w-1/3';

    popupContent.innerHTML = `
        <h2 class="text-2xl font-bold mb-4">Edit Prompt</h2>
        <input type="hidden" id="editRandomVal" value="${randomVal}">
        <div class="mb-4">
            <label for="editTitle" class="block mb-2">Title:</label>
            <input type="text" id="editTitle" value="${title}" class="w-full p-3 bg-gray-700 rounded-lg">
        </div>
        <div class="mb-6">
            <label for="editPrompt" class="block mb-2">Prompt:</label>
            <textarea id="editPrompt" class="w-full p-3 bg-gray-700 rounded-lg">${prompt}</textarea>
        </div>
        <div class="flex justify-end space-x-4">
            <button id="cancelEdit" class="bg-gray-500 text-white px-6 py-3 rounded-lg hover:bg-gray-600 transition duration-200">Cancel</button>
            <button id="saveEdit" class="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200">Save</button>
        </div>
    `;

    popup.appendChild(popupContent);
    document.body.appendChild(popup);

    // Cancel button functionality
    document.getElementById('cancelEdit').onclick = function () {
        closePopup('edit-popup');
    };

    // Save button functionality
    document.getElementById('saveEdit').onclick = function () {
        const newRandomVal = document.getElementById('editRandomVal').value;
        const newTitle = document.getElementById('editTitle').value;
        const newPrompt = document.getElementById('editPrompt').value;
        saveEditedPrompt(newRandomVal, newTitle, newPrompt);
    };
}

// Function to save the edited prompt
function saveEditedPrompt(randomVal, title, prompt) {
    const formData = new FormData();
    formData.append('random_val', randomVal);
    formData.append('edited_title', title);
    formData.append('edited_prompt', prompt);

    fetch('/save_edit', {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else if (!response.ok) {
            throw new Error('Failed to update prompt.');
        }
        return response.text();
    })
    .then(() => {
        showPopup("Success", "Prompt updated successfully!");
        closePopup('edit-popup');
    })
    .catch((error) => {
        console.error('Error:', error);
        showPopup("Error", "Failed to update prompt: " + error.message);
    });
}

// Function to confirm deletion
function confirmDelete(randomVal) {
    const popup = document.createElement('div');
    popup.id = 'delete-popup';
    popup.className = 'fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50';

    const popupContent = document.createElement('div');
    popupContent.className = 'bg-gray-800 p-8 rounded-xl shadow-2xl w-11/12 md:w-1/2 lg:w-1/3';

    popupContent.innerHTML = `
        <h2 class="text-2xl font-bold mb-4">Confirm Deletion</h2>
        <p class="text-lg text-gray-300 mb-6">Are you sure you want to delete this prompt?</p>
        <div class="flex justify-end space-x-4">
            <button id="cancelDelete" class="bg-gray-500 text-white px-6 py-3 rounded-lg hover:bg-gray-600 transition duration-200">Cancel</button>
            <button id="confirmDelete" class="bg-red-500 text-white px-6 py-3 rounded-lg hover:bg-red-600 transition duration-200">Delete</button>
        </div>
    `;

    popup.appendChild(popupContent);
    document.body.appendChild(popup);

    // Cancel button functionality
    document.getElementById('cancelDelete').onclick = function () {
        closePopup('delete-popup');
    };

    // Confirm delete button functionality
    document.getElementById('confirmDelete').onclick = function () {
        deletePrompt(randomVal);
        closePopup('delete-popup');
    };
}

// Function to delete a prompt
function deletePrompt(randomVal) {
    fetch('/delete_prompt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'prompt_id=' + encodeURIComponent(randomVal), // Change 'random_val' to 'prompt_id'
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else if (!response.ok) {
            throw new Error('Failed to delete prompt.');
        }
        return response.text();
    })
    .then(() => {
        showPopup("Success", "Prompt deleted successfully!");
    })
    .catch((error) => {
        console.error('Error:', error);
        showPopup("Error", "Failed to delete prompt: " + error.message);
    });
}

// Add event listeners to all delete buttons
document.addEventListener('DOMContentLoaded', function () {
    const deleteButtons = document.querySelectorAll('.delete-button');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault(); // Prevent the form from submitting immediately
            const randomVal = button.getAttribute('data-random-val');
            confirmDelete(randomVal);
        });
    });
});

// Function to handle sharing a prompt
function sharePrompt(promptId, title, promptContent) {
    const data = {
        prompt_id: promptId,
        title: title,
        prompt: promptContent
    };

    fetch('/share_prompt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Failed to share prompt.');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showPopup("Success", "Prompt shared successfully!");
        } else {
            showPopup("Error", "Failed to share prompt: " + (data.error || "Unknown error"));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showPopup("Error", "Error sharing prompt: " + error.message);
    });
}

// Add event listeners to all share buttons
document.addEventListener('DOMContentLoaded', function () {
    const shareButtons = document.querySelectorAll('.share-button');
    shareButtons.forEach(button => {
        button.addEventListener('click', function () {
            const promptId = button.getAttribute('data-prompt-id');
            const title = button.getAttribute('data-title');
            const promptContent = button.getAttribute('data-prompt');

            if (promptId && title && promptContent) {
                sharePrompt(promptId, title, promptContent);
            } else {
                showPopup("Error", "Error: Missing prompt data.");
            }
        });
    });
});
