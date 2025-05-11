// Submit form asynchronously
function submitForm(formId, url) {
    var formElement = document.getElementById(formId);
    if (!formElement) {
        console.error(`Form with ID "${formId}" not found.`);
        return;
    }

    var formData = new FormData(formElement); // Get form data

    // showGlobalLoader(); // No longer using global loader for this specific function
    var loading = document.getElementById("loading"); 
    if (loading) loading.classList.remove('hidden');
    blurBackground(true); // Restore blur for local loader's backdrop effect

    fetch(url, {
        method: 'POST',
        body: formData
    })
    .then(response => response.text()) // Assuming text response for prompt generation
    .then(result => {
        // Log the response text
        console.log('Response from server:', result);

        // Update result section with the response
        var resultSection = document.getElementById('resultSection');
        var responseParagraph = document.getElementById('response');
        if (resultSection && responseParagraph) {
            if (result && result.trim() !== '') {
                resultSection.classList.remove('hidden'); // Show result section
                responseParagraph.innerHTML = parseResponse(result); // Parse and update the response content
            } else {
                resultSection.classList.add('hidden'); // Hide if no prompt
                responseParagraph.innerHTML = '';
            }
        } else {
            console.error('Result section or response paragraph not found in the DOM');
        }

        // Hide preview if no image
        var previewContainer = document.getElementById('preview-container');
        var previewImage = document.getElementById('preview-image');
        if (previewContainer && previewImage) {
            if (!previewImage.src || previewImage.src.endsWith('favicon.ico')) {
                previewContainer.classList.add('hidden');
            }
        }
    })
    .catch(error => {
        console.error('Error submitting form:', error);
        showToast("An error occurred while submitting the form.", 'error'); 
    })
    .finally(() => {
        // hideGlobalLoader(); // No longer using global loader here
        if (loading) loading.classList.add('hidden'); 
        blurBackground(false); // Restore blur removal
    });
}

// Function to parse the server response
function parseResponse(response) {
    // Escape HTML characters to safely render text
    let escaped = response
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    // Convert markdown-style formatting to HTML
    return escaped
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>') // Code blocks
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold text
        .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic text
        .replace(/\n/g, '<br>'); // Line breaks
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
                    container.classList.remove('hidden'); // Show image preview
                    document.body.setAttribute('data-image-selected', 'true');
                };

                reader.readAsDataURL(file);
            } else {
                container.classList.add('hidden'); // Hide preview when no image
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
    if (previewContainer) previewContainer.classList.add('hidden');
    var resultSection = document.getElementById('resultSection');
    if (resultSection) resultSection.classList.add('hidden');

    previewImage();

    // Handle form submission for text prompt
    var textPromptForm = document.getElementById('text-prompt-form');
    if (textPromptForm) {
        textPromptForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission behavior
            submitForm('text-prompt-form', '/generate/tprompt'); // Submit form asynchronously
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
                showToast("Nothing to save! Generate a prompt first.", "warning");
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
            textInputForm.style.display = 'block';
            imageUploadForm.style.display = 'none';
            document.getElementById('generate-button').textContent = 'Generate';
        } else if (option === 'image') {
            textInputForm.style.display = 'none';
            imageUploadForm.style.display = 'block';
            document.getElementById('generate-button').textContent = 'Generate';
        } else if (option === 'random') {
            textInputForm.style.display = 'none';
            imageUploadForm.style.display = 'none';
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
            showToast("Response copied to clipboard!", 'success');
        } catch (err) {
            showToast("Failed to copy response.", 'error');
            console.error('Fallback: Oops, unable to copy', err);
        }
        document.body.removeChild(textArea);
    } else {
        console.error('Response text element not found in the DOM');
        showToast("Failed to copy response: content not found.", 'error'); 
    }
}

// Loading animation
function loadingAnimation() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.classList.remove('hidden');
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
                    showToast("Title cannot be empty.", "error");
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
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || "Prompt saved successfully!", "success");
        } else {
            showToast(data.message || "Failed to save prompt.", "error");
        }
    })
    .catch(error => {
        console.error('Error saving prompt:', error);
        showToast("An error occurred while saving the prompt. Check console for details.", "error");
    })
    .finally(() => {
        hideGlobalLoader(); // Hide loader after fetch
    });
}
