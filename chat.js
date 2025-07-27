document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.querySelector('.chat-form');
    const chatInput = document.querySelector('.chat-input input');
    const chatMessages = document.querySelector('.chat-messages');
    const typingIndicator = document.querySelector('.typing-indicator');
    let retryCount = 0;
    const maxRetries = 3;
    const retryDelay = 5000; // 5 seconds
    let lastUserMessage = null;
    let isRetrying = false;

    // Function to add a message to the chat
    function addMessage(content, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        messageDiv.textContent = content;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to show typing indicator
    function showTypingIndicator() {
        typingIndicator.style.display = 'block';
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to hide typing indicator
    function hideTypingIndicator() {
        typingIndicator.style.display = 'none';
    }

    // Function to remove the last bot message
    function removeLastBotMessage() {
        const lastBotMessage = chatMessages.querySelector('.bot-message:last-child');
        if (lastBotMessage) {
            lastBotMessage.remove();
        }
    }

    // Function to handle API errors
    function handleError(error) {
        console.error('Error:', error);
        hideTypingIndicator();
        
        removeLastBotMessage(); // Remove any previous error message
        
        if (error.toLowerCase().includes('api key') || error.toLowerCase().includes('authentication')) {
            addMessage("I'm having trouble with authentication. Please check if your API key is set correctly. 🔑", false);
        } else if (error.toLowerCase().includes('rate limit') && retryCount < maxRetries && !isRetrying) {
            isRetrying = true;
            retryCount++;
            const retryMessage = `I'm receiving many requests. Waiting a moment before trying again... (Attempt ${retryCount}/${maxRetries}) 🌸`;
            addMessage(retryMessage, false);
            
            setTimeout(() => {
                showTypingIndicator();
                sendMessage(lastUserMessage);
            }, retryDelay);
        } else if (error.toLowerCase().includes('network') || error.toLowerCase().includes('connection')) {
            addMessage("I'm having trouble connecting to the server. Please check your internet connection. 🌐", false);
            retryCount = 0;
            isRetrying = false;
        } else {
            addMessage("I encountered an unexpected error. Please try again in a moment. 🙏", false);
            retryCount = 0;
            isRetrying = false;
        }
    }

    // Function to send message to server
    async function sendMessage(message) {
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            
            // Hide typing indicator
            hideTypingIndicator();

            // Remove any previous error or retry messages
            removeLastBotMessage();
            
            // Add bot response to chat
            addMessage(data.response, false);
            retryCount = 0;
            isRetrying = false;

            // Save the chat to history
            try {
                await fetch('/save_chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        response: data.response
                    })
                });
            } catch (error) {
                console.error('Error saving chat history:', error);
            }

        } catch (error) {
            handleError(error.message);
        }
    }

    // Handle form submission
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const message = chatInput.value.trim();
        if (!message) return;

        // Store the message for potential retries
        lastUserMessage = message;

        // Add user message to chat
        addMessage(message, true);
        chatInput.value = '';

        // Show typing indicator
        showTypingIndicator();

        // Send message to server
        await sendMessage(message);
    });
}); 