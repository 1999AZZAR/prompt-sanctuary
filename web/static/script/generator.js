// Submit form with streaming response
function submitFormStream(formId, url) {
    var formElement = document.getElementById(formId);
    if (!formElement) {
        console.error(`Form with ID "${formId}" not found.`);
        return;
    }

    var formData = new FormData(formElement);

    // Use global loading functions if available, otherwise fallback to local logic
    if (typeof showLoading === 'function') {
        showLoading();
    } else {
        var loading = document.getElementById("loading");
        if (loading) loading.removeAttribute('hidden');
    }
    blurBackground(true);

    // Clear previous response and show result section
    const resultSection = document.getElementById('resultSection');
    let responseContainer = document.getElementById('generated-prompt-text');
    if (!responseContainer) {
        responseContainer = document.getElementById('response');
    }
    if (resultSection && responseContainer) {
        resultSection.removeAttribute('hidden');
        responseContainer.textContent = _('Generating response...');
    }

    fetch(url, {
        method: 'POST',
        headers: window.CSRF.getFormHeaders(),
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.body.getReader();
    })
    .then(reader => {
        const decoder = new TextDecoder();
        let buffer = '';
        let fullResponse = '';

        function readStream() {
            return reader.read().then(({ done, value }) => {
                if (done) {
                    // Final processing of the complete response
                    if (fullResponse.trim()) {
                        processCompleteResponse(fullResponse);
                    }
                    return;
                }

                // Decode the chunk
                buffer += decoder.decode(value, { stream: true });
                
                // Process complete lines
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep the incomplete line in buffer

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6); // Remove 'data: ' prefix
                        
                        if (data === '[DONE]') {
                            // Stream complete
                            if (fullResponse.trim()) {
                                processCompleteResponse(fullResponse);
                            }
                            return;
                        }
                        
                        if (data.trim()) {
                            fullResponse += data;
                            // Update display progressively
                            updateStreamingDisplay(fullResponse);
                        }
                    }
                }

                return readStream();
            });
        }

        return readStream();
    })
    .catch(error => {
        console.error('Error in streaming response:', error);
        showToast(_("An error occurred while generating the response."), 'error');
        if (responseContainer) {
            responseContainer.innerHTML = '<div class="error">' + _("Error generating response. Please try again.") + '</div>';
        }
    })
    .finally(() => {
        // Use global loading functions if available, otherwise fallback to local logic
        if (typeof hideLoading === 'function') {
            hideLoading();
        } else {
            if (loading) loading.setAttribute('hidden', '');
        }
        blurBackground(false);
        updateUserPoints();
    });
}

// Update the display progressively during streaming
function updateStreamingDisplay(text) {
    // Try both old and new element IDs for compatibility
    let responseContainer = document.getElementById('generated-prompt-text');
    if (!responseContainer) {
        responseContainer = document.getElementById('response');
    }
    if (responseContainer && text.trim()) {
        // Use raw text directly like refinement.html (no cleaning)
        responseContainer.textContent = text;
    }
}

// Process the complete response after streaming is done
function processCompleteResponse(text) {
    // Try both old and new element IDs for compatibility
    let responseContainer = document.getElementById('generated-prompt-text');
    if (!responseContainer) {
        responseContainer = document.getElementById('response');
    }
    
    if (responseContainer && text.trim()) {
        // Use raw text directly like refinement.html (no cleaning)
        responseContainer.textContent = text;

        // Show the result section
        const resultSection = document.getElementById('resultSection');
        if (resultSection) {
            resultSection.removeAttribute('hidden');
            resultSection.scrollIntoView({ behavior: 'smooth' });
        }
    }
}

