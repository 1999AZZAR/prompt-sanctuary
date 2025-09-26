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
    attachHistoryButtonListeners();
    attachSeeButtonListeners();
    // Note: ClipboardJS is initialized once and handles elements matching '.copy-button'
}

function reattachEventListeners() {
    // This function is called when DOM changes, e.g., after search results are rendered.
    // It re-attaches listeners to any new buttons.
    attachEditButtonListeners();
    attachDeleteButtonListeners();
    attachShareButtonListeners();
    attachHistoryButtonListeners();
    attachSeeButtonListeners();
}
// Version history: view and rollback
function attachHistoryButtonListeners() {
    document.querySelectorAll('.history-button:not(.listener-attached)').forEach(button => {
        button.addEventListener('click', function () {
            const promptId = this.getAttribute('data-random-val');
            const title = this.getAttribute('data-title') || 'Prompt';
            if (!promptId) {
                showToast('Missing prompt id.', 'error');
                return;
            }
            fetch(`/versions/${encodeURIComponent(promptId)}`)
                .then(res => res.json())
                .then(data => {
                    if (!data.success) throw new Error(data.error || 'Failed to load versions');
                    const versions = data.versions || [];
                    if (versions.length === 0) {
                        showToast('No versions found for this prompt.', 'info');
                        return;
                    }
                    const listHtml = versions.map(v => `
                        <div class="mb-4 p-3 rounded-lg bg-white/60 border border-white/40">
                            <div class="flex items-center justify-between mb-2">
                                <div class="text-sm text-slate-700">v${v.version_number} • ${escapeHtml(String(v.created_at))}</div>
                                <div class="space-x-2">
                                    <button class="px-3 py-1 rounded-md bg-slate-700 text-white text-xs preview-btn" data-v="${v.version_number}">Preview</button>
                                    <button class="px-3 py-1 rounded-md bg-amber-500 text-white text-xs rollback-btn" data-v="${v.version_number}">Restore</button>
                                </div>
                            </div>
                            <div class="text-sm font-semibold mb-1">${escapeHtml(v.title)}</div>
                            <div class="hidden text-sm whitespace-pre-wrap break-words version-content" data-v="${v.version_number}">${escapeHtml(v.prompt)}</div>
                        </div>
                    `).join('');

                    const content = `
                        <div>
                            <div class="text-sm text-slate-600 mb-3">History for: <strong>${escapeHtml(title)}</strong></div>
                            ${listHtml}
                        </div>
                    `;

                    showAppPopup('Version History', content, {
                        type: 'custom',
                        buttons: [
                            { text: 'Close', class: 'px-5 py-2.5 rounded-xl bg-slate-600 text-white', action: () => {} }
                        ],
                        size: 'xl'
                    });

                    // Attach preview and rollback handlers inside popup
                    setTimeout(() => {
                        document.querySelectorAll('.preview-btn').forEach(btn => {
                            btn.addEventListener('click', () => {
                                const v = btn.getAttribute('data-v');
                                const area = document.querySelector(`.version-content[data-v="${v}"]`);
                                if (area) {
                                    const isHidden = area.classList.toggle('hidden');
                                    if (!isHidden) {
                                        // Optionally render markdown and highlight
                                        try {
                                            const rendered = marked.parse(area.textContent, { mangle: false, headerIds: false });
                                            const safeHtml = DOMPurify.sanitize(rendered);
                                            area.innerHTML = safeHtml;
                                            if (window.Prism) Prism.highlightAllUnder(area);
                                        } catch (_) {}
                                    }
                                }
                            });
                        });
                        document.querySelectorAll('.rollback-btn').forEach(btn => {
                            btn.addEventListener('click', () => {
                                const v = btn.getAttribute('data-v');
                                const fd = new FormData();
                                fd.append('prompt_id', promptId);
                                fd.append('version_number', v);
                                fetch('/versions/rollback', { method: 'POST', body: fd })
                                    .then(res => res.json())
                                    .then(resp => {
                                        if (!resp.success) throw new Error(resp.error || 'Rollback failed');
                                        showToast('Restored this version.', 'success');
                                        setTimeout(() => window.location.reload(), 800);
                                    })
                                    .catch(err => showToast(err.message || 'Rollback failed', 'error'));
                            });
                        });
                    }, 0);
                })
                .catch(err => {
                    console.error(err);
                    showToast('Failed to load history.', 'error');
                });
        });
        button.classList.add('listener-attached');
    });
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
        headers: { 'X-CSRFToken': getCsrfTokenFromCookie() || '' },
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
            ...window.CSRF.getFormHeaders()
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
            ...window.CSRF.getFormHeaders()
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
            ...window.CSRF.getFormHeaders()
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

// See Details function - use details popup with wider size and markdown rendering
function attachSeeButtonListeners() {
    document.querySelectorAll('.see-button:not(.listener-attached)').forEach(button => {
        button.addEventListener('click', function () {
            const title = this.dataset.title;
            const promptContent = this.dataset.content || '';
            showAppPopup(title, promptContent, { type: 'details', size: 'xl' });
        });
        button.classList.add('listener-attached');
    });
}

