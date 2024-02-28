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
            resultSection.classList.remove('hidden'); // Display the result section
            responseParagraph.innerHTML = parseResponse(result); // Parse and update the response content
        } else {
            console.error('Result section or response paragraph not found in the DOM');
        }

        // Hide loading animation
        loading.classList.add('hidden');
    })
    .catch(error => {
        console.error('Error submitting form:', error);
        // Hide loading animation in case of error
        loading.classList.add('hidden');
    });
}

// Function to parse the server response
function parseResponse(response) {
    // Parse the response into HTML
    return response
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold text
        .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic text
        .replace(/\n/g, '<br>') // Line breaks
        .replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>'); // Code blocks
}

// image input preview
function previewImage() {
    var input = document.querySelector('input[name="image"]');
    var preview = document.getElementById('preview-image');

    if (input && preview) {
        input.addEventListener('change', function () {
            var file = input.files[0];

            // preview image
            if (file) {
                var reader = new FileReader();

                reader.onload = function (e) {
                    preview.src = e.target.result;
                    document.body.setAttribute('data-image-selected', 'true');
                };

                reader.readAsDataURL(file);
            } else {
                // Set the default image source using Flask's url_for function
                preview.src = "{{ url_for('static', filename='icon/favicon.ico') }}";
                document.body.setAttribute('data-image-selected', 'false');
            }
        });
    } else {
        console.error('Image input or preview element not found in the DOM');
    }
}

// Initialize the image preview function when the DOM content is loaded
document.addEventListener("DOMContentLoaded", function () {
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

// copy the response to the clipboard
function copyToClipboard() {
    var responseText = document.getElementById("response");
    if (responseText) {
        var textArea = document.createElement("textarea");
        textArea.value = responseText.innerText;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        alert("Response copied to clipboard!");
    } else {
        console.error('Response text element not found in the DOM');
    }
}

// loading animation
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