// Submit form asynchronously
function submitForm(formId, url) {
    var formElement = document.getElementById(formId);
    if (!formElement) {
        console.error(`Form with ID "${formId}" not found.`);
        return;
    }

    var formData = new FormData(formElement); // Get form data

    // Use global loading functions if available, otherwise fallback to local logic
    if (typeof showLoading === 'function') {
        showLoading();
    } else {
        var loading = document.getElementById("loading");
        if (loading) loading.removeAttribute('hidden');
    }
    blurBackground(true); // Restore blur for local loader's backdrop effect

    fetch(url, {
        method: 'POST',
        headers: window.CSRF.getFormHeaders(),
        body: formData
    })
    .then(response => {
        // Check if the response is JSON (for error responses) or plain text (for successful responses)
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json().then(data => ({ response, data }));
        } else {
            return response.text().then(text => ({ response, text }));
        }
    })
    .then(({ response, data, text }) => {
        // Handle error responses (JSON format)
        if (data && !data.success) {
            if (response.status === 402) {
                showToast(_("Insufficient points! Visit your profile to see your current balance."), 'warning');
                return;
            } else {
                showToast(data.error || _("An error occurred while generating the response."), 'error');
                return;
            }
        }

        // Handle successful responses (plain text)
        const result = data ? data.response : text;

        // Use raw response directly like refinement.html (no intensive cleaning)
        console.log('Raw response from server:', result);

        // Update result section with simple text display
        const resultSection = document.getElementById('resultSection');
        let responseContainer = document.getElementById('generated-prompt-text');
        if (!responseContainer) {
            responseContainer = document.getElementById('response');
        }
        
        if (resultSection && responseContainer) {
            if (result && result.trim() !== '') {
                resultSection.removeAttribute('hidden');
                responseContainer.textContent = result.trim();
                resultSection.scrollIntoView({ behavior: 'smooth' });
            } else {
                resultSection.setAttribute('hidden', '');
                responseContainer.textContent = '';
            }
        } else {
            console.error('Result section or response paragraph not found in the DOM');
        }

        // Hide preview if no image
        const previewContainer = document.getElementById('preview-container');
        const previewImage = document.getElementById('preview-image');
        if (previewContainer && previewImage) {
            if (!previewImage.src || previewImage.src.endsWith('favicon.ico')) {
                previewContainer.setAttribute('hidden', '');
            }
        }
    })
    .catch(error => {
        console.error('Error submitting form:', error);
        showToast(_("An error occurred while submitting the form."), 'error');
    })
    .finally(() => {
        // Use global loading functions if available, otherwise fallback to local logic
        if (typeof hideLoading === 'function') {
            hideLoading();
        } else {
            if (loading) loading.setAttribute('hidden', '');
        }
        blurBackground(false); // Restore blur removal
        updateUserPoints(); // Update points display after generation
    });
}

