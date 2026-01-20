const messagesDiv = document.getElementById('messages');
const commandInput = document.getElementById('commandInput');
const sendBtn = document.getElementById('sendBtn');
const btnText = document.getElementById('btnText');
const btnLoader = document.getElementById('btnLoader');

// Focus input on load
commandInput.focus();

// Send command on Enter key
commandInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !sendBtn.disabled) {
        sendCommand();
    }
});

function addMessage(content, type = 'assistant') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const timestamp = new Date().toLocaleTimeString();
    
    if (type === 'user') {
        messageDiv.innerHTML = `
            <div><strong>You:</strong></div>
            <pre>${escapeHtml(content)}</pre>
            <div class="timestamp">${timestamp}</div>
        `;
    } else if (type === 'error') {
        messageDiv.innerHTML = `
            <div><strong>❌ Error:</strong></div>
            <pre>${escapeHtml(content)}</pre>
            <div class="timestamp">${timestamp}</div>
        `;
    } else {
        // Check if result has formatted report
        let displayContent = content;
        try {
            const parsed = JSON.parse(content);
            
            // If there's a formatted report, show that instead of JSON
            if (parsed._formatted_report) {
                displayContent = parsed._formatted_report;
            } else {
                displayContent = JSON.stringify(parsed, null, 2);
            }
        } catch (e) {
            // Not JSON, use as is
        }
        
        messageDiv.innerHTML = `
            <div><strong>🤖 Agent:</strong></div>
            <pre>${escapeHtml(displayContent)}</pre>
            <div class="timestamp">${timestamp}</div>
        `;
    }
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function setLoading(loading) {
    sendBtn.disabled = loading;
    commandInput.disabled = loading;
    
    if (loading) {
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-block';
    } else {
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

async function sendCommand() {
    const command = commandInput.value.trim();
    
    if (!command) {
        return;
    }
    
    // Add user message
    addMessage(command, 'user');
    
    // Clear input
    commandInput.value = '';
    
    // Set loading state
    setLoading(true);
    
    try {
        const response = await fetch('/api/command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ command: command })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (data.result) {
                addMessage(JSON.stringify(data.result), 'assistant');
            } else if (data.message) {
                addMessage(data.message, 'assistant');
            }
        } else {
            addMessage(data.error || 'Unknown error occurred', 'error');
        }
        
    } catch (error) {
        addMessage(`Network error: ${error.message}`, 'error');
    } finally {
        setLoading(false);
        commandInput.focus();
    }
}

function setCommand(cmd) {
    commandInput.value = cmd;
    commandInput.focus();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add welcome message
addMessage('Welcome! Enter a command to get started.', 'assistant');
