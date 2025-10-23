/**
 * chatUpload.js - Document Upload Module
 * Handles document uploads in the chat interface
 * Allows users to upload PDF, DOCX, TXT files and send them via email
 */

const ChatUpload = (() => {
    // Store uploaded files
    let uploadedFiles = [];

    /**
     * Initialize upload functionality
     */
    function init() {
        console.log('[ChatUpload] Initializing document upload module');
        
        const uploadButton = document.getElementById('uploadButton');
        const fileInput = document.getElementById('fileInput');

        if (uploadButton && fileInput) {
            // Trigger file input when upload button is clicked
            uploadButton.addEventListener('click', () => {
                fileInput.click();
            });

            // Handle file selection
            fileInput.addEventListener('change', handleFileSelect);
        } else {
            console.error('[ChatUpload] Upload button or file input not found');
        }
    }

    /**
     * Handle file selection
     */
    async function handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        console.log(`[ChatUpload] File selected: ${file.name} (${file.type})`);

        // Validate file type
        const allowedTypes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'text/plain'
        ];

        const allowedExtensions = ['.pdf', '.docx', '.doc', '.txt'];
        const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

        if (!allowedExtensions.includes(fileExtension)) {
            alert('Only PDF, DOCX, and TXT files are allowed.');
            event.target.value = ''; // Reset input
            return;
        }

        // Show uploading message
        if (window.ChatUI) {
            window.ChatUI.addBotMessage('📎 Uploading document...');
        }

        try {
            // Upload file
            const result = await uploadDocument(file);
            
            if (result.status === 'success') {
                // Store uploaded file info
                uploadedFiles.push({
                    filename: result.filename,
                    filepath: result.filepath,
                    originalName: file.name
                });

                console.log(`[ChatUpload] File uploaded successfully: ${result.filename}`);
                
                // Show success message with email option
                if (window.ChatUI) {
                    const message = `✅ Document "${file.name}" uploaded successfully!\n\nWould you like to send it via email?`;
                    window.ChatUI.addBotMessage(message);
                    
                    // Add email button
                    addEmailButton(result.filename, result.filepath, file.name);
                }
            } else {
                throw new Error(result.error || 'Upload failed');
            }
        } catch (error) {
            console.error('[ChatUpload] Upload error:', error);
            if (window.ChatUI) {
                window.ChatUI.addBotMessage(`❌ Failed to upload document: ${error.message}`);
            }
        }

        // Reset file input
        event.target.value = '';
    }

    /**
     * Upload document to server
     */
    async function uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/upload_docs', {
            method: 'POST',
            body: formData
        });

        return await response.json();
    }

    /**
     * Add email button for uploaded document
     */
    function addEmailButton(filename, filepath, originalName) {
        if (!window.ChatUI) return;

        const buttonHtml = `
            <div class="action-buttons">
                <button class="email-doc-btn" data-filename="${filename}" data-filepath="${filepath}" data-original="${originalName}">
                    📧 Send via Email
                </button>
            </div>
        `;

        const messageArea = document.getElementById('messageArea');
        const lastMessage = messageArea.lastElementChild;
        
        if (lastMessage) {
            const buttonContainer = document.createElement('div');
            buttonContainer.innerHTML = buttonHtml;
            lastMessage.appendChild(buttonContainer.firstElementChild);

            // Add event listener
            const emailBtn = lastMessage.querySelector('.email-doc-btn');
            if (emailBtn) {
                emailBtn.addEventListener('click', () => {
                    promptEmailDocument(filename, filepath, originalName);
                });
            }
        }
    }

    /**
     * Prompt user for email details and send document
     */
    function promptEmailDocument(filename, filepath, originalName) {
        const recipient = prompt('Enter recipient email address:');
        if (!recipient) return;

        const subject = prompt('Enter email subject:', `Document: ${originalName}`);
        if (!subject) return;

        const body = prompt('Enter email message:', `Please find the attached document: ${originalName}`);
        if (!body) return;

        // Send email with document
        sendDocumentEmail(recipient, subject, body, filepath, originalName);
    }

    /**
     * Send document via email
     */
    async function sendDocumentEmail(toEmail, subject, body, filepath, originalName) {
        if (window.ChatUI) {
            window.ChatUI.addBotMessage('📧 Sending email...');
        }

        try {
            const response = await fetch('/send_email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    to_email: toEmail,
                    subject: subject,
                    body: body,
                    attachments: [filepath]
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                console.log('[ChatUpload] Email sent successfully');
                if (window.ChatUI) {
                    window.ChatUI.addBotMessage(`✅ Document "${originalName}" sent to ${toEmail}`);
                }
            } else {
                throw new Error(result.error || 'Failed to send email');
            }
        } catch (error) {
            console.error('[ChatUpload] Email error:', error);
            if (window.ChatUI) {
                window.ChatUI.addBotMessage(`❌ Failed to send email: ${error.message}`);
            }
        }
    }

    /**
     * Get list of uploaded files
     */
    function getUploadedFiles() {
        return uploadedFiles;
    }

    // Public API
    return {
        init,
        uploadDocument,
        sendDocumentEmail,
        getUploadedFiles
    };
})();

// Make available globally
window.ChatUpload = ChatUpload;
