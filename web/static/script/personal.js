// Copy function on personal library
document.addEventListener('DOMContentLoaded', function () {
    // Initialize ClipboardJS for copy buttons
    // This targets buttons with class 'copy-button' which are typically on each prompt card
    var clipboard = new ClipboardJS('.copy-button', {
        text: function (trigger) {
            // Assuming the prompt content is in an attribute like 'data-clipboard-text'
            // or find it relative to the trigger if it's in a specific element.
            // For this example, let's assume it's directly on the button or a nearby element.
            // This might need adjustment based on your HTML structure.
            const promptCard = trigger.closest('.prompt-card'); // Or however you identify the card
            if (promptCard) {
                const promptTextElement = promptCard.querySelector('.prompt-text-content'); // Adjust selector
                if (promptTextElement) {
                    return promptTextElement.innerText;
                }
            }
            // Fallback if specific content not found, use data-clipboard-text if available
            return trigger.getAttribute('data-clipboard-text') || "No text to copy";
        }
    });

    clipboard.on('success', function (e) {
        e.clearSelection();
        showToast("Prompt copied to clipboard!", "success"); // Use global toast
    });

    clipboard.on('error', function (e) {
        showToast("Failed to copy prompt.", "error"); // Use global toast
    });


    // Re-attach event listeners for dynamically added elements or after search/filter
    const personalPromptsContainer = document.getElementById('personalPromptsContainer');
    if (personalPromptsContainer) {
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.addedNodes.length) {
                    reattachEventListeners(); // Re-attach to new nodes
                }
            });
        });
        observer.observe(personalPromptsContainer, { childList: true, subtree: true });
    }
    attachInitialEventListeners(); // Attach to initially loaded elements
});


function attachInitialEventListeners() {
    // Attach to existing buttons on load
    attachEditButtonListeners();
    attachDeleteButtonListeners();
    attachShareButtonListeners();
    attachSeeButtonListeners();
    // Note: ClipboardJS is initialized once and handles elements matching '.copy-button'
}

function reattachEventListeners() {
    // This function is called when DOM changes, e.g., after search results are rendered.
    // It re-attaches listeners to any new buttons.
    attachEditButtonListeners();
    attachDeleteButtonListeners();
    attachShareButtonListeners();
    attachSeeButtonListeners();
}


// Edit function
function attachEditButtonListeners() {
    document.querySelectorAll('.edit-button:not(.listener-attached)').forEach(button => {
        button.addEventListener('click', function () {
            const randomVal = button.getAttribute('data-random-val');
            const title = button.getAttribute('data-title');
            const prompt = button.getAttribute('data-prompt');
            const tags = button.getAttribute('data-tags') || ""; // Get tags
            openEditModal(randomVal, title, prompt, tags);
        });
        button.classList.add('listener-attached');
    });
}

// Function to open the edit popup - MODIFIED TO USE showAppPopup
function openEditModal(randomVal, title, prompt, tags) {
    // Wrapped existing content in a single parent div
    const contentHtml = `
        <div> 
            <input type="hidden" id="editRandomValModal" value="${randomVal}">
            <div class="mb-4">
                <label for="editTitleModal" class="block mb-2 text-sm font-medium text-gray-200">Title:</label>
                <input type="text" id="editTitleModal" value="${escapeHTML(title)}" class="w-full p-2 bg-gray-700 border border-gray-600 text-white rounded-lg focus:ring-blue-500 focus:border-blue-500 placeholder-gray-400">
            </div>
            <div class="mb-6">
                <label for="editPromptModal" class="block mb-2 text-sm font-medium text-gray-200">Prompt:</label>
                <textarea id="editPromptModal" rows="12" class="w-full p-2 bg-gray-700 border border-gray-600 text-white rounded-lg focus:ring-blue-500 focus:border-blue-500 placeholder-gray-400">${escapeHTML(prompt)}</textarea>
            </div>
        </div>
    `;

    const editButtons = [
        {
            text: "Save Changes",
            action: function() {
                const newRandomVal = document.getElementById('editRandomValModal').value;
                const newTitle = document.getElementById('editTitleModal').value;
                const newPrompt = document.getElementById('editPromptModal').value;
                if (!newTitle.trim()) {
                    showToast("Title cannot be empty.", "error");
                    const titleInput = document.getElementById('editTitleModal');
                    if (titleInput) titleInput.focus();
                    return false; 
                }
                saveEditedPrompt(newRandomVal, newTitle, newPrompt);
            }
        },
        {
            text: "Cancel",
            action: function() {
                closeAppPopup(); 
            }
        }
    ];

    showAppPopup("Edit Prompt", contentHtml, { 
        type: 'custom', 
        buttons: editButtons,
        size: '85vw'
    });
}

function escapeHTML(str) {
    if (typeof str !== 'string') return '';
    return str.replace(/[&<>\\"']/g, function (match) { // Added backslash for double quote
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        }[match];
    });
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
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || "Prompt updated successfully!", "success");
            closeAppPopup(); // Ensure popup is closed on success
            setTimeout(() => window.location.reload(), 1000); 
        } else {
            showToast(data.message || "Failed to update prompt.", "error");
            // Keep the edit modal open on failure so the user can correct and retry.
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        showToast("Error updating prompt: " + error.message, "error");
        // Keep the edit modal open on failure.
    });
}

