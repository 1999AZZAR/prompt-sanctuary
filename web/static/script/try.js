document.addEventListener('DOMContentLoaded', function() {
    const loadingIndicator = document.getElementById('loading-indicator');

    document.getElementById('send-btn').addEventListener('click', function() {
        const input = document.getElementById('message-input');
        if (input.value.trim() !== '') {
            showLoadingIndicator();
            const userMessage = input.value;
            sendUserInput(userMessage);
            postMessage(userMessage, 'user');
            input.value = '';
        }
    });

    function sendUserInput(userInput) {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/user_input', true);
        xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                hideLoadingIndicator();
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    if (response.image_path && response.image_path.endsWith('.png')) {
                        // Handle image response
                        const chatHistory = document.getElementById('chat-history');
                        const imageElement = document.createElement('img');
                        // Construct the full image URL using url_for
                        imageElement.src = "../static/image/" + response.image_path;
                        imageElement.classList.add('img-class');
                        chatHistory.appendChild(imageElement);
                        chatHistory.scrollTop = chatHistory.scrollHeight;
                    } else {
                        postMessage(response.bot_response, 'bot');
                    }
                } else {
                    postMessage('Error fetching response', 'bot');
                }
            }
        };
        xhr.send(JSON.stringify({ user_input: userInput }));
    }

    function showLoadingIndicator() {
        loadingIndicator.style.display = 'block';
        // Move the loading indicator to the bottom of chat-history
        const chatHistory = document.getElementById('chat-history');
        chatHistory.appendChild(loadingIndicator);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function hideLoadingIndicator() {
        loadingIndicator.style.display = 'none';
    }

    function postMessage(message, sender) {
        const chatHistory = document.getElementById('chat-history');
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');

        if (sender === 'user') {
            messageElement.classList.add('user-message');
        } else {
            messageElement.classList.add('bot-message');
        }

        messageElement.textContent = message;
        chatHistory.appendChild(messageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
});
