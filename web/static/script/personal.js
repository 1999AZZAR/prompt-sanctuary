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
                    .then(() => showToast(_("Prompt copied to clipboard!"), "success"))
                    .catch(() => showToast(_("Failed to copy prompt."), "error"));
            } else {
                showToast(_("Clipboard not available in this browser."), "error");
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
                showToast(_('Missing prompt id.'), 'error');
                return;
            }
            fetch(`/versions/${encodeURIComponent(promptId)}`)
                .then(res => res.json())
                .then(data => {
                    if (!data.success) throw new Error(data.error || 'Failed to load versions');
                    const versions = data.versions || [];
                    if (versions.length === 0) {
                        showToast(_('No versions found for this prompt.'), 'info');
                        return;
                    }
                    // Sort newest first so the most recent version is at the top.
                    const sorted = versions.slice().sort((a, b) => b.version_number - a.version_number);
                    const listHtml = sorted.map(v => `
                        <div class="card card--compact card--sunken" style="margin-bottom: var(--p-sp-3);">
                            <div class="cluster cluster--between" style="margin-bottom: var(--p-sp-2); gap: var(--p-sp-3);">
                                <div class="cluster" style="gap: var(--p-sp-2); align-items: baseline; min-width: 0;">
                                    <span class="badge"><i class="fa-solid fa-code-branch"></i> v${v.version_number}</span>
                                    <span class="t-body-sm t-muted">${escapeHtml(String(v.created_at))}</span>
                                </div>
                                <div class="cluster" style="gap: var(--p-sp-2);">
                                    <button type="button" class="btn btn--tertiary btn--sm version-preview-btn" data-v="${v.version_number}"><i class="fa-solid fa-eye"></i> ${_("Preview")}</button>
                                    <button type="button" class="btn btn--primary btn--sm rollback-btn" data-v="${v.version_number}"><i class="fa-solid fa-rotate-left"></i> ${_("Restore")}</button>
                                </div>
                            </div>
                            <div class="t-body-sm t-strong" style="word-break: break-word;">${escapeHtml(v.title)}</div>
                        </div>
                    `).join('');

                    // The modal holds two views that share one body: the list
                    // and a single version's preview. Showing a preview swaps
                    // the visible view and rewrites the footer (Preview row
                    // becomes Back to list). The list and preview state are
                    // driven by a `mode` variable.
                    const versionCount = sorted.length;
                    const versionText = versionCount === 1
                        ? _("1 version")
                        : _("%(n)s versions", { n: versionCount });
                    const currentText = _("current is v%(v)s", { v: sorted[0].version_number });
                    const content = `
                        <div id="historyListView">
                            <div class="t-body-sm t-muted" style="margin-bottom: var(--p-sp-4);">${versionText} · ${currentText}</div>
                            ${listHtml}
                        </div>
                        <div id="historyPreviewView" hidden>
                            <div class="preview-header" style="margin-bottom: var(--p-sp-3);">
                                <div class="preview-header__eyebrow">
                                    <span>${_("Version")}</span>
                                    <span id="historyPreviewLabel"></span>
                                </div>
                                <h2 class="preview-header__title" id="historyPreviewTitle"></h2>
                            </div>
                            <pre class="preview-body" id="historyPreviewBody" style="min-height: 240px; max-height: 56vh;"></pre>
                        </div>
                    `;

                    const buttons = [
                        {
                            text: _("Preview"),
                            class: "btn--tertiary",
                            action: function () { return false; }
                        },
                        {
                            text: _("Back to list"),
                            class: "btn--tertiary",
                            action: function () {
                                const popup = document.getElementById('app-global-popup');
                                if (!popup) return true;
                                document.getElementById('historyListView').hidden = false;
                                document.getElementById('historyPreviewView').hidden = true;
                                Array.from(popup.querySelectorAll('.modal__footer button')).forEach(b => {
                                    b.hidden = b.dataset.historyLabel !== 'Close';
                                });
                                return false;
                            }
                        },
                        {
                            text: _("Close"),
                            class: "btn--secondary",
                            action: function () { return true; }
                        }
                    ];

                    showAppPopup(_('Version History'), content, {
                        type: 'custom',
                        buttons: buttons,
                        size: 'xl'
                    });

                    // After the modal is mounted: tag footer buttons, wire
                    // the per-version Preview/Restore handlers.
                    setTimeout(() => {
                        const popup = document.getElementById('app-global-popup');
                        if (popup) {
                            const footer = popup.querySelector('.modal__footer');
                            if (footer) {
                                Array.from(footer.querySelectorAll('button')).forEach(btn => {
                                    const txt = (btn.textContent || '').trim();
                                    if (txt.startsWith(_('Preview')) && !txt.includes(_('Back to list'))) btn.dataset.historyLabel = 'Preview';
                                    else if (txt.includes(_('Back to list'))) btn.dataset.historyLabel = 'Back to list';
                                    else if (txt.includes(_('Close'))) btn.dataset.historyLabel = 'Close';
                                });
                                // Hide the no-op top "Preview" button. The
                                // per-version rows are the actual entry points.
                                const topPreview = footer.querySelector('button[data-history-label="Preview"]');
                                if (topPreview) topPreview.hidden = true;
                            }
                        }

                        document.querySelectorAll('.version-preview-btn').forEach(btn => {
                            btn.addEventListener('click', () => {
                                const v = Number(btn.getAttribute('data-v'));
                                const version = sorted.find(x => x.version_number === v);
                                if (!version) return;
                                const popup = document.getElementById('app-global-popup');
                                if (!popup) return;
                                document.getElementById('historyListView').hidden = true;
                                document.getElementById('historyPreviewView').hidden = false;
                                document.getElementById('historyPreviewTitle').textContent = version.title;
                                document.getElementById('historyPreviewLabel').textContent = 'v' + version.version_number + ' · ' + String(version.created_at);
                                document.getElementById('historyPreviewBody').textContent = version.prompt;
                                // Footer: keep only the "Back to list" + "Close" buttons.
                                Array.from(popup.querySelectorAll('.modal__footer button')).forEach(b => {
                                    b.hidden = b.dataset.historyLabel === 'Preview';
                                });
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
                                        if (!resp.success) throw new Error(resp.error || _('Rollback failed'));
                                        showToast(_('Restored v%(v)s.', { v: v }), 'success');
                                        setTimeout(() => window.location.reload(), 800);
                                    })
                                    .catch(err => showToast(err.message || _('Rollback failed'), 'error'));
                            });
                        });
                    }, 0);
                })
                .catch(err => {
                    console.error(err);
                    showToast(_('Failed to load history.'), 'error');
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

// Function to open the edit popup - uses showAppPopup with a refined layout:
// eyebrow with the original title, live char/word/line counts, a Preview
// button that swaps the modal body to a preview view (Back to edit returns
// to the form), a Revert button to reset the form, and Cmd/Ctrl+Enter to save.
function openEditModal(randomVal, title, prompt, tags) {
    // Escape user-controlled strings for safe interpolation into the markup.
    const safeTitle = escapeHTML(title || '');
    const safePrompt = escapeHTML(prompt || '');

    const formHtml = `
        <div class="stack" id="editFormView">
            <input type="hidden" id="editRandomValModal" value="${escapeHTML(randomVal)}">
            <div class="cluster" style="gap: var(--p-sp-2); align-items: center; color: var(--p-color-text-subdued); font-size: var(--p-fs-eyebrow); text-transform: uppercase; letter-spacing: 0.16em;">
                <i class="fa-solid fa-pen" aria-hidden="true"></i>
                <span>${_("Editing")}</span>
                <span class="t-strong" style="text-transform: none; letter-spacing: 0; color: var(--p-color-text);">&ldquo;${safeTitle}&rdquo;</span>
            </div>
            <div class="field">
                <label class="field__label" for="editTitleModal">${_("Title")}</label>
                <input class="input" type="text" id="editTitleModal" value="${safeTitle}" autocomplete="off" maxlength="200">
            </div>
            <div class="field">
                <div class="cluster cluster--between" style="margin-bottom: var(--p-sp-2); align-items: baseline;">
                    <label class="field__label" for="editPromptModal" style="margin: 0;">${_("Prompt body")}</label>
                    <span class="t-body-sm t-muted t-mono" id="editCountStrip">0 chars &middot; 0 words &middot; 1 line</span>
                </div>
                <textarea class="textarea input--mono" id="editPromptModal" rows="18" style="resize: vertical; min-height: 280px;">${safePrompt}</textarea>
            </div>
        </div>
        <div class="stack" id="editPreviewView" hidden>
            <div class="preview-header" style="margin-bottom: var(--p-sp-3);">
                <div class="preview-header__eyebrow">
                    <span>${_("Preview")}</span>
                    <span>${_("Edit preview")}</span>
                </div>
                <h2 class="preview-header__title" id="editPreviewTitle"></h2>
            </div>
            <pre class="preview-body" id="editPreviewBody" style="min-height: 280px; max-height: 56vh;"></pre>
        </div>
    `;

    let mode = 'form';  // 'form' | 'preview'

    const editButtons = [
        {
            text: _("Preview"),
            class: "btn--tertiary",
            action: function() {
                if (mode === 'preview') return false;
                const newTitle = document.getElementById('editTitleModal').value;
                const newPrompt = document.getElementById('editPromptModal').value;
                if (!newTitle.trim()) {
                    showToast(_("Add a title before previewing."), "error");
                    document.getElementById('editTitleModal').focus();
                    return false;
                }
                document.getElementById('editPreviewTitle').textContent = newTitle;
                document.getElementById('editPreviewBody').textContent = newPrompt;
                document.getElementById('editFormView').hidden = true;
                document.getElementById('editPreviewView').hidden = false;
                mode = 'preview';
                refreshEditFooter();
                return false;
            }
        },
        {
            text: _("Back to edit"),
            class: "btn--tertiary",
            action: function() {
                if (mode === 'form') return false;
                document.getElementById('editFormView').hidden = false;
                document.getElementById('editPreviewView').hidden = true;
                mode = 'form';
                refreshEditFooter();
                return false;
            }
        },
        {
            text: _("Revert"),
            class: "btn--ghost",
            action: function() {
                document.getElementById('editTitleModal').value = title || '';
                document.getElementById('editPromptModal').value = prompt || '';
                updateEditCounts();
                const ta = document.getElementById('editPromptModal');
                if (ta) ta.dispatchEvent(new Event('input'));
                showToast(_("Reverted to the saved version."), "info");
                return false;
            }
        },
        {
            text: _("Cancel"),
            class: "btn--secondary",
            action: function() {
                return true;
            }
        },
        {
            text: _("Save changes"),
            class: "btn--primary",
            action: function() {
                const newRandomVal = document.getElementById('editRandomValModal').value;
                const newTitle = document.getElementById('editTitleModal').value;
                const newPrompt = document.getElementById('editPromptModal').value;
                if (!newTitle.trim()) {
                    showToast(_("Title cannot be empty."), "error");
                    const titleInput = document.getElementById('editTitleModal');
                    if (titleInput) titleInput.focus();
                    return false;
                }
                saveEditedPrompt(newRandomVal, newTitle, newPrompt);
                return true;
            }
        }
    ];

    // The full set of footer buttons, in display order. We swap the visible
    // subset between the form view and the preview view by rebuilding the
    // modal footer on demand (see refreshEditFooter).
    const FORM_BUTTONS = [_('Preview'), _('Revert'), _('Cancel'), _('Save changes')];
    const PREVIEW_BUTTONS = [_('Back to edit'), _('Revert'), _('Cancel'), _('Save changes')];

    function refreshEditFooter() {
        const popup = document.getElementById('app-popup');
        if (!popup) return;
        const footer = popup.querySelector('.modal__footer');
        if (!footer) return;
        const labels = mode === 'preview' ? PREVIEW_BUTTONS : FORM_BUTTONS;
        const buttons = Array.from(footer.querySelectorAll('button'));
        buttons.forEach(b => {
            const label = (b.dataset.editLabel || b.textContent || '').trim();
            b.hidden = !labels.includes(label);
        });
    }

    // Tag each footer button with the label it represents so refreshEditFooter
    // can find them by name in refreshEditFooter.
    editButtons.forEach(b => { b._editLabel = b.text; });

    showAppPopup(_("Edit prompt"), formHtml, {
        type: 'custom',
        buttons: editButtons,
        size: '800px'
    });

    // Live count + keyboard shortcut + focus, after the modal is in the DOM.
    setTimeout(() => {
        const titleInput = document.getElementById('editTitleModal');
        const bodyInput = document.getElementById('editPromptModal');
        if (titleInput) titleInput.focus();
        const handler = () => updateEditCounts();
        if (bodyInput) bodyInput.addEventListener('input', handler);
        if (titleInput) titleInput.addEventListener('input', handler);
        // After the modal is mounted, label each footer button by its
        // human-readable text so refreshEditFooter can find it by name.
        const popup = document.getElementById('app-global-popup');
        if (popup) {
            const footer = popup.querySelector('.modal__footer');
            if (footer) {
                Array.from(footer.querySelectorAll('button')).forEach(btn => {
                    const txt = (btn.textContent || '').trim();
                    if (txt.includes(_('Back to edit'))) btn.dataset.editLabel = 'Back to edit';
                    else if (txt.startsWith(_('Preview'))) btn.dataset.editLabel = 'Preview';
                    else if (txt.includes(_('Revert'))) btn.dataset.editLabel = 'Revert';
                    else if (txt.includes(_('Cancel'))) btn.dataset.editLabel = 'Cancel';
                    else if (txt.includes(_('Save changes'))) btn.dataset.editLabel = 'Save changes';
                });
            }
            // Cmd/Ctrl+Enter saves the form from anywhere in the modal.
            popup.addEventListener('keydown', function (e) {
                if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                    e.preventDefault();
                    const saveBtn = Array.from(popup.querySelectorAll('button')).find(b => (b.dataset.editLabel || '') === 'Save changes');
                    if (saveBtn) saveBtn.click();
                }
            });
        }
        updateEditCounts();
    }, 0);
}

// Live char/word/line counter for the edit modal.
function updateEditCounts() {
    const strip = document.getElementById('editCountStrip');
    const body = document.getElementById('editPromptModal');
    if (!strip || !body) return;
    const text = body.value || '';
    const chars = text.length;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    const lines = text === '' ? 1 : text.split('\n').length;
    const fmt = (n) => Number(n).toLocaleString();
    strip.textContent = `${fmt(chars)} chars · ${fmt(words)} words · ${fmt(lines)} line${lines === 1 ? '' : 's'}`;
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
            showToast(data.message || _("Prompt updated successfully!"), "success");
            closeAppPopup(); // Ensure popup is closed on success
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showToast(data.message || _("Failed to update prompt."), "error");
            // Keep the edit modal open on failure so the user can correct and retry.
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        showToast(_("Error updating prompt: %(message)s", { message: error.message }), "error");
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
    const contentHtml = '<p>' + _("Are you sure you want to delete this prompt? This action cannot be undone.") + '</p>';

    const deleteButtons = [
        {
            text: _("Delete"),
            class: "btn--destructive",
            action: function() {
                deletePrompt(randomVal);
                return true;
            }
        },
        {
            text: _("Cancel"),
            class: "btn--secondary",
            action: function() {
                return true;
            }
        }
    ];
    showAppPopup(_("Delete prompt"), contentHtml, {
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
            showToast(data.message || _("Prompt deleted successfully!"), "success");
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showToast(data.message || _("Failed to delete prompt."), "error");
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        showToast(_("Error deleting prompt: %(message)s", { message: error.message }), "error");
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
                showToast(_("Cannot share: critical data missing from button."), "error");
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
                showToast(_("Cannot unshare: missing prompt ID."), "error");
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
                    showToast(_("Prompt is already shared!"), "info");
                } else if (result.message.includes("updated")) {
                    showToast(_("Shared prompt updated!"), "success");
                } else {
                    showToast(_("Prompt shared successfully!"), "success");
                }
            } else {
                showToast(_("Prompt shared successfully!"), "success");
            }

            if(buttonElement) {
                const unshareLabel = _("Unshare");
                buttonElement.textContent = unshareLabel;
                buttonElement.classList.remove('share-button');
                buttonElement.classList.add('unshare-button');
                // Update the span text inside the button
                const spanElement = buttonElement.querySelector('span');
                if (spanElement) {
                    spanElement.textContent = unshareLabel;
                }
                // Remove share-specific data attributes
                delete buttonElement.dataset.title;
                delete buttonElement.dataset.prompt;
                // Update aria-label
                buttonElement.setAttribute('aria-label', _("Unshare prompt: %(title)s", { title: title }));
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
            showToast(result.error || _("Failed to share prompt."), "error");
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        showToast(_("Error sharing prompt: %(message)s", { message: error.message }), "error");
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
            showToast(_("Prompt unshared successfully!"), "success");
            if(buttonElement) {
                const shareLabel = _("Share");
                buttonElement.textContent = shareLabel;
                buttonElement.classList.remove('unshare-button');
                buttonElement.classList.add('share-button');
                // Update the span text inside the button
                const spanElement = buttonElement.querySelector('span');
                if (spanElement) {
                    spanElement.textContent = shareLabel;
                }
                // Update data attributes for sharing
                buttonElement.dataset.title = title;
                buttonElement.dataset.prompt = promptContent;
                // Update aria-label
                buttonElement.setAttribute('aria-label', _("Share prompt: %(title)s", { title: title }));
                // Clear the marker so the share handler can be wired.
                buttonElement.classList.remove('listener-attached');
                setTimeout(() => {
                    attachShareButtonListeners();
                }, 0);
            }
        } else {
            showToast(result.error || _("Failed to unshare prompt."), "error");
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        showToast(_("Error unsharing prompt: %(message)s", { message: error.message }), "error");
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
            showToast(_("Prompt updated successfully!"), "success");
            if(buttonElement) {
                buttonElement.textContent = _("Unshare");
                buttonElement.classList.remove('update-shared-button');
                buttonElement.classList.add('unshare-button');
                buttonElement.classList.remove('bg-yellow-100', 'text-yellow-700', 'hover:bg-yellow-200');
                buttonElement.classList.add('bg-red-100', 'text-red-700', 'hover:bg-red-200');
            }
        } else {
            showToast(result.error || _("Failed to update prompt."), "error");
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        showToast(_("Error updating prompt: %(message)s", { message: error.message }), "error");
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
                showToast(_("Cannot update: critical data missing from button."), "error");
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
