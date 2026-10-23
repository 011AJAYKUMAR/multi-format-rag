const API_URL = "http://127.0.0.1:8000";

const fileInput = document.getElementById('fileInput');
const dropzone = document.getElementById('dropzone');
const fileList = document.getElementById('fileList');
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const apiStatus = document.getElementById('apiStatus');
const selectAllBtn = document.getElementById('selectAllBtn');

// Fetch and render files on startup
async function fetchFiles() {
    try {
        const response = await fetch(`${API_URL}/files`);
        const files = await response.json();
        
        fileList.innerHTML = '';
        if (files.length === 0) {
            fileList.innerHTML = `<li class="no-files">No documents uploaded yet.</li>`;
            return;
        }

        files.forEach(file => {
            appendFileItem(file.filename, file.chunks);
        });
    } catch (err) {
        console.error("Failed to load files:", err);
    }
}

async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_URL}/`);
        const data = await response.json();
        if (data.status === "running") {
            apiStatus.textContent = "System Online";
            apiStatus.classList.add("online");
            fetchFiles(); // Load files once online
        }
    } catch (err) {
        apiStatus.textContent = "System Offline";
        apiStatus.style.background = "#7f1d1d";
        apiStatus.style.color = "#f87171";
    }
}
checkBackendHealth();

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
    fileInput.value = '';
});

dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.style.borderColor = '#38bdf8'; });
dropzone.addEventListener('dragleave', () => { dropzone.style.borderColor = '#475569'; });
dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.style.borderColor = '#475569';
    handleFiles(e.dataTransfer.files);
});

async function handleFiles(files) {
    for (let file of files) {
        const formData = new FormData();
        formData.append('file', file);

        const noFilesEl = fileList.querySelector('.no-files');
        if (noFilesEl) noFilesEl.remove();

        const li = document.createElement('li');
        li.innerHTML = `<span><i class="fa-solid fa-spinner fa-spin"></i> ${file.name}</span>`;
        fileList.appendChild(li);

        try {
            const response = await fetch(`${API_URL}/upload`, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (response.ok) {
                li.remove();
                appendFileItem(file.name, result.chunks_created || 0);
            } else {
                li.innerHTML = `<span><i class="fa-solid fa-triangle-exclamation" style="color: #f87171;"></i> ${file.name}</span> <small style="color:#f87171;">Failed</small>`;
            }
        } catch (err) {
            li.innerHTML = `<span><i class="fa-solid fa-triangle-exclamation" style="color: #f87171;"></i> ${file.name}</span> <small style="color:#f87171;">Error</small>`;
        }
    }
}

function appendFileItem(filename, chunks) {
    const li = document.createElement('li');
    li.dataset.filename = filename;
    li.innerHTML = `
        <div class="file-info">
            <input type="checkbox" class="file-checkbox" checked value="${filename}">
            <span title="${filename}"><i class="fa-solid fa-file-lines" style="color: #38bdf8;"></i> ${filename}</span>
        </div>
        <button class="delete-file-btn" onclick="deleteFile('${filename}', this)" title="Delete file"><i class="fa-solid fa-trash-can"></i></button>
    `;
    fileList.appendChild(li);
}

async function deleteFile(filename, btnElement) {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;
    
    try {
        const response = await fetch(`${API_URL}/files/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();

        if (response.ok) {
            // Remove element from UI
            const li = btnElement.closest('li');
            if (li) li.remove();

            // Show 'No documents' if list is empty
            if (fileList.children.length === 0) {
                fileList.innerHTML = `<li class="no-files">No documents uploaded yet.</li>`;
            }
        } else {
            console.error("Delete failed on server:", result);
            alert(`Failed to delete file: ${result.detail || 'Server error'}`);
        }
    } catch (err) {
        console.error("Error connecting to server for deletion:", err);
        alert("Network error failed to delete file.");
    }
}

// Select All toggle button
let allSelected = true;
selectAllBtn.addEventListener('click', () => {
    allSelected = !allSelected;
    document.querySelectorAll('.file-checkbox').forEach(cb => cb.checked = allSelected);
});

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });

async function sendMessage() {
    const question = userInput.value.trim();
    if (!question) return;

    // Collect selected files for customization
    const selectedSources = Array.from(document.querySelectorAll('.file-checkbox:checked'))
                                 .map(cb => cb.value);

    appendMessage(question, 'user-message');
    userInput.value = '';

    const loadingId = appendMessage('<i class="fa-solid fa-spinner fa-spin"></i> Thinking...', 'bot-message', true);

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, selected_sources: selectedSources })
        });
        const data = await response.json();

        document.getElementById(loadingId).remove();

        if (response.ok) {
            let content = data.answer;
            if (data.sources && data.sources.length > 0) {
                content += `<div class="sources-box"><i class="fa-solid fa-bookmark"></i> Sources: ${data.sources.join(', ')}</div>`;
            }
            appendMessage(content, 'bot-message');
        } else {
            appendMessage("Sorry, I encountered an error answering your question.", 'bot-message');
        }
    } catch (err) {
        document.getElementById(loadingId).remove();
        appendMessage("Network error connecting to backend.", 'bot-message');
    }
}

function appendMessage(text, className, isLoading = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${className}`;
    if (isLoading) messageDiv.id = 'loading-msg-' + Date.now();
    messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return messageDiv.id;
}

const resetChatBtn = document.getElementById('resetChatBtn');

resetChatBtn.addEventListener('click', async () => {
    if (!confirm("Start a new chat and clear history?")) return;
    try {
        await fetch(`${API_URL}/reset-chat`, { method: 'POST' });
        chatMessages.innerHTML = `
            <div class="message bot-message">
                <div class="message-content">
                    Chat history cleared! Ask me anything about your documents.
                </div>
            </div>
        `;
    } catch (err) {
        console.error("Failed to reset chat:", err);
    }
});