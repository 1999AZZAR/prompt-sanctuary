// Submit form asynchronously
function submitForm(formId, url) {
    var formElement = document.getElementById(formId);
    if (!formElement) {
        console.error(`Form with ID "${formId}" not found.`);
        return;
    }

    var formData = new FormData(formElement); // Get form data

    // Display loading animation
    var loading = document.getElementById("loading");
    loading.classList.remove('hidden');
    blurBackground(true);

    fetch(url, {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
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

        // Hide loading animation
        loading.classList.add('hidden');
    blurBackground(false);
        // Hide preview if no image
        var previewContainer = document.getElementById('preview-container');
        var previewImage = document.getElementById('preview-image');
        if (previewContainer && previewImage) {
            if (!previewImage.src || previewImage.src.endsWith('favicon.ico')) {
                previewContainer.classList.add('hidden');
            }
        }
        // Result section is handled above

    })
    .catch(error => {
        console.error('Error submitting form:', error);
        // Hide loading animation in case of error
        loading.classList.add('hidden');
    blurBackground(false);
        showPopup("Error", "An error occurred while submitting the form.");
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
function showPopup(title, message) {
    blurBackground(true);
    // Create the popup container
    const popup = document.createElement('div');
    popup.id = 'custom-popup';
    popup.className = 'fixed inset-0 flex items-center justify-center glass z-50';

    // Create the popup content
    const popupContent = document.createElement('div');
    popupContent.className = 'glass p-8 rounded-lg w-11/12 max-w-md';

    // Create the popup title
    const popupTitle = document.createElement('h2');
    popupTitle.id = 'popup-title';
    popupTitle.className = 'text-2xl font-bold mb-4';
    popupTitle.textContent = title;

    // Create the popup message
    const popupMessage = document.createElement('p');
    popupMessage.id = 'popup-message';
    popupMessage.className = 'text-lg text-gray-300 mb-6';
    popupMessage.textContent = message;

    // Create the OK button
    const okButton = document.createElement('button');
    okButton.className = 'bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200';
    okButton.textContent = 'OK';
    okButton.onclick = closePopup;

    // Create the button container
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'flex justify-end';
    buttonContainer.appendChild(okButton);

    // Assemble the popup content
    popupContent.appendChild(popupTitle);
    popupContent.appendChild(popupMessage);
    popupContent.appendChild(buttonContainer);

    // Assemble the popup
    popup.appendChild(popupContent);

    // Add the popup to the body
    document.body.appendChild(popup);
}

// Function to close the custom popup
function closePopup() {
    const popup = document.getElementById('custom-popup');
    if (popup) {
        popup.remove(); // Remove the popup from the DOM
        blurBackground(false);
        blurBackground(false);
    } else {
        console.error('Popup element not found in the DOM');
    }
}

// Blur/unblur main content when popup is open/closed
function blurBackground(blur) {
    // Blur main, header, footer, sidebar
    var main = document.querySelector('main');
    var footer = document.querySelector('footer');
    var sidebar = document.getElementById('sidePanel');
    if (main) blur ? main.classList.add('blurred') : main.classList.remove('blurred');
    if (footer) blur ? footer.classList.add('blurred') : footer.classList.remove('blurred');
    if (sidebar) blur ? sidebar.classList.add('blurred') : sidebar.classList.remove('blurred');
}

// Blur/unblur main content when popup is open/closed
function blurBackground(blur) {
    // Blur main, footer, sidebar
    var main = document.querySelector('main');
    var footer = document.querySelector('footer');
    var sidebar = document.getElementById('sidePanel');
    if (main) blur ? main.classList.add('blurred') : main.classList.remove('blurred');
    if (footer) blur ? footer.classList.add('blurred') : footer.classList.remove('blurred');
    if (sidebar) blur ? sidebar.classList.add('blurred') : sidebar.classList.remove('blurred');
}

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
        textArea.value = responseText.innerText;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showPopup("Success", "Response copied to clipboard!"); // Use dynamic popup
    } else {
        console.error('Response text element not found in the DOM');
        showPopup("Error", "Failed to copy response to clipboard."); // Use dynamic popup
    }
}

// Loading animation
function loadingAnimation() {
    var loading = document.getElementById("loading");
    if (loading) {
        loading.style.display = "flex";
        return true;
    } else {
        console.error('Loading element not found in the DOM');
        return false;
    }
}

function promptForTitle() {
    // Create the popup container
    const popup = document.createElement('div');
    popup.id = 'custom-popup';
    popup.className = 'fixed inset-0 flex items-center justify-center glass z-50';

    // Create the popup content
    const popupContent = document.createElement('div');
    popupContent.className = 'glass p-8 rounded-lg w-11/12 max-w-md';

    // Create the popup title
    const popupTitle = document.createElement('h2');
    popupTitle.id = 'popup-title';
    popupTitle.className = 'text-2xl font-bold mb-4';
    popupTitle.textContent = "Save Prompt";

    // Create the popup message (input field and buttons)
    const popupMessage = document.createElement('div');
    popupMessage.innerHTML = `
        <label for="title-input" class="block mb-2">Enter a title for your prompt:</label>
        <input type="text" id="title-input" class="w-full p-3 bg-gray-700 rounded-lg" placeholder="Enter title" required>
        <div class="flex justify-end space-x-4 mt-6">
            <button id="cancel-button" class="bg-gray-500 text-white px-6 py-3 rounded-lg hover:bg-gray-600 transition duration-200">Cancel</button>
            <button id="ok-button" class="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200">OK</button>
        </div>
    `;

    // Assemble the popup content
    popupContent.appendChild(popupTitle);
    popupContent.appendChild(popupMessage);
    popup.appendChild(popupContent);

    // Add the popup to the body
    document.body.appendChild(popup);

    // Add event listener for the OK button
    const okButton = document.getElementById('ok-button');
    const cancelButton = document.getElementById('cancel-button');
    const titleInput = document.getElementById('title-input');

    if (okButton && cancelButton && titleInput) {
        // OK button click handler
        okButton.onclick = function () {
            if (titleInput.value.trim()) { // Check if title is not empty
                const promptText = document.getElementById("response").innerText;
                saveToLibrary(titleInput.value.trim(), promptText);
            } else {
                showPopup("Error", "Please enter a title."); // Use dynamic popup for error
            }
        };

        // Cancel button click handler
        cancelButton.onclick = function () {
            closePopup(); // Close the popup
        };
    } else {
        console.error('OK button, Cancel button, or title input not found in the DOM');
    }
}

function saveToLibrary(title, prompt) {
    console.log("Saving prompt with title:", title); // Debugging
    fetch('/save_prompt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'title=' + encodeURIComponent(title) + '&prompt=' + encodeURIComponent(prompt),
    })
        .then(response => {
            console.log("Server response status:", response.status); // Debugging
            if (!response.ok) {
                throw new Error("Server returned an error");
            }
            return response.text();
        })
        .then(data => {
            console.log("Server response data:", data); // Debugging
            showPopup("Success", data); // Use dynamic popup for success
            closePopup(); // Close the title input popup
        })
        .catch(error => {
            console.error("Error saving prompt:", error); // Debugging
            showPopup("Error", "Failed to save prompt."); // Use dynamic popup for error
            closePopup(); // Close the title input popup
        });
}
