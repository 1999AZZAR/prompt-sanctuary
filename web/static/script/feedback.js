// Function to show the custom popup
function showPopup(title, contentHtml, buttons = [], addCloseX = true) {
    if (typeof blurBackground === 'function') blurBackground(true);

    // Remove existing popup if any
    closePopup();

    const popup = document.createElement('div');
    popup.id = 'custom-popup-modal'; // New ID to avoid conflicts
    popup.className = 'fixed inset-0 flex items-center justify-center z-[5000] p-4'; // High z-index
    popup.style.backgroundColor = 'rgba(0, 0, 0, 0.6)'; // Dimmed background

    const popupContent = document.createElement('div');
    popupContent.className = 'bg-gray-800 p-6 rounded-lg shadow-xl w-full max-w-md text-white relative glass-effect'; // Apply glass if desired
    popupContent.style.maxHeight = '90vh';
    popupContent.style.overflowY = 'auto';

    if (addCloseX) {
        const closeXButton = document.createElement('button');
        closeXButton.innerHTML = '&times;';
        closeXButton.className = 'absolute top-3 right-3 text-gray-400 hover:text-white text-2xl leading-none';
        closeXButton.onclick = closePopup;
        popupContent.appendChild(closeXButton);
    }

    const popupTitle = document.createElement('h2');
    popupTitle.className = 'text-xl font-semibold mb-4';
    popupTitle.textContent = title;
    popupContent.appendChild(popupTitle);

    const messageDiv = document.createElement('div');
    messageDiv.className = 'mb-6 popup-message-content'; // Class for styling content area
    messageDiv.innerHTML = contentHtml; // Directly set HTML content
    popupContent.appendChild(messageDiv);

    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'flex justify-end space-x-3';

    if (!buttons || buttons.length === 0) {
        // Add a default close button if no buttons are specified
        buttons = [{
            text: 'Close',
            class: 'bg-gray-500 hover:bg-gray-600',
            action: closePopup
        }];
    }

    buttons.forEach(btnConfig => {
        const button = document.createElement('button');
        button.textContent = btnConfig.text;
        button.className = `px-4 py-2 rounded-md text-white transition duration-150 ${btnConfig.class || 'bg-blue-500 hover:bg-blue-600'}`;
        button.onclick = function(event) {
            if (btnConfig.action) {
                btnConfig.action(event); // Pass event to action
            }
            // By default, popups might not close on action, depends on the action's responsibility
            // if (btnConfig.closesPopup !== false) closePopup(); // Optional: close unless specified not to
        };
        buttonContainer.appendChild(button);
    });

    popupContent.appendChild(buttonContainer);
    popup.appendChild(popupContent);
    document.body.appendChild(popup);

    // Focus on the first button or input if available
    const firstFocusable = popupContent.querySelector('button, input, textarea, select');
    if (firstFocusable) {
        firstFocusable.focus();
    }
     // Trap focus within the modal
    popup.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closePopup();
        }
    });
}

// Function to close the custom popup
function closePopup() {
    const popup = document.getElementById('custom-popup-modal');
    if (popup) {
        popup.remove();
        if (typeof blurBackground === 'function') blurBackground(false);
    }
}

// Function to open the feedback popup
function openFeedbackPopup() {
    const popup = document.getElementById('feedback-popup');
    popup.classList.remove('hidden');
    setTimeout(() => {
        popup.classList.add('show');
    }, 10); // Short delay to trigger the transition
}

// Function to close the feedback popup
document.getElementById('close-popup').addEventListener('click', function () {
    const popup = document.getElementById('feedback-popup');
    popup.classList.remove('show');
    setTimeout(() => {
        popup.classList.add('hidden');
    }, 300); // Wait for the transition to end before hiding the popup
});

// Function to handle the form submission
document.getElementById('feedback-form').addEventListener('submit', function (event) {
    event.preventDefault();

    // Get the feedback text from the form
    const feedbackText = document.querySelector('#feedback-form textarea[name="feedback"]').value;

    // Validate the feedback text
    if (!feedbackText.trim()) {
        showPopup("Error", "Please enter your feedback before submitting.");
        return;
    }

    // Create form data
    const formData = new FormData();
    formData.append('feedback', feedbackText);

    // Send the feedback to the server
    fetch('/submit_feedback', {
        method: 'POST',
        body: formData, // Send as form data
    })
        .then(response => {
            if (!response.ok) {
            // Try to parse error JSON, else throw generic error
            return response.json().then(errData => {
                throw { serverError: true, data: errData }; 
            }).catch(() => { // Catch if response.json() fails (not valid JSON)
                throw { networkError: true, status: response.status }; 
            });
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
            showToast(data.message, 'success');
                document.getElementById('feedback-form').reset(); // Reset the form
                const popup = document.getElementById('feedback-popup');
            if (popup) {
                popup.classList.remove('show');
                setTimeout(() => {
                    popup.classList.add('hidden');
                }, 300);
            }
            } else {
            // This case might not be hit if server returns non-2xx for errors
            showToast(data.message || "An error occurred. Please try again.", 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        if (error.serverError && error.data && error.data.message) {
            showToast(error.data.message, 'error');
        } else if (error.networkError) {
            showToast(`Network error (status ${error.status}). Please try again.`, 'error');
        } else {
            showToast("An unexpected error occurred. Please try again.", 'error');
        }
        });
});

// Ensure blurBackground is available (it might be defined elsewhere like generator.js)
// If not, define it here or ensure it's loaded globally before this script.
// For this example, let's assume blurBackground is globally available.
function blurBackground(blur) {
    // Blur main, header, footer, sidebar
    // Ensure these selectors are general enough or adjust as needed.
    const main = document.querySelector('main');
    const footer = document.querySelector('footer');
    const header = document.querySelector('header'); // Assuming you might have a header
    const sidebar = document.getElementById('sidePanel');

    const elementsToBlur = [main, footer, header, sidebar].filter(el => el);

    elementsToBlur.forEach(el => {
        if (blur) {
            el.classList.add('blurred'); // Define .blurred in your CSS (e.g., filter: blur(4px); pointer-events: none;)
        } else {
            el.classList.remove('blurred');
        }
    });
}
