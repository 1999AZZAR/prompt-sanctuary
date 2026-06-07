// Copy function on personal library
function attachCopyButtonListeners() {
    // Copy buttons use the native Clipboard API. The data-clipboard-text
    // attribute on the button is the source of truth.
    document.querySelectorAll('.copy-button:not(.listener-attached)').forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const text = button.getAttribute('data-clipboard-text') || '';
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text)
                    .then(() => showToast("Prompt copied to clipboard!", "success"))
                    .catch(() => showToast("Failed to copy prompt.", "error"));
            } else {
                showToast("Clipboard not available in this browser.", "error");
            }
        });
        button.classList.add('listener-attached');
    });
}

document.addEventListener('DOMContentLoaded', function () {
    attachCopyButtonListeners();

    // Re-attach event listeners for dynamically added elements or after search/filter
    const personalPromptsContainer = document.getElementById('savedPromptsContainer');
    if (personalPromptsContainer) {
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.addedNodes.length) {
                    reattachEventListeners();
                }
            });
        });
        observer.observe(personalPromptsContainer, { childList: true, subtree: true });
    }
    attachInitialEventListeners();
});

// Expose reattach on window so the inline search script in personal.html
// can re-attach listeners after a search re-render. Aliased to match
// the community library's pattern (which exposes `reattachCommunityListeners`).
window.reattachPersonalListeners = reattachEventListeners;
window.reattachEventListeners = reattachEventListeners;

// HTML-escape helper used by the inline templates in this file
// (history popup, edit modal).
function escapeHtml(str) {
    if (typeof str !== 'string') return '';
    return str.replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#039;');
}


function attachInitialEventListeners() {
    attachCopyButtonListeners();
    attachEditButtonListeners();
    attachDeleteButtonListeners();
    attachShareButtonListeners();
    attachHistoryButtonListeners();
    attachSeeButtonListeners();
    attachUpdateSharedButtonListeners();
}