// Function to clean and parse the server response
function cleanResponse(text) {
    if (!text) return '';

    // Remove any JSON-like formatting that might have been accidentally included
    try {
        // Check if the response looks like JSON (starts with { and ends with })
        if (text.trim().startsWith('{') && text.trim().endsWith('}')) {
            const parsed = JSON.parse(text);
            // If it's a proper JSON response, extract the actual content
            if (parsed.response) {
                text = parsed.response;
            } else if (parsed.success === true && parsed.response) {
                text = parsed.response;
            } else if (typeof parsed === 'string') {
                text = parsed;
            }
        }
    } catch (e) {
        // Not valid JSON, continue with text processing
    }

    // Clean up formatting artifacts while preserving markdown structure
    let cleaned = text
        .replace(/\\n/g, '\n')  // Convert escaped newlines to actual newlines
        .replace(/\\"/g, '"')   // Convert escaped quotes to actual quotes
        .replace(/\\\\/g, '\\') // Convert escaped backslashes to actual backslashes
        .replace(/\\t/g, '    ')  // Convert escaped tabs to 4 spaces (markdown code indent)
        .replace(/&lt;/g, '<')  // Convert HTML entities back
        .replace(/&gt;/g, '>')  // Convert HTML entities back
        .replace(/&amp;/g, '&') // Convert HTML entities back
        .trim();

    // Normalize line endings for consistent markdown parsing
    cleaned = cleaned.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

    // Fix non-standard markdown formatting
    cleaned = cleaned
        // Fix double hash with brackets: # # [Header] -> ## Header
        .replace(/^# # \[([^\]]+)\]$/gm, '## $1')
        // Convert square bracket headers to proper headers
        .replace(/^\[([^\]]+)\]\*?$/gm, '## $1')
        .replace(/^\[([^\]]+)\]$/gm, '### $1')
        // Fix standalone asterisks that should be list markers
        .replace(/^([^*]+)\*$/gm, '- $1')
        // Fix indented content with spaces (convert to proper markdown)
        .replace(/^(\s{4,})([^*:\n]+):$/gm, '    - $2:')
        .replace(/^(\s{8,})([^*:\n]+):$/gm, '        - $2:')
        .replace(/^(\s{12,})([^*:\n]+):$/gm, '            - $2:')
        // Add spacing around headers if missing
        .replace(/^(#+)([^\s])/gm, '$1 $2')
        // Add spacing around list items if missing
        .replace(/^([*-+])([^\s])/gm, '$1 $2')
        // Ensure proper spacing around numbered lists
        .replace(/^(\d+\.)([^\s])/gm, '$1 $2')
        // Fix common markdown issues
        .replace(/^\*([^*]+)\*$/gm, '**$1**');  // Convert *text* to **text**

    return cleaned;
}

// Function to parse the server response
function normalizeFences(text) {
    // Ensure triple backticks are on their own lines and add language class if hinted
    return text
        .replace(/```\s*([a-zA-Z0-9_-]+)?\n/g, (m, lang) => `\n\n
~~~${lang ? lang : ''}\n`)
        .replace(/```/g, '\n~~~\n')
        .replace(/~~~([a-zA-Z0-9_-]*)\n([\s\S]*?)\n~~~/g, (m, lang, code) => {
            const langClass = lang && lang.trim() ? ` class="language-${lang.trim()}"` : '';
            return `<pre><code${langClass}>${escapeHtml(code)}</code></pre>`;
        });
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Function to update user points display
function updateUserPoints() {
    fetch('/get_user_points', {
        method: 'GET',
        headers: window.CSRF.getFormHeaders()
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.points !== undefined) {
            const pointsElement = document.getElementById('user-points');
            if (pointsElement) {
                pointsElement.textContent = parseFloat(data.points).toFixed(1);
            }
        }
    })
    .catch(error => {
        console.error('Error updating user points:', error);
    });
}

// Image input preview
function previewImage() {
    var input = document.querySelector('input[name="image"]');
    var preview = document.getElementById('preview-image');
    var container = document.getElementById('preview-container');

    if (input && preview) {
        input.addEventListener('change', function () {
            var file = input.files[0];

            // Preview image
            if (file) {
                var reader = new FileReader();

                reader.onload = function (e) {
                    preview.src = e.target.result;
                    container.removeAttribute('hidden'); // Show image preview
                    document.body.setAttribute('data-image-selected', 'true');
                };

                reader.readAsDataURL(file);
            } else {
                container.setAttribute('hidden', ''); // Hide preview when no image
                // Set the default image source using Flask's url_for function
                preview.src = "{{ url_for('static', filename='icon/favicon.ico') }}";
                document.body.setAttribute('data-image-selected', 'false');
            }
        });
    } else {
        console.error('Image input or preview element not found in the DOM');
    }
}

// Function to show the custom popup
// [ENTIRE showPopup FUNCTION from line 103 to 141 WILL BE REMOVED]

// Function to close the custom popup
// [ENTIRE closePopup FUNCTION from line 144 to 152 WILL BE REMOVED]

// Blur/unblur main content when popup is open/closed
// function blurBackground(blur) { // Moved to feedback.js or a global utility
//     // Blur main, header, footer, sidebar
//     var main = document.querySelector('main');
//     var footer = document.querySelector('footer');
//     var sidebar = document.getElementById('sidePanel');
//     if (main) blur ? main.classList.add('blurred') : main.classList.remove('blurred');
//     if (footer) blur ? footer.classList.add('blurred') : footer.classList.remove('blurred');
//     if (sidebar) blur ? sidebar.classList.add('blurred') : sidebar.classList.remove('blurred');
// }

// Initialize the image preview function when the DOM content is loaded
document.addEventListener("DOMContentLoaded", function () {
    // Always hide preview and result on load
    var previewContainer = document.getElementById('preview-container');
    if (previewContainer) previewContainer.setAttribute('hidden', '');
    var resultSection = document.getElementById('resultSection');
    if (resultSection) resultSection.setAttribute('hidden', '');

    previewImage();

    // Handle form submission for text prompt
    var textPromptForm = document.getElementById('text-prompt-form');
    if (textPromptForm) {
        textPromptForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission behavior
            submitFormStream('text-prompt-form', '/generate/tprompt/stream'); // Submit form with streaming
        });
    } else {
        console.error('Text prompt form not found in the DOM');
    }

    // Handle form submission for random text prompt
    var randomTextPromptForm = document.getElementById('random-text-prompt-form');
    if (randomTextPromptForm) {
        randomTextPromptForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission behavior
            submitForm('random-text-prompt-form', '/generate/trandom'); // Submit form asynchronously
        });
    } else {
        console.error('Random text prompt form not found in the DOM');
    }

    // Handle form submission for advanced text prompt
    var aTextPromptForm = document.getElementById('a-text-prompt-form');
    if (aTextPromptForm) {
        aTextPromptForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission behavior
            submitForm('a-text-prompt-form', '/advance/generate'); // Submit form asynchronously
        });
    } else {
        console.error('Advanced text prompt form not found in the DOM');
    }

    // Handle form submission for advanced image prompt
    var aImagePromptForm = document.getElementById('a-image-prompt-form');
    if (aImagePromptForm) {
        aImagePromptForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission behavior
            submitForm('a-image-prompt-form', '/advance/igenerate'); // Submit form asynchronously
        });
    } else {
        console.error('Advanced image prompt form not found in the DOM');
    }

    // Handle form submission for advanced reverse image prompt
    var aReverseImageForm = document.getElementById('a-reverse-image-form');
    if (aReverseImageForm) {
        aReverseImageForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission behavior
            submitForm('a-reverse-image-form', '/advance/image'); // Submit form asynchronously
        });
    } else {
        console.error('Advanced reverse image form not found in the DOM');
    }

    // Handle form submission for image prompt
    var imagePromptForm = document.getElementById('image-prompt-form');
    if (imagePromptForm) {
        imagePromptForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission behavior
            submitForm('image-prompt-form', '/generate/iprompt'); // Submit form asynchronously
        });
    }

    // Save to library button
    const saveButton = document.getElementById("save-to-library");
    if (saveButton) {
        saveButton.addEventListener("click", function () {
            const promptText = document.getElementById("response").innerText;
            if (promptText && promptText.trim() !== "") {
                promptForTitleModal(promptText);
            } else {
                showToast(_("Nothing to save! Generate a prompt first."), "warning");
            }
        });
    }
});

