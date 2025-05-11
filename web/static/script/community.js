// Function to show the custom popup
// REMOVE LOCAL showPopup and closePopup

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
                    // Use global toast for copy confirmation
                    showToast("Prompt copied to clipboard!", "success");
                })
                .catch((err) => {
                    console.error('Failed to copy prompt:', err);
                    // Use global toast for copy error
                    showToast("Failed to copy prompt. Please try again.", "error");
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
            showAppPopup(
                "Confirm Save",
                `Are you sure you want to save "${title}" to your personal library?`,
                {
                    type: 'confirmation',
                    onConfirm: () => {
                        // If user clicks "Yes", save the prompt
                        savePrompt(title, prompt);
                    },
                    onCancel: () => {
                        // If user clicks "No", do nothing
                        console.log("Save canceled.");
                    }
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
            // Use new global popup for details view
            showAppPopup(title, content, { type: 'details' });
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
            // Use global toast for success
            showToast("Prompt unshared successfully!", "success");
            setTimeout(() => window.location.reload(), 1000);
        } else {
            // Use global toast for error
            showToast("Failed to unshare prompt: " + (data.error || "Unknown error"), "error");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Use global toast for error
        showToast("Error unsharing prompt: " + error.message, "error");
    });
}

// Attach unshare button listeners
function attachUnshareButtonListeners() {
    document.querySelectorAll('.unshare-button').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const promptId = button.getAttribute('data-prompt-id');
            showAppPopup(
                "Confirm Unshare",
                "Are you sure you want to unshare this prompt?",
                {
                    type: 'confirmation',
                    onConfirm: () => unsharePrompt(promptId),
                    onCancel: () => console.log("Unshare canceled.")
                }
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
    .then(response => response.json()) // Assuming /save_prompt returns JSON now
    .then(data => {
        if (data.success) {
            // Use global toast for success
            showToast(data.message || "Prompt saved successfully!", "success");
        } else {
            // Use global toast for error
            showToast(data.message || 'Failed to save prompt.', "error");
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        // Use global toast for error
        showToast("Failed to save prompt: " + error.message, "error");
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
