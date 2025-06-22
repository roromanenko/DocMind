document.addEventListener('DOMContentLoaded', async () => {
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const attachBtn = document.getElementById('attach-btn');
    const chatBox = document.getElementById('chat-box');
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.style.display = 'none';
    document.body.appendChild(fileInput); // Add to DOM to be clickable

    // Get or create chat session
    let chatId = localStorage.getItem('currentChatId');
    if (!chatId) {
        console.log('No existing chat session found, creating new one...');
        try {
            const response = await fetch('/api/v1/chats', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    name: `Chat ${new Date().toLocaleString()}`,
                    description: 'Auto-created chat session'
                }),
            });
            const result = await response.json();
            if (response.ok) {
                chatId = result.id;
                localStorage.setItem('currentChatId', chatId);
                console.log('Created new chat session:', chatId);
                appendMessage(`Chat session created: ${result.name}`, 'system');
            } else {
                console.error('Failed to create chat session:', result);
                appendMessage(`Error: Failed to create chat session - ${result.detail || response.statusText}`, 'error');
                return;
            }
        } catch (error) {
            console.error('Error creating chat session:', error);
            appendMessage('Error: Failed to create chat session', 'error');
            return;
        }
    } else {
        console.log('Using existing chat session:', chatId);
        appendMessage(`Using chat session: ${chatId}`, 'system');
    }

    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = `${userInput.scrollHeight}px`;
    });

    // Handle file attachment
    attachBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (!file) {
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        appendMessage(`Uploading file "${file.name}"...`, 'system');

        try {
            const response = await fetch(`/api/v1/documents/${chatId}/upload`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();
            if (response.ok) {
                updateLastMessage(`File "${file.name}" uploaded successfully. Document ID: ${result.document_id}`, 'system');
                console.log('Upload result:', result);
            } else {
                 updateLastMessage(`Error uploading file: ${result.detail || response.statusText}`, 'error');
            }
        } catch (error) {
            updateLastMessage(`Error uploading file: ${error.message}`, 'error');
            console.error('Upload error:', error);
        }
    });

    // Handle sending message
    const sendMessage = async () => {
        const message = userInput.value.trim();
        if (!message) {
            return;
        }

        appendMessage(message, 'user');
        userInput.value = '';
        userInput.style.height = 'auto'; // Reset height

        appendMessage('...', 'bot'); // Placeholder for bot response

        try {
            const response = await fetch(`/api/v1/rag/${chatId}/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: message }),
            });
            
            const result = await response.json();
            if (response.ok) {
                updateLastMessage(result.answer, 'bot');
            } else {
                updateLastMessage(`Error: ${result.detail || response.statusText}`, 'error');
            }
        } catch (error) {
            updateLastMessage(`Error: ${error.message}`, 'error');
        }
    };

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    function appendMessage(text, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        // Simple markdown for bold and code
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/`(.*?)`/g, '<code>$1</code>');
        messageElement.innerHTML = text;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function updateLastMessage(text, sender) {
        const lastMessage = chatBox.lastChild;
        if (lastMessage) {
            lastMessage.classList.remove('bot-message', 'system-message', 'error-message');
            lastMessage.classList.add(`${sender}-message`);
             // Simple markdown for bold and code
            text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            text = text.replace(/`(.*?)`/g, '<code>$1</code>');
            lastMessage.innerHTML = text;
        }
    }

    // Chat management functions
    async function loadChatList() {
        const chatList = document.getElementById('chat-list');
        chatList.innerHTML = '<div class="chat-list-loading"><svg><use href="/assets/sprite.svg#loader"></use></svg> Loading chats...</div>';

        try {
            const response = await fetch('/api/v1/chats');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const chats = await response.json();
            renderChatList(chats);
        } catch (error) {
            console.error('Error loading chats:', error);
            chatList.innerHTML = '<div class="chat-list-empty"><p>Failed to load chats</p></div>';
        }
    }

    function renderChatList(chats) {
        const chatList = document.getElementById('chat-list');
        
        if (!chats || chats.length === 0) {
            chatList.innerHTML = `
                <div class="chat-list-empty">
                    <svg><use href="/assets/sprite.svg#message-circle"></use></svg>
                    <h3>No chats yet</h3>
                    <p>Create your first chat to get started</p>
                </div>
            `;
            return;
        }

        chatList.innerHTML = chats.map(chat => {
            const isActive = chat.id === chatId;
            const date = new Date(chat.created_at).toLocaleDateString();
            
            return `
                <div class="chat-item ${isActive ? 'active' : ''}" data-chat-id="${chat.id}">
                    <div class="chat-item-content">
                        <div class="chat-item-name">${chat.name}</div>
                        <div class="chat-item-info">
                            <div class="chat-item-docs">
                                <svg width="12" height="12"><use href="/assets/sprite.svg#file"></use></svg>
                                ${chat.document_count} docs
                            </div>
                            <div class="chat-item-date">${date}</div>
                        </div>
                    </div>
                    <div class="chat-item-actions">
                        <button class="chat-action-btn delete-btn" onclick="deleteChat('${chat.id}')" title="Delete chat">
                            <svg><use href="/assets/sprite.svg#trash"></use></svg>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // Add click handlers for chat items
        chatList.querySelectorAll('.chat-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.chat-action-btn')) return; // Don't switch chat when clicking action buttons
                
                const newChatId = item.dataset.chatId;
                if (newChatId !== chatId) {
                    switchToChat(newChatId);
                }
            });
        });
    }

    async function switchToChat(newChatId) {
        chatId = newChatId;
        localStorage.setItem('currentChatId', chatId);
        
        // Clear current chat
        chatBox.innerHTML = '';
        
        // Update UI
        loadChatList(); // Refresh to show active state
        appendMessage(`Switched to chat: ${chatId}`, 'system');
        
        console.log('Switched to chat:', chatId);
    }

    async function createNewChat() {
        try {
            const response = await fetch('/api/v1/chats', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    name: `Chat ${new Date().toLocaleString()}`,
                    description: 'Auto-created chat session'
                }),
            });
            
            const result = await response.json();
            if (response.ok) {
                switchToChat(result.id);
                appendMessage(`New chat created: ${result.name}`, 'system');
            } else {
                appendMessage(`Error creating chat: ${result.detail || response.statusText}`, 'error');
            }
        } catch (error) {
            console.error('Error creating chat:', error);
            appendMessage('Error: Failed to create new chat', 'error');
        }
    }

    // Global function for delete button onclick
    window.deleteChat = async function(chatIdToDelete) {
        if (!confirm('Are you sure you want to delete this chat? This will also delete all associated documents and cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/v1/chats/${chatIdToDelete}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                // If we deleted the current chat, create a new one
                if (chatIdToDelete === chatId) {
                    localStorage.removeItem('currentChatId');
                    location.reload(); // Reload to create new chat
                } else {
                    loadChatList(); // Just refresh the list
                }
                appendMessage('Chat deleted successfully', 'system');
            } else {
                const result = await response.json();
                appendMessage(`Error deleting chat: ${result.detail || response.statusText}`, 'error');
            }
        } catch (error) {
            console.error('Error deleting chat:', error);
            appendMessage('Error: Failed to delete chat', 'error');
        }
    };

    // Add event listeners for chat management
    document.getElementById('new-chat-btn').addEventListener('click', createNewChat);
    
    // Load chat list on page load
    loadChatList();
}); 