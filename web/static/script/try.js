// TryBot chat app
document.addEventListener('DOMContentLoaded', function () {
    const loadingIndicator = document.getElementById('loading-indicator');

    // Send message when send button clicked
    document.getElementById('send-btn').addEventListener('click', function () {
        const input = document.getElementById('message-input');
        if (input.value.trim() !== '') {
            showLoadingIndicator();
            const userMessage = input.value;
            sendUserInput(userMessage);
            postMessage(userMessage, 'user');
            input.value = '';
        }
    });

    // Add event listener to handle clicking on the image
    document.addEventListener('click', function (event) {
        if (event.target.classList.contains('img-class')) {
            showImageFullScreen(event.target);
        }
    });

    function showImageFullScreen(imageElement) {
        // Create a modal container
        const modalContainer = document.createElement('div');
        modalContainer.classList.add('modal-container');

        // Create a modal content wrapper
        const modalContent = document.createElement('div');
        modalContent.classList.add('modal-content');

        // Create an image element inside the modal content
        const modalImg = document.createElement('img');
        modalImg.src = imageElement.src;

        // Append the image to the modal content
        modalContent.appendChild(modalImg);

        // Append the modal content to the modal container
        modalContainer.appendChild(modalContent);

        // Append the modal container to the document body
        document.body.appendChild(modalContainer);

        // Close the modal when clicked outside the image
        modalContainer.addEventListener('click', function () {
            modalContainer.remove();
        });
    }

    // Send user input to server
    function sendUserInput(userInput) {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/user_input', true);
        xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                hideLoadingIndicator();
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    if (response.image_path && response.image_path.endsWith('.png')) {
                        // Handle image response
                        const chatHistory = document.getElementById('chat-history');
                        const imageElement = document.createElement('img');
                        imageElement.src = "../static/image/" + response.image_path;
                        imageElement.classList.add('img-class');
                        chatHistory.appendChild(imageElement);
                        chatHistory.scrollTop = chatHistory.scrollHeight;
                        // Post text response
                    } else {
                        postMessage(response.bot_response, 'bot');
                    }
                    // Handle error
                } else {
                    postMessage('Error fetching response', 'bot');
                }
            }
        };
        xhr.send(JSON.stringify({
            user_input: userInput
        }));
    }

    // Show loading indicator
    function showLoadingIndicator() {
        loadingIndicator.style.display = 'block';
        const chatHistory = document.getElementById('chat-history');
        chatHistory.appendChild(loadingIndicator);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // Hide loading indicator
    function hideLoadingIndicator() {
        loadingIndicator.style.display = 'none';
    }

    // Post message to chat history
    function postMessage(message, sender) {
        const chatHistory = document.getElementById('chat-history');
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');

        // Add CSS class based on sender
        if (sender === 'user') {
            messageElement.classList.add('user-message');
        } else {
            messageElement.classList.add('bot-message');
        }

        // Set message text
        messageElement.textContent = message;
        chatHistory.appendChild(messageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
});