// share.js
document.addEventListener('DOMContentLoaded', () => {
    const shareButtons = document.querySelectorAll('.share-button');

    if (shareButtons.length === 0) {
        console.warn('No share buttons found.');
    } else {
        shareButtons.forEach(button => {
            button.addEventListener('click', () => {
                const promptId = button.getAttribute('data-prompt-id');
                const title = button.getAttribute('data-title');
                const prompt = button.getAttribute('data-prompt');

                const data = {
                    prompt_id: promptId,
                    title: title,
                    prompt: prompt
                };

                console.log('Sending data:', data);

                fetch('/share_prompt', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Prompt shared successfully!');
                    } else {
                        alert('Failed to share the prompt.');
                    }
                })
                .catch(error => console.error('Error:', error));
            });
        });
    }
});
