// Function to handle sharing a prompt
function sharePrompt(promptId, title, promptContent) {
    const data = {
        prompt_id: promptId,
        title: title,
        prompt: promptContent
    };

    fetch('/share_prompt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Failed to share prompt.');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('Prompt shared successfully!');
        } else {
            alert('Failed to share prompt: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error sharing prompt: ' + error.message);
    });
}

// Add event listeners to all share buttons
document.addEventListener('DOMContentLoaded', function () {
    const shareButtons = document.querySelectorAll('.share-button');

    shareButtons.forEach(button => {
        button.addEventListener('click', function () {
            const promptId = button.getAttribute('data-prompt-id');
            const title = button.getAttribute('data-title');
            const promptContent = button.getAttribute('data-prompt');

            if (promptId && title && promptContent) {
                sharePrompt(promptId, title, promptContent);
            } else {
                alert('Error: Missing prompt data.');
            }
        });
    });
});