// Copy function for personal library
document.addEventListener('DOMContentLoaded', function () {
    // Add click event listeners to all copy buttons
    document.querySelectorAll('.copy-button').forEach(button => {
        button.addEventListener('click', function (e) {
            // Prevent default button behavior
            e.preventDefault();

            // Get the prompt content from the sibling <p> element
            const promptContent = button.previousElementSibling.textContent;

            // Use the Clipboard API to copy the content
            navigator.clipboard.writeText(promptContent)
                .then(() => {
                    alert('Prompt copied to clipboard!');
                })
                .catch((err) => {
                    console.error('Failed to copy prompt:', err);
                    alert('Failed to copy prompt. Please try again.');
                });
        });
    });
});
