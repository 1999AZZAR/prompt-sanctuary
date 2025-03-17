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

    // Function to clear the chat history
    function clearChatHistory() {
        const chatHistory = document.getElementById('chat-history');
        chatHistory.innerHTML = ''; // Clear the chat history
    }

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
        modalImg.classList.add('modal-image'); // Add a class for styling

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

                        // Create a message container for the bot
                        const messageElement = document.createElement('div');
                        messageElement.classList.add('message', 'flex', 'items-start', 'space-x-4');

                        // Create bot avatar
                        const avatar = document.createElement('div');
                        avatar.classList.add('flex', 'items-center', 'justify-center', 'w-10', 'h-10', 'rounded-full', 'bg-gray-700');
                        avatar.innerHTML = '<i class="fas fa-robot text-white"></i>'; // Bot icon
                        messageElement.appendChild(avatar);

                        // Create image element
                        const imageElement = document.createElement('img');
                        imageElement.src = "../static/image/" + response.image_path;
                        imageElement.classList.add('img-class', 'rounded-lg', 'cursor-pointer'); // Add border radius and cursor pointer
                        messageElement.appendChild(imageElement);

                        // Append the message element to the chat history
                        chatHistory.appendChild(messageElement);
                        chatHistory.scrollTop = chatHistory.scrollHeight;
                    } else {
                        if (userInput.trim().toLowerCase() === 'clear') {
                            clearChatHistory(); // Clear the chat history if user input is 'clear'
                        } else {
                            postMessage(response.bot_response, 'bot');
                        }
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
        loadingIndicator.style.display = 'flex';
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
        messageElement.classList.add('message', 'flex', 'items-start', 'space-x-4');

        // Create avatar element using Font Awesome icons
        const avatar = document.createElement('div');
        avatar.classList.add('flex', 'items-center', 'justify-center', 'w-10', 'h-10', 'rounded-full', 'bg-gray-700');
        if (sender === 'user') {
            avatar.innerHTML = '<i class="fas fa-user text-white"></i>'; // User icon
            messageElement.classList.add('user-message');
        } else {
            avatar.innerHTML = '<i class="fas fa-robot text-white"></i>'; // Bot icon
            messageElement.classList.add('bot-message');
        }

        // Create message content container
        const messageContent = document.createElement('div');
        messageContent.classList.add('flex-1', 'bg-gray-700', 'p-3', 'rounded-lg');
        messageContent.textContent = message;

        // Append avatar and message content to the message element
        messageElement.appendChild(avatar);
        messageElement.appendChild(messageContent);

        // Append the message element to the chat history
        chatHistory.appendChild(messageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
});

// Open Help Popup
function openHelpPopup() {
    const helpPopup = document.getElementById('help-popup');
    helpPopup.classList.remove('hidden');
}

// Close Help Popup
document.getElementById('close-help-popup').addEventListener('click', () => {
    const helpPopup = document.getElementById('help-popup');
    helpPopup.classList.add('hidden');
});
