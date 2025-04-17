// Function to show the custom popup
function showPopup(title, message, isConfirmation = false, onConfirm = null, onCancel = null) {
    const popup = document.createElement('div');
    popup.id = 'custom-popup';
    popup.className = 'fixed inset-0 flex items-center justify-center bg-black bg-opacity-25 backdrop-blur-sm z-50';

    const popupContent = document.createElement('div');
    popupContent.className = 'glass text-white p-6 sm:p-8 rounded-xl shadow-2xl max-w-lg w-11/12 sm:w-10/12 md:w-1/2 lg:w-1/3 relative';
    // Inline overflow styling for scroll
    popupContent.style.maxHeight = '80vh';
    popupContent.style.overflowY = 'auto';
    popupContent.style.overflowX = 'hidden';

    // Close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'absolute top-4 right-4 text-white text-xl';
    closeBtn.innerHTML = '&times;';
    closeBtn.onclick = () => closePopup('custom-popup');
    popupContent.appendChild(closeBtn);

    const popupTitle = document.createElement('h2');
    popupTitle.id = 'popup-title';
    popupTitle.className = 'text-2xl font-bold mb-4';
    popupTitle.textContent = title;

    const popupMessage = document.createElement('p');
    popupMessage.id = 'popup-message';
    popupMessage.className = 'text-lg text-gray-300 mb-6 whitespace-pre-wrap break-words';
    popupMessage.textContent = message;

    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'flex justify-end space-x-4';

    if (isConfirmation) {
        // Yes Button (for confirmation popups)
        const yesButton = document.createElement('button');
        yesButton.className = 'bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200';
        yesButton.textContent = 'Yes';
        yesButton.onclick = () => {
            if (onConfirm) onConfirm();
            closePopup('custom-popup');
        };

        // No Button (for confirmation popups)
        const noButton = document.createElement('button');
        noButton.className = 'bg-gray-500 text-white px-6 py-3 rounded-lg hover:bg-gray-600 transition duration-200';
        noButton.textContent = 'No';
        noButton.onclick = () => {
            if (onCancel) onCancel();
            closePopup('custom-popup');
        };

        buttonContainer.appendChild(yesButton);
        buttonContainer.appendChild(noButton);
    } else {
        // Non-confirmation popups (e.g., See): add Copy and Close
        const copyBtn = document.createElement('button');
        copyBtn.className = 'bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200';
        copyBtn.textContent = 'Copy';
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(message)
                .then(() => showPopup('Success', 'Prompt copied to clipboard!'))
                .catch(err => {
                    console.error('Failed to copy prompt:', err);
                    showPopup('Error', 'Failed to copy prompt. Please try again.');
                });
        };
        const closeBtn2 = document.createElement('button');
        closeBtn2.className = 'bg-gray-500 text-white px-6 py-3 rounded-lg hover:bg-gray-600 transition duration-200';
        closeBtn2.textContent = 'Close';
        closeBtn2.onclick = () => closePopup('custom-popup');
        buttonContainer.appendChild(copyBtn);
        buttonContainer.appendChild(closeBtn2);
    }

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

// Function to attach event listeners to copy buttons
function attachCopyButtonListeners() {
    document.querySelectorAll('.copy-button').forEach(button => {
        button.addEventListener('click', function (e) {
            // Prevent default button behavior
            e.preventDefault();

            // Get the prompt content from the data-clipboard-text attribute
            const promptContent = button.getAttribute('data-clipboard-text');

            // Use the Clipboard API to copy the content
            navigator.clipboard.writeText(promptContent)
                .then(() => {
                    showPopup("Success", "Prompt copied to clipboard!");
                })
                .catch((err) => {
                    console.error('Failed to copy prompt:', err);
                    showPopup("Error", "Failed to copy prompt. Please try again.");
                });
        });
    });
}

// Function to attach event listeners to save buttons
function attachSaveButtonListeners() {
    document.querySelectorAll('.save-button').forEach(button => {
        button.addEventListener('click', function (e) {
            // Prevent default button behavior
            e.preventDefault();

            // Get the title and prompt content from data attributes
            const title = button.getAttribute('data-title');
            const prompt = button.getAttribute('data-prompt');

            // Show custom confirmation popup with "Yes" and "No" buttons
            showPopup(
                "Confirm Save",
                `Are you sure you want to save "${title}" to your personal library?`,
                true, // This is a confirmation popup
                () => {
                    // If user clicks "Yes", save the prompt
                    savePrompt(title, prompt);
                },
                () => {
                    // If user clicks "No", do nothing
                    console.log("Save canceled.");
                }
            );
        });
    });

    // Attach See button listeners
    document.querySelectorAll('.see-button').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const card = btn.closest('.prompt-card');
            const title = card.querySelector('.mdc-typography--headline6').innerText;
            const content = card.querySelector('.mdc-typography--body2').innerText;
            showPopup(title, content);
        });
    });
}

// Function to unshare a prompt
function unsharePrompt(promptId) {
    fetch('/unshare_prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt_id: promptId })
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to unshare prompt.');
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showPopup("Success", "Prompt unshared successfully!");
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showPopup("Error", "Failed to unshare prompt: " + (data.error || "Unknown error"));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showPopup("Error", "Error unsharing prompt: " + error.message);
    });
}

// Attach unshare button listeners
function attachUnshareButtonListeners() {
    document.querySelectorAll('.unshare-button').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const promptId = button.getAttribute('data-prompt-id');
            showPopup(
                "Confirm Unshare",
                "Are you sure you want to unshare this prompt?",
                true,
                () => unsharePrompt(promptId),
                () => console.log("Unshare canceled.")
            );
        });
    });
}

// Function to save a prompt
function savePrompt(title, prompt) {
    const formData = new FormData();
    formData.append('title', title);
    formData.append('prompt', prompt);

    fetch('/save_prompt', {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (response.ok) {
            showPopup("Success", "Prompt saved successfully!");
        } else {
            throw new Error('Failed to save prompt.');
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        showPopup("Error", "Failed to save prompt: " + error.message);
    });
}

// Attach event listeners when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function () {
    attachCopyButtonListeners();
    attachSaveButtonListeners();
    attachUnshareButtonListeners();
});

// Re-attach event listeners after rendering prompts dynamically
function reattachEventListeners() {
    attachCopyButtonListeners();
    attachSaveButtonListeners();
    attachUnshareButtonListeners();
    // show-button listeners already in attachSaveButtonListeners
}
window.reattachEventListeners = reattachEventListeners;