// Delete function
function attachDeleteButtonListeners() {
    document.querySelectorAll('.delete-button:not(.listener-attached)').forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault(); 
            const randomVal = button.getAttribute('data-random-val');
            openDeleteConfirmationModal(randomVal);
        });
        button.classList.add('listener-attached');
    });
}

// Function to confirm deletion - MODIFIED TO USE showAppPopup
function openDeleteConfirmationModal(randomVal) {
    const contentHtml = "<p class='text-gray-100'>Are you sure you want to delete this prompt? This action cannot be undone.</p>"; // text-gray-100 for better visibility
    
    // Base classes from showAppPopup for consistent look
    const baseButtonClass = 'px-5 py-2.5 rounded-lg transition duration-200 text-sm font-medium w-full sm:w-auto';
    const deleteButtonClass = `bg-red-600 hover:bg-red-700 text-white ${baseButtonClass}`;
    const cancelButtonClass = `bg-gray-600 hover:bg-gray-700 text-white ${baseButtonClass}`;

    const deleteButtons = [
        {
            text: "Delete",
            class: deleteButtonClass,
            action: function() {
                deletePrompt(randomVal);
                // closeAppPopup(); // showAppPopup handles close by default unless action returns false
            }
        },
        {
            text: "Cancel",
            class: cancelButtonClass,
            action: function() {
                closeAppPopup(); // Explicitly close, or rely on default
            }
        }
    ];
    showAppPopup("Confirm Deletion", contentHtml, { 
        type: 'custom', 
        buttons: deleteButtons 
    });
}

// Function to delete a prompt
function deletePrompt(randomVal) {
    fetch('/delete_prompt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'prompt_id=' + encodeURIComponent(randomVal),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || "Prompt deleted successfully!", "success");
            setTimeout(() => window.location.reload(), 1000); 
        } else {
            showToast(data.message || "Failed to delete prompt.", "error");
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        showToast("Error deleting prompt: " + error.message, "error");
    });
}

// Share function
function attachShareButtonListeners() {
    document.querySelectorAll('.share-button:not(.listener-attached)').forEach(button => {
        button.addEventListener('click', function () {
            // CORRECTED: Read prompt ID from data-prompt-id attribute
            const promptId = this.dataset.promptId; 
            const title = this.dataset.title;
            // Prompt content is correctly read from data-prompt based on HTML
            const promptContent = this.dataset.prompt; 
            const isShared = this.classList.contains('unshare-action');

            if (!promptId || !title || !promptContent) {
                console.error('Share button is missing data attributes:', this.dataset);
                showToast("Cannot share: critical data missing from button.", "error");
                return;
            }

            if (isShared) {
                unsharePrompt(promptId, this);
            } else {
                sharePrompt(promptId, title, promptContent, this);
            }
        });
        button.classList.add('listener-attached');
    });
}


function sharePrompt(promptId, title, promptContent, buttonElement) {
    const data = {
        prompt_id: promptId,
        title: title,
        prompt: promptContent
        // Tags are not explicitly sent here, community prompts might not use them directly or derive them.
    };

    fetch('/share_prompt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showToast("Prompt shared successfully!", "success");
            if(buttonElement) {
                buttonElement.textContent = 'Unshare';
                buttonElement.classList.remove('share-action');
                buttonElement.classList.add('unshare-action');
                // Optionally update a visual indicator
            }
        } else {
            showToast(result.error || "Failed to share prompt.", "error");
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        showToast("Error sharing prompt: " + error.message, "error");
            });
        }

function unsharePrompt(promptId, buttonElement) {
    fetch('/unshare_prompt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt_id: promptId }),
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showToast("Prompt unshared successfully!", "success");
             if(buttonElement) {
                buttonElement.textContent = 'Share';
                buttonElement.classList.remove('unshare-action');
                buttonElement.classList.add('share-action');
                 // Optionally update a visual indicator
            }
        } else {
            showToast(result.error || "Failed to unshare prompt.", "error");
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        showToast("Error unsharing prompt: " + error.message, "error");
    });
}

// See Details function - MODIFIED TO USE showAppPopup
function attachSeeButtonListeners() {
    document.querySelectorAll('.see-button:not(.listener-attached)').forEach(button => {
        button.addEventListener('click', function () {
            const title = this.dataset.title;
            const promptContent = this.dataset.content;
            
            // Modified detailHtml to remove max-h-60 and overflow-auto for consistency with community.js type: 'details' behavior
            const detailHtml = `
                <div>
                    <strong class="block text-sm font-medium text-gray-100 mb-1">Prompt:</strong>
                    <div class="mt-1 p-2 bg-gray-700/50 rounded-md text-gray-300 whitespace-pre-wrap break-words">
                        ${escapeHTML(promptContent || '')}
                    </div>
                </div>
            `;

            const customButtons = [
                {
                    text: "Copy Prompt",
                    action: () => {
                        navigator.clipboard.writeText(promptContent || '')
                            .then(() => showToast('Prompt copied to clipboard!', 'success'))
                            .catch(err => {
                                console.error('Failed to copy prompt:', err);
                                showToast('Failed to copy prompt.', 'error');
                            });
                    }
                },
                {
                    text: "Close",
                    action: () => {
                        closeAppPopup(); 
                    }
                }
            ];
            
            showAppPopup(title, detailHtml, { 
                type: 'custom', // Still custom because we are defining the full HTML and buttons
                buttons: customButtons 
                // No size option, defaults to 'md' like community.js type: 'details'
            }); 
        });
        button.classList.add('listener-attached');
    });
}