// Function to toggle prompt input based on user's selection
function togglePromptInput(option) {
    var textInputForm = document.getElementById('image-prompt-form');
    var imageUploadForm = document.getElementById('image-upload-form');

    if (textInputForm && imageUploadForm) {
        if (option === 'text') {
            textInputForm.removeAttribute('hidden');
            imageUploadForm.setAttribute('hidden', '');
            document.getElementById('generate-button').textContent = 'Generate';
        } else if (option === 'image') {
            textInputForm.setAttribute('hidden', '');
            imageUploadForm.removeAttribute('hidden');
            document.getElementById('generate-button').textContent = 'Generate';
        } else if (option === 'random') {
            textInputForm.setAttribute('hidden', '');
            imageUploadForm.setAttribute('hidden', '');
            if (!document.getElementById('user_input_image').value) {
                document.getElementById('generate-button').textContent = 'Random';
            } else {
                document.getElementById('generate-button').textContent = 'Generate';
            }
        }
    } else {
        console.error('Text input form or image upload form not found in the DOM');
    }
}

// Function to handle form submission based on user's selection
function generatePrompt() {
    var option = document.querySelector('input[name="prompt-option"]:checked').value;
    if (option === "text") {
        submitForm('image-prompt-form', '/generate/iprompt');
    } else if (option === "image") {
        submitForm('image-upload-form', '/generate/image');
    } else if (option === "random") {
        submitForm('random-text-prompt-form', '/generate/irandom');
    }
}

