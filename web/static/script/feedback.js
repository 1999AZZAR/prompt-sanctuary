// Function to open the feedback popup
function openFeedbackPopup() {
    const popup = document.getElementById('feedback-popup');
    popup.classList.remove('hidden');
    setTimeout(() => {
        popup.classList.add('show');
    }, 10); // Short delay to trigger the transition
}

// Function to close the feedback popup
document.getElementById('close-popup').addEventListener('click', function() {
    const popup = document.getElementById('feedback-popup');
    popup.classList.remove('show');
    setTimeout(() => {
        popup.classList.add('hidden');
    }, 300); // Wait for the transition to end before hiding the popup
});

// Function to handle the form submission
document.getElementById('feedback-form').addEventListener('submit', function(event) {
    event.preventDefault();

    // Get the feedback text from the form
    const feedbackText = document.querySelector('#feedback-form textarea[name="feedback"]').value;

    // Validate the feedback text
    if (!feedbackText.trim()) {
        alert('Please enter your feedback before submitting.');
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
            alert(data.message);
            document.getElementById('feedback-form').reset(); // Reset the form
            const popup = document.getElementById('feedback-popup');
            popup.classList.remove('show');
            setTimeout(() => {
                popup.classList.add('hidden');
            }, 300);
        } else {
            alert('An error occurred. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    });
});
