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
    const formData = new FormData(this);

    fetch('/submit_feedback', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(data.message);
            document.getElementById('feedback-form').reset();
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