// Copy the response to the clipboard
function copyToClipboard() {
    var responseText = document.getElementById("response");
    if (responseText) {
        var textArea = document.createElement("textarea");
        // Preserve formatting (especially newlines) by using innerText
        textArea.value = responseText.innerText; 
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showToast(_("Response copied to clipboard!"), 'success');
        } catch (err) {
            showToast(_("Failed to copy response."), 'error');
            console.error('Fallback: Oops, unable to copy', err);
        }
        document.body.removeChild(textArea);
    } else {
        console.error('Response text element not found in the DOM');
        showToast(_("Failed to copy response: content not found."), 'error');
    }
}

// Loading animation
function loadingAnimation() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.removeAttribute('hidden');
    }
}

// Prompts the user for a title using the global showAppPopup
function promptForTitleModal(promptText) {
    const contentHtml = `
        <div>
            <label for="promptTitle" class="block mb-2 text-sm font-medium text-gray-200">Enter a title for this prompt:</label>
            <input type="text" id="promptTitle" class="w-full p-2.5 bg-gray-700 border border-gray-600 text-white rounded-lg focus:ring-blue-500 focus:border-blue-500 placeholder-gray-400" placeholder="Prompt Title" required>
        </div>
        <!-- Removed Tags Input Field -->
    `;

    const buttons = [
        {
            text: "Save",
            action: () => {
                const title = document.getElementById('promptTitle').value;
                // Removed: const tags = document.getElementById('promptTags').value;
                if (!title.trim()) {
                    showToast(_("Title cannot be empty."), "error");
                    const titleInput = document.getElementById('promptTitle');
                    if (titleInput) titleInput.focus();
                    return false; // Keep popup open
                }
                // Removed 'tags' from the call to saveToLibrary
                saveToLibrary(title, promptText);
                // Popup will close automatically unless false is returned
            }
        },
        {
            text: "Cancel",
            action: () => {
                closeAppPopup(); // Explicitly close, or rely on default
            }
        }
    ];

    showAppPopup("Save Prompt to Library", contentHtml, { 
        type: 'custom', 
        buttons: buttons,
        size: 'sm' // Keep this popup relatively small
    });
}

// Saves the prompt to the user's library
// Removed 'tags' parameter from function definition
function saveToLibrary(title, promptContent) { 
    const formData = new FormData();
    formData.append('title', title);
    formData.append('prompt', promptContent);
    // Removed: formData.append('tags', tags);

    showGlobalLoader(); // Show loader before fetch

    fetch('/save_prompt', {
        method: 'POST',
        headers: window.CSRF.getFormHeaders(),
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || _("Prompt saved successfully!"), "success");
        } else {
            showToast(data.message || _("Failed to save prompt."), "error");
        }
    })
    .catch(error => {
        console.error('Error saving prompt:', error);
        showToast(_("An error occurred while saving the prompt. Check console for details."), "error");
    })
    .finally(() => {
        hideGlobalLoader(); // Hide loader after fetch
    });
}
