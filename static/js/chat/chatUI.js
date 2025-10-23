/**
 * chatUI.js - Message rendering and UI animations
 */

const ChatUI = {
    messageArea: null,
    inputBox: null,
    sendButton: null,
    micButton: null,

    /**
     * Initialize UI elements
     */
    init() {
        console.log('[ChatUI] Initializing UI elements');
        this.messageArea = document.getElementById('messageArea');
        this.inputBox = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.micButton = document.getElementById('micButton');

        if (!this.messageArea || !this.inputBox) {
            console.error('[ChatUI] Required UI elements not found');
            return;
        }

        this.setupEventListeners();
        
        // Note: Chat history will be restored by main.js after all modules load
        
        console.log('[ChatUI] UI initialized successfully');
    },

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Enter key to send
        if (this.inputBox) {
            this.inputBox.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    console.log('[ChatUI] Enter key pressed');
                    if (window.ChatCore) {
                        window.ChatCore.sendMessage();
                    }
                }
            });
        }

        // Send button click
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => {
                console.log('[ChatUI] Send button clicked');
                if (window.ChatCore) {
                    window.ChatCore.sendMessage();
                }
            });
        }

        // Mic button click
        if (this.micButton) {
            this.micButton.addEventListener('click', () => {
                console.log('[ChatUI] Mic button clicked');
                if (window.ChatAudio) {
                    window.ChatAudio.toggleRecording();
                }
            });
        }
    },

    /**
     * Add user message to UI
     * @param {string} message - User message text
     */
    addUserMessage(message) {
        console.log(`[ChatUI] Adding user message: ${message.substring(0, 50)}...`);
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.dataset.type = 'user';
        messageDiv.dataset.content = message;
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = message;
        
        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        messageDiv.appendChild(content);
        messageDiv.appendChild(time);
        this.messageArea.appendChild(messageDiv);
        
        this.scrollToBottom();
        this.saveChatHistory();
    },

    /**
     * Add bot message to UI
     * @param {string} message - Bot message text
     */
    addBotMessage(message) {
        console.log(`[ChatUI] Adding bot message: ${message.substring(0, 50)}...`);
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        messageDiv.dataset.type = 'bot';
        messageDiv.dataset.content = message;
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = message;
        
        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        messageDiv.appendChild(content);
        messageDiv.appendChild(time);
        this.messageArea.appendChild(messageDiv);
        
        // Animate message
        setTimeout(() => {
            messageDiv.classList.add('fade-in');
        }, 10);
        
        this.scrollToBottom();
        this.saveChatHistory();
    },

    /**
     * Add system message (error, info, etc.)
     * @param {string} message - System message text
     * @param {string} type - Message type ('error', 'info', 'success')
     */
    addSystemMessage(message, type = 'info') {
        console.log(`[ChatUI] Adding system message (${type}): ${message}`);
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message system-message ${type}`;
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = message;
        
        messageDiv.appendChild(content);
        this.messageArea.appendChild(messageDiv);
        
        this.scrollToBottom();
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageDiv.classList.add('fade-out');
            setTimeout(() => messageDiv.remove(), 500);
        }, 5000);
    },

    /**
     * Show typing indicator
     */
    showTypingIndicator() {
        console.log('[ChatUI] Showing typing indicator');
        
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.id = 'typingIndicator';
        indicator.innerHTML = `
            <span></span>
            <span></span>
            <span></span>
        `;
        
        this.messageArea.appendChild(indicator);
        this.scrollToBottom();
    },

    /**
     * Hide typing indicator
     */
    hideTypingIndicator() {
        console.log('[ChatUI] Hiding typing indicator');
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    },

    /**
     * Clear input box
     */
    clearInput() {
        if (this.inputBox) {
            this.inputBox.value = '';
            console.log('[ChatUI] Input cleared');
        }
    },

    /**
     * Set input value
     * @param {string} value - Text to set
     */
    setInput(value) {
        if (this.inputBox) {
            this.inputBox.value = value;
            console.log(`[ChatUI] Input set to: ${value.substring(0, 50)}...`);
        }
    },

    /**
     * Get input value
     * @returns {string} Current input text
     */
    getInput() {
        return this.inputBox ? this.inputBox.value.trim() : '';
    },

    /**
     * Disable input while processing
     */
    disableInput() {
        console.log('[ChatUI] Disabling input');
        if (this.inputBox) this.inputBox.disabled = true;
        if (this.sendButton) this.sendButton.disabled = true;
        if (this.micButton) this.micButton.disabled = true;
    },

    /**
     * Enable input after processing
     */
    enableInput() {
        console.log('[ChatUI] Enabling input');
        if (this.inputBox) {
            this.inputBox.disabled = false;
            this.inputBox.focus();
        }
        if (this.sendButton) this.sendButton.disabled = false;
        if (this.micButton) this.micButton.disabled = false;
    },

    /**
     * Update mic button state
     * @param {boolean} isRecording - Whether recording is active
     */
    updateMicButton(isRecording) {
        console.log(`[ChatUI] Updating mic button - Recording: ${isRecording}`);
        if (this.micButton) {
            if (isRecording) {
                this.micButton.classList.add('recording');
                this.micButton.innerHTML = '🔴'; // Recording indicator
            } else {
                this.micButton.classList.remove('recording');
                this.micButton.innerHTML = '🎤'; // Mic icon
            }
        }
    },

    /**
     * Scroll message area to bottom
     */
    scrollToBottom() {
        if (this.messageArea) {
            this.messageArea.scrollTop = this.messageArea.scrollHeight;
        }
    },

    /**
     * Clear all messages
     */
    clearMessages() {
        console.log('[ChatUI] Clearing all messages');
        if (this.messageArea) {
            this.messageArea.innerHTML = '';
        }
        this.saveChatHistory();
    },
    
    /**
     * Save chat history to localStorage
     */
    saveChatHistory() {
        try {
            const messages = [];
            const messageElements = this.messageArea.querySelectorAll('.message');
            
            messageElements.forEach(msg => {
                if (msg.dataset.type && msg.dataset.content) {
                    messages.push({
                        type: msg.dataset.type,
                        content: msg.dataset.content
                    });
                }
            });
            
            localStorage.setItem('chatHistory', JSON.stringify(messages));
            console.log(`[ChatUI] Saved ${messages.length} messages to localStorage`);
        } catch (error) {
            console.error('[ChatUI] Error saving chat history:', error);
        }
    },
    
    /**
     * Restore chat history from localStorage
     */
    restoreChatHistory() {
        try {
            const saved = localStorage.getItem('chatHistory');
            if (!saved) {
                console.log('[ChatUI] No chat history found');
                return;
            }
            
            const messages = JSON.parse(saved);
            console.log(`[ChatUI] Restoring ${messages.length} messages from localStorage`);
            
            messages.forEach(msg => {
                if (msg.type === 'user') {
                    this.addUserMessage(msg.content);
                } else if (msg.type === 'bot') {
                    this.addBotMessage(msg.content);
                }
            });
            
            console.log('[ChatUI] Chat history restored successfully');
        } catch (error) {
            console.error('[ChatUI] Error restoring chat history:', error);
        }
    },

    /**
     * Add AI-generated summary for SQL results
     * Phase 2 Enhancement: Display insights before data table
     * @param {string} summary - AI-generated summary text
     */
    addDataSummary(summary) {
        if (!summary) return;
        
        console.log(`[ChatUI] Adding data summary`);
        
        const summaryContainer = document.createElement('div');
        summaryContainer.className = 'data-summary-container';
        summaryContainer.innerHTML = `
            <div class="data-summary">
                <div class="summary-icon">💡</div>
                <div class="summary-content">
                    <div class="summary-label">AI Insights</div>
                    <div class="summary-text">${this.escapeHtml(summary)}</div>
                </div>
            </div>
        `;
        
        this.messageArea.appendChild(summaryContainer);
        this.scrollToBottom();
        
        console.log('[ChatUI] Data summary added');
    },

    /**
     * Add data table to chat
     * Phase 2: Display SQL query results as table
     * @param {Array} data - Array of objects (query results)
     * @param {string} sql - SQL query (optional)
     */
    addDataTable(data, sql = '') {
        console.log(`[ChatUI] Adding data table with ${data.length} rows`);
        
        if (!data || data.length === 0) {
            console.log('[ChatUI] No data to display');
            return;
        }
        
        const tableContainer = document.createElement('div');
        tableContainer.className = 'data-table-container';
        
        // Add SQL query info if provided
        if (sql) {
            const sqlInfo = document.createElement('div');
            sqlInfo.className = 'sql-info';
            sqlInfo.innerHTML = `<strong>SQL:</strong> <code>${this.escapeHtml(sql)}</code>`;
            tableContainer.appendChild(sqlInfo);
        }
        
        // Create table
        const table = document.createElement('table');
        table.className = 'data-table';
        
        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        const columns = Object.keys(data[0]);
        
        columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create body
        const tbody = document.createElement('tbody');
        data.forEach(row => {
            const tr = document.createElement('tr');
            columns.forEach(col => {
                const td = document.createElement('td');
                td.textContent = row[col] !== null ? row[col] : 'NULL';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        
        tableContainer.appendChild(table);
        this.messageArea.appendChild(tableContainer);
        this.scrollToBottom();
        
        console.log('[ChatUI] Data table added successfully');
    },

    /**
     * Add Plotly chart to chat
     * Phase 2: Embed interactive Plotly chart
     * @param {string} chartHtml - Plotly chart HTML
     */
    addChart(chartHtml) {
        console.log(`[ChatUI] Adding Plotly chart (${chartHtml.length} chars)`);
        
        if (!chartHtml) {
            console.log('[ChatUI] No chart HTML provided');
            return;
        }
        
        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container';
        
        // Insert HTML (this includes the div and script)
        chartContainer.innerHTML = chartHtml;
        
        this.messageArea.appendChild(chartContainer);
        
        // Execute the script tag manually (innerHTML doesn't auto-execute scripts)
        const scripts = chartContainer.getElementsByTagName('script');
        console.log(`[ChatUI] Found ${scripts.length} script tags in chart HTML`);
        
        for (let i = 0; i < scripts.length; i++) {
            const oldScript = scripts[i];
            const newScript = document.createElement('script');
            newScript.type = 'text/javascript';
            
            if (oldScript.src) {
                newScript.src = oldScript.src;
            } else {
                newScript.textContent = oldScript.textContent;
            }
            
            // Replace old script with new one to trigger execution
            oldScript.parentNode.replaceChild(newScript, oldScript);
            console.log(`[ChatUI] Executed script ${i + 1}/${scripts.length}`);
        }
        
        this.scrollToBottom();
        
        console.log('[ChatUI] Plotly chart added and scripts executed successfully');
    },

    /**
     * Add email draft with send button
     * Phase 3: Display email draft in chat with AI modification
     * @param {Object} draft - Email draft object {to_email, subject, body}
     */
    addEmailDraft(draft) {
        console.log('[ChatUI] Adding email draft');
        
        // Store draft and get ID
        const draftId = window.ChatEmail ? window.ChatEmail.setDraft(draft) : 0;
        
        const draftContainer = document.createElement('div');
        draftContainer.className = 'email-draft-container';
        draftContainer.dataset.draftId = draftId;
        
        draftContainer.innerHTML = `
            <div class="email-draft">
                <div class="email-draft-header">📧 Email Draft</div>
                <div class="email-field">
                    <strong>To:</strong> 
                    <input type="email" class="email-to-input" value="${this.escapeHtml(draft.to_email || '')}" 
                           placeholder="Enter recipient email" />
                </div>
                <div class="email-field">
                    <strong>Subject:</strong> 
                    <input type="text" class="email-subject-input" value="${this.escapeHtml(draft.subject)}" readonly />
                </div>
                <div class="email-field">
                    <strong>Body:</strong>
                    <textarea class="email-body-input" readonly>${this.escapeHtml(draft.body)}</textarea>
                </div>
                <div class="email-actions">
                    <button class="btn-send-email">Send Email</button>
                    <button class="btn-ai-modify">AI Modify</button>
                    <button class="btn-edit-email">Manual Edit</button>
                </div>
            </div>
        `;
        
        this.messageArea.appendChild(draftContainer);
        
        // Add event listeners
        const sendBtn = draftContainer.querySelector('.btn-send-email');
        const aiModifyBtn = draftContainer.querySelector('.btn-ai-modify');
        const editBtn = draftContainer.querySelector('.btn-edit-email');
        const toInput = draftContainer.querySelector('.email-to-input');
        const subjectInput = draftContainer.querySelector('.email-subject-input');
        const bodyInput = draftContainer.querySelector('.email-body-input');
        
        // Send button
        sendBtn.addEventListener('click', async () => {
            const to = toInput.value.trim();
            if (!to) {
                this.addSystemMessage('Please enter recipient email', 'error');
                return;
            }
            
            // Check if ChatEmail module is available
            if (!window.ChatEmail) {
                console.error('[ChatUI] ChatEmail module not available');
                this.addSystemMessage('Email module not loaded. Please refresh the page.', 'error');
                return;
            }
            
            sendBtn.disabled = true;
            sendBtn.textContent = 'Sending...';
            
            try {
                const success = await window.ChatEmail.sendEmail(
                    to,
                    subjectInput.value,
                    bodyInput.value
                );
                
                if (success) {
                    sendBtn.textContent = '✓ Sent';
                    sendBtn.classList.add('sent');
                } else {
                    sendBtn.disabled = false;
                    sendBtn.textContent = 'Send Email';
                }
            } catch (error) {
                console.error('[ChatUI] Error sending email:', error);
                sendBtn.disabled = false;
                sendBtn.textContent = 'Send Email';
                this.addSystemMessage('Error sending email: ' + error.message, 'error');
            }
        });
        
        // AI Modify button
        aiModifyBtn.addEventListener('click', () => {
            // Check if ChatEmail module is available
            if (!window.ChatEmail) {
                console.error('[ChatUI] ChatEmail module not available');
                this.addSystemMessage('Email module not loaded. Please refresh the page.', 'error');
                return;
            }
            this.showModifyPrompt(draftId, draftContainer, subjectInput, bodyInput);
        });
        
        // Manual Edit button
        editBtn.addEventListener('click', () => {
            // Enable editing
            subjectInput.readOnly = false;
            bodyInput.readOnly = false;
            subjectInput.focus();
            editBtn.textContent = 'Editing...';
            editBtn.disabled = true;
            console.log('[ChatUI] Email draft manual editing enabled');
        });
        
        this.scrollToBottom();
        console.log('[ChatUI] Email draft added');
    },

    /**
     * Show AI modification prompt modal
     * Phase 3: Allow user to describe modifications for AI
     */
    showModifyPrompt(draftId, container, subjectInput, bodyInput) {
        console.log('[ChatUI] Showing modification prompt');
        
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'modify-modal';
        modal.innerHTML = `
            <div class="modify-modal-content">
                <h3>🤖 AI Email Modifier</h3>
                <p>Describe what you'd like to change in the email:</p>
                <textarea class="modify-input" placeholder="E.g., Make it more formal, add a deadline, shorten it, etc." rows="4"></textarea>
                <div class="modify-actions">
                    <button class="btn-modify-confirm">Modify with AI</button>
                    <button class="btn-modify-cancel">Cancel</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const modifyInput = modal.querySelector('.modify-input');
        const confirmBtn = modal.querySelector('.btn-modify-confirm');
        const cancelBtn = modal.querySelector('.btn-modify-cancel');
        
        // Focus input
        setTimeout(() => modifyInput.focus(), 100);
        
        // Confirm button
        confirmBtn.addEventListener('click', async () => {
            const modifications = modifyInput.value.trim();
            if (!modifications) {
                this.addSystemMessage('Please describe what you want to change', 'error');
                return;
            }
            
            // Disable button during modification
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'Modifying...';
            
            // Call AI modification
            const modifiedDraft = await window.ChatEmail.modifyDraft(draftId, modifications);
            
            if (modifiedDraft) {
                // Update UI with modified draft
                subjectInput.value = modifiedDraft.subject;
                bodyInput.value = modifiedDraft.body;
                if (modifiedDraft.to_email) {
                    const toInput = container.querySelector('.email-to-input');
                    toInput.value = modifiedDraft.to_email;
                }
                console.log('[ChatUI] Draft UI updated with modifications');
            }
            
            // Remove modal
            modal.remove();
        });
        
        // Cancel button
        cancelBtn.addEventListener('click', () => {
            modal.remove();
        });
        
        // Close on outside click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    },

    /**
     * Add report preview with generate button
     * Phase 4: Display report preview in chat
     */
    addReportPreview(preview) {
        console.log('[ChatUI] Adding report preview');
        
        const previewContainer = document.createElement('div');
        previewContainer.className = 'report-preview-container';
        
        previewContainer.innerHTML = `
            <div class="report-preview">
                <div class="report-preview-header">📄 Report Preview</div>
                <div class="report-field">
                    <strong>Title:</strong>
                    <input type="text" class="report-title-input" 
                           value="${this.escapeHtml(preview.title)}" 
                           placeholder="Enter report title" />
                </div>
                <div class="report-field">
                    <strong>Summary:</strong> ${preview.summary ? 'Included ✓' : 'Not available'}
                </div>
                <div class="report-field">
                    <strong>Chart:</strong> ${preview.has_chart ? 'Included ✓' : 'Not available'}
                </div>
                <div class="report-field">
                    <strong>Data Table:</strong> ${preview.data_count} rows
                </div>
                <div class="report-field">
                    <strong>SQL Query:</strong> Included ✓
                </div>
                <div class="report-actions">
                    <button class="btn-generate-report">Generate PDF</button>
                </div>
            </div>
        `;
        
        this.messageArea.appendChild(previewContainer);
        
        // Add event listener
        const generateBtn = previewContainer.querySelector('.btn-generate-report');
        const titleInput = previewContainer.querySelector('.report-title-input');
        
        generateBtn.addEventListener('click', async () => {
            const title = titleInput.value.trim() || 'Data Report';
            
            generateBtn.disabled = true;
            generateBtn.textContent = 'Generating...';
            
            const success = await window.ChatReport.generateReport(title);
            
            if (success) {
                generateBtn.textContent = '✓ Generated';
                generateBtn.classList.add('generated');
            } else {
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate PDF';
            }
        });
        
        this.scrollToBottom();
        console.log('[ChatUI] Report preview added');
    },

    /**
     * Escape HTML to prevent XSS (moved from chatUtils for use here)
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Export for use in other modules
window.ChatUI = ChatUI;
