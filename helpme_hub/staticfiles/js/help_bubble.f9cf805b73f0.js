/**
 * Help Bubble Chat Widget
 * Quick AI assistant accessible from anywhere on the site
 */
(function() {
    'use strict';
    
    const helpBubbleButton = document.getElementById('helpBubbleButton');
    const helpChatWidget = document.getElementById('helpChatWidget');
    const closeHelpChat = document.getElementById('closeHelpChat');
    const helpChatForm = document.getElementById('helpChatForm');
    const helpChatInput = document.getElementById('helpChatInput');
    const helpChatMessages = document.getElementById('helpChatMessages');
    
    let isOpen = false;
    let conversationHistory = [];
    
    // Toggle chat widget
    function toggleChat() {
        isOpen = !isOpen;
        if (isOpen) {
            helpChatWidget.classList.remove('hidden');
            helpChatInput.focus();
        } else {
            helpChatWidget.classList.add('hidden');
        }
    }
    
    // Add message to chat
    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${isUser ? 'justify-end' : 'justify-start'}`;
        
        const messageBubble = document.createElement('div');
        messageBubble.className = `max-w-[80%] px-4 py-2 rounded-lg ${
            isUser 
                ? 'bg-light-blue dark:bg-calm-blue text-white' 
                : 'bg-light-card-hover dark:bg-dark-card-hover text-text-primary-light dark:text-text-primary-dark'
        }`;
        
        const messageText = document.createElement('p');
        messageText.className = 'text-sm whitespace-pre-wrap';
        messageText.textContent = content;
        
        messageBubble.appendChild(messageText);
        messageDiv.appendChild(messageBubble);
        helpChatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        helpChatMessages.scrollTop = helpChatMessages.scrollHeight;
    }
    
    // Show typing indicator
    function showTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typingIndicator';
        typingDiv.className = 'flex justify-start';
        
        const typingBubble = document.createElement('div');
        typingBubble.className = 'px-4 py-2 bg-light-card-hover dark:bg-dark-card-hover rounded-lg';
        typingBubble.innerHTML = '<div class="flex gap-1"><div class="w-2 h-2 bg-text-muted-light dark:text-text-muted-dark rounded-full animate-bounce"></div><div class="w-2 h-2 bg-text-muted-light dark:text-text-muted-dark rounded-full animate-bounce" style="animation-delay: 0.2s"></div><div class="w-2 h-2 bg-text-muted-light dark:text-text-muted-dark rounded-full animate-bounce" style="animation-delay: 0.4s"></div></div>';
        
        typingDiv.appendChild(typingBubble);
        helpChatMessages.appendChild(typingDiv);
        helpChatMessages.scrollTop = helpChatMessages.scrollHeight;
    }
    
    // Remove typing indicator
    function removeTyping() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Send message to AI
    async function sendMessage(message) {
        if (!message.trim()) return;
        
        // Add user message
        addMessage(message, true);
        conversationHistory.push({ role: 'user', content: message });
        
        // Show typing indicator
        showTyping();
        
        try {
            // Send to backend
            const response = await fetch('/chats/quick-help/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    message: message,
                    history: conversationHistory.slice(-10) // Last 10 messages for context
                })
            });
            
            removeTyping();
            
            if (response.ok) {
                const data = await response.json();
                if (data.response) {
                    addMessage(data.response, false);
                    conversationHistory.push({ role: 'assistant', content: data.response });
                } else {
                    addMessage('Sorry, I encountered an error. Please try again.', false);
                }
            } else {
                removeTyping();
                addMessage('Sorry, I encountered an error. Please try again.', false);
            }
        } catch (error) {
            removeTyping();
            console.error('Error sending message:', error);
            addMessage('Sorry, I encountered an error. Please try again.', false);
        }
    }
    
    // Get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Event listeners
    if (helpBubbleButton) {
        helpBubbleButton.addEventListener('click', toggleChat);
    }
    
    if (closeHelpChat) {
        closeHelpChat.addEventListener('click', toggleChat);
    }
    
    if (helpChatForm) {
        helpChatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const message = helpChatInput.value.trim();
            if (message) {
                helpChatInput.value = '';
                sendMessage(message);
            }
        });
    }
    
    // Close on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && isOpen) {
            toggleChat();
        }
    });
    
    // Close when clicking outside (optional)
    document.addEventListener('click', (e) => {
        if (isOpen && 
            !helpChatWidget.contains(e.target) && 
            !helpBubbleButton.contains(e.target)) {
            toggleChat();
        }
    });
})();