function reattachEventListeners() {
    attachCopyButtonListeners();
    attachEditButtonListeners();
    attachDeleteButtonListeners();
    attachShareButtonListeners();
    attachHistoryButtonListeners();
    attachSeeButtonListeners();
    attachUpdateSharedButtonListeners();
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
                        <div class="card card--compact card--sunken" style="margin-bottom: var(--p-sp-3);">
                            <div class="cluster cluster--between" style="margin-bottom: var(--p-sp-2);">
                                <div class="t-body-sm t-muted"><strong class="t-mono">v${v.version_number}</strong> · ${escapeHtml(String(v.created_at))}</div>
                                <div class="cluster" style="gap: var(--p-sp-2);">
                                    <button class="btn btn--tertiary btn--sm preview-btn" data-v="${v.version_number}"><i class="fa-solid fa-eye"></i> Preview</button>
                                    <button class="btn btn--primary btn--sm rollback-btn" data-v="${v.version_number}"><i class="fa-solid fa-rotate-left"></i> Restore</button>
                                </div>
                            </div>
                            <div class="t-body-sm t-strong" style="margin-bottom: var(--p-sp-2); word-break: break-word;">${escapeHtml(v.title)}</div>
                            <div class="hidden code-block" data-v="${v.version_number}" style="margin-top: var(--p-sp-2); font-size: var(--p-fs-body-sm);">${escapeHtml(v.prompt)}</div>
                        </div>
                    `).join('');

                    const content = `
                        <div>
                            <div class="t-body-sm t-muted" style="margin-bottom: var(--p-sp-4);">History for: <strong>${escapeHtml(title)}</strong></div>
                            ${listHtml}
                        </div>
                    `;

                    showAppPopup('Version History', content, {
                        type: 'custom',
                        buttons: [
                            { text: 'Close', class: 'btn--secondary', action: function () { return true; } }
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
        <div class="stack">
            <input type="hidden" id="editRandomValModal" value="${randomVal}">
            <div class="field">
                <label class="field__label" for="editTitleModal">Title</label>
                <input class="input" type="text" id="editTitleModal" value="${escapeHTML(title)}" autocomplete="off">
            </div>
            <div class="field">
                <label class="field__label" for="editPromptModal">Prompt</label>
                <textarea class="textarea input--mono" id="editPromptModal" rows="14" style="resize: vertical;">${escapeHTML(prompt)}</textarea>
            </div>
        </div>
    `;

    const editButtons = [
        {
            text: "Save changes",
            class: "btn--primary",
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
                return true;
            }
        },
        {
            text: "Cancel",
            class: "btn--secondary",
            action: function() {
                return true;
            }
        }
    ];

    showAppPopup("Edit prompt", contentHtml, {
        type: 'custom',
        buttons: editButtons,
        size: '720px'
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
        headers: window.CSRF.getFormHeaders(),
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
    const contentHtml = '<p>Are you sure you want to delete this prompt? This action cannot be undone.</p>';

    const deleteButtons = [
        {
            text: "Delete",
            class: "btn--destructive",
            action: function() {
                deletePrompt(randomVal);
                return true;
            }
        },
        {
            text: "Cancel",
            class: "btn--secondary",
            action: function() {
                return true;
            }
        }
    ];
    showAppPopup("Delete prompt", contentHtml, {
        type: 'custom',
        buttons: deleteButtons,
        size: 'sm'
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
    // Handle share buttons (need title and prompt data)
    document.querySelectorAll('.share-button:not(.listener-attached)').forEach(button => {
        button.addEventListener('click', function (e) {
            // The button may have transitioned to .unshare-button between the
            // time the listener was attached and the click event firing (e.g.
            // a successful share flipped the class). Bail so we don't fire
            // the stale share handler with now-deleted data attributes.
            if (!this.classList.contains('share-button')) return;
            const promptId = this.dataset.promptId;
            const title = this.dataset.title;
            const promptContent = this.dataset.prompt;

            if (!promptId || !title || !promptContent) {
                console.error('Share button is missing data attributes:', this.dataset);
                showToast("Cannot share: critical data missing from button.", "error");
                return;
            }

            sharePrompt(promptId, title, promptContent, this);
        });
        button.classList.add('listener-attached');
    });

    // Handle unshare buttons (only need promptId)
    document.querySelectorAll('.unshare-button:not(.listener-attached)').forEach(button => {
        button.addEventListener('click', function () {
            // See note on the share handler — the button may have transitioned
            // back to .share-button since this listener was attached.
            if (!this.classList.contains('unshare-button')) return;
            const promptId = this.dataset.promptId;
            // The unshare button carries only promptId; read title and body
            // from the parent card so we can restore the share button state
            // (data-title, data-prompt) on success.
            const card = this.closest('.prompt-box') || this.closest('.card');
            const titleEl = card && card.querySelector('.prompt-box__title');
            const bodyEl = card && card.querySelector('.prompt-text');
            const title = titleEl ? titleEl.textContent : '';
            const promptContent = bodyEl ? bodyEl.textContent : '';

            if (!promptId) {
                console.error('Unshare button is missing promptId:', this.dataset);
                showToast("Cannot unshare: missing prompt ID.", "error");
                return;
            }

            unsharePrompt(promptId, title, promptContent, this);
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
            // Handle different success messages from backend
            if (result.message) {
                if (result.message.includes("already shared")) {
                    showToast("Prompt is already shared!", "info");
                } else if (result.message.includes("updated")) {
                    showToast("Shared prompt updated!", "success");
                } else {
                    showToast("Prompt shared successfully!", "success");
                }
            } else {
                showToast("Prompt shared successfully!", "success");
            }

            if(buttonElement) {
                buttonElement.textContent = 'Unshare';
                buttonElement.classList.remove('share-button');
                buttonElement.classList.add('unshare-button');
                // Update the span text inside the button
                const spanElement = buttonElement.querySelector('span');
                if (spanElement) {
                    spanElement.textContent = 'Unshare';
                }
                // Remove share-specific data attributes
                delete buttonElement.dataset.title;
                delete buttonElement.dataset.prompt;
                // Update aria-label
                buttonElement.setAttribute('aria-label', `Unshare prompt: ${title}`);
                // The button is now an unshare-button but already has the
                // `listener-attached` marker from the share handler. Clear
                // it so attachShareButtonListeners can wire the unshare
                // handler on the next pass.
                buttonElement.classList.remove('listener-attached');
                setTimeout(() => {
                    attachShareButtonListeners();
                }, 0);
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

function unsharePrompt(promptId, title, promptContent, buttonElement) {
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
                buttonElement.classList.remove('unshare-button');
                buttonElement.classList.add('share-button');
                // Update the span text inside the button
                const spanElement = buttonElement.querySelector('span');
                if (spanElement) {
                    spanElement.textContent = 'Share';
                }
                // Update data attributes for sharing
                buttonElement.dataset.title = title;
                buttonElement.dataset.prompt = promptContent;
                // Update aria-label
                buttonElement.setAttribute('aria-label', `Share prompt: ${title}`);
                // Clear the marker so the share handler can be wired.
                buttonElement.classList.remove('listener-attached');
                setTimeout(() => {
                    attachShareButtonListeners();
                }, 0);
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

// Update Shared function
function updateSharedPrompt(promptId, title, promptContent, buttonElement) {
    const data = {
        prompt_id: promptId,
        title: title,
        prompt: promptContent
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
            showToast("Prompt updated successfully!", "success");
            if(buttonElement) {
                buttonElement.textContent = 'Unshare';
                buttonElement.classList.remove('update-shared-button');
                buttonElement.classList.add('unshare-button');
                buttonElement.classList.remove('bg-yellow-100', 'text-yellow-700', 'hover:bg-yellow-200');
                buttonElement.classList.add('bg-red-100', 'text-red-700', 'hover:bg-red-200');
            }
        } else {
            showToast(result.error || "Failed to update prompt.", "error");
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        showToast("Error updating prompt: " + error.message, "error");
    });
}

// Update Shared Button listeners
function attachUpdateSharedButtonListeners() {
    document.querySelectorAll('.update-shared-button:not(.listener-attached)').forEach(button => {
        button.addEventListener('click', function () {
            const promptId = this.dataset.promptId;
            const title = this.dataset.title;
            const promptContent = this.dataset.prompt;

            if (!promptId || !title || !promptContent) {
                console.error('Update shared button is missing data attributes:', this.dataset);
                showToast("Cannot update: critical data missing from button.", "error");
                return;
            }

            updateSharedPrompt(promptId, title, promptContent, this);
        });
        button.classList.add('listener-attached');
    });
}

// See Details function - use details popup with wider size and markdown rendering
function attachSeeButtonListeners() {
    document.querySelectorAll('.see-button:not(.listener-attached)').forEach(button => {
        button.addEventListener('click', function () {
            const title = this.dataset.title;
            const promptContent = this.dataset.content || '';
            const card = this.closest('.prompt-box') || this.closest('.card');
            const kindEl = card && card.querySelector('.badge');
            const kind = kindEl ? (kindEl.textContent || '').trim() : 'Prompt';
            const labelEl = card && card.querySelector('.index');
            const label = labelEl ? (labelEl.textContent || '').trim() : 'Preview';
            const badgeHtml = kindEl ? kindEl.outerHTML : '';
            const tagsAttr = this.getAttribute('data-tags') || '';
            const tags = tagsAttr ? tagsAttr.split(',').map(s => s.trim()).filter(Boolean) : [];
            showAppPopup(title, promptContent, {
                type: 'details',
                size: 'xl',
                kind: kind,
                label: label,
                badgeHtml: badgeHtml,
                tags: tags
            });
        });
        button.classList.add('listener-attached');
    });
}

