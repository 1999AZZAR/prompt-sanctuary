// Function to show the custom popup
function showPopup(title, message, isConfirmation = false, onConfirm = null, onCancel = null) {
    const popup = document.createElement('div');
    popup.id = 'custom-popup';
    popup.className = 'fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50';

    const popupContent = document.createElement('div');
    popupContent.className = 'bg-gray-800 p-8 rounded-xl shadow-2xl w-11/12 md:w-1/2 lg:w-1/3';

    const popupTitle = document.createElement('h2');
    popupTitle.id = 'popup-title';
    popupTitle.className = 'text-2xl font-bold mb-4';
    popupTitle.textContent = title;

    const popupMessage = document.createElement('p');
    popupMessage.id = 'popup-message';
    popupMessage.className = 'text-lg text-gray-300 mb-6';
    popupMessage.textContent = message;

    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'flex justify-end space-x-4';

    if (isConfirmation) {
        // Yes Button (for confirmation popups)
        const yesButton = document.createElement('button');
        yesButton.className = 'bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200';
        yesButton.textContent = 'Yes';
        yesButton.onclick = () => {
            if (onConfirm) onConfirm();
            closePopup('custom-popup');
        };

        // No Button (for confirmation popups)
        const noButton = document.createElement('button');
        noButton.className = 'bg-gray-500 text-white px-6 py-3 rounded-lg hover:bg-gray-600 transition duration-200';
        noButton.textContent = 'No';
        noButton.onclick = () => {
            if (onCancel) onCancel();
            closePopup('custom-popup');
        };

        buttonContainer.appendChild(yesButton);
        buttonContainer.appendChild(noButton);
    } else {
        // OK Button (for non-confirmation popups)
        const okButton = document.createElement('button');
        okButton.className = 'bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition duration-200';
        okButton.textContent = 'OK';
        okButton.onclick = () => closePopup('custom-popup');

        buttonContainer.appendChild(okButton);
    }

    popupContent.appendChild(popupTitle);
    popupContent.appendChild(popupMessage);
    popupContent.appendChild(buttonContainer);

    popup.appendChild(popupContent);
    document.body.appendChild(popup);
}

// Function to close the custom popup
function closePopup(popupId = 'custom-popup') {
    const popup = document.getElementById(popupId);
    if (popup) {
        popup.remove();
    } else {
        console.error('Popup element not found in the DOM');
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
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                showPopup("Success", data.message);
                document.getElementById('feedback-form').reset(); // Reset the form
                const popup = document.getElementById('feedback-popup');
                popup.classList.remove('show');
                setTimeout(() => {
                    popup.classList.add('hidden');
                }, 300);
            } else {
                showPopup("Error", "An error occurred. Please try again.");
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showPopup("Error", "An error occurred. Please try again.");
        });
});
