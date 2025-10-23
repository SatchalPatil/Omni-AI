/**
 * chatReport.js - Report generation and download
 * Phase 4: PDF report generation from SQL results
 */

const ChatReport = {
    currentPreview: null,

    init() {
        console.log('[ChatReport] Report module initialized');
    },

    /**
     * Store report preview
     */
    setPreview(preview) {
        this.currentPreview = preview;
        console.log('[ChatReport] Preview stored:', preview);
    },

    /**
     * Generate PDF report
     */
    async generateReport(title = 'Data Report') {
        console.log(`[ChatReport] Generating report: ${title}`);
        
        try {
            if (window.ChatUI) {
                window.ChatUI.addSystemMessage('🔄 Generating PDF report...', 'info');
            }
            
            const response = await fetch('/generate_report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    confirm: true,
                    title: title
                })
            });
            
            const result = await response.json();
            console.log('[ChatReport] Generate result:', result);
            
            if (result.status === 'success' && result.pdf_path) {
                // Extract filename from path (handle both / and \)
                const filename = result.pdf_path.split('/').pop().split('\\').pop();
                const downloadUrl = `/download_report/${filename}`;
                
                if (window.ChatUI) {
                    window.ChatUI.addSystemMessage('✅ Report generated successfully!', 'success');
                }
                
                // Trigger download
                this.downloadFile(downloadUrl, filename);
                
                return true;
            } else {
                if (window.ChatUI) {
                    window.ChatUI.addSystemMessage(`❌ Failed: ${result.error}`, 'error');
                }
                return false;
            }
        } catch (error) {
            console.error('[ChatReport] Error generating report:', error);
            if (window.ChatUI) {
                window.ChatUI.addSystemMessage('❌ Error generating report', 'error');
            }
            return false;
        }
    },

    /**
     * Download file
     */
    downloadFile(url, filename) {
        console.log(`[ChatReport] Downloading: ${url}`);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log('[ChatReport] Download triggered');
        
        // Ask if user wants to email the report
        setTimeout(() => {
            this.promptEmailReport(filename);
        }, 500);
    },
    
    /**
     * Prompt user to email report
     */
    promptEmailReport(filename) {
        if (window.ChatUI) {
            const message = `\n📧 Would you like to send this report via email?`;
            window.ChatUI.addSystemMessage(message, 'info');
            
            // Add email button
            this.addEmailReportButton(filename);
        }
    },
    
    /**
     * Add email button for report
     */
    addEmailReportButton(filename) {
        const buttonHtml = `
            <div class="action-buttons">
                <button class="email-report-btn" data-filename="${filename}">
                    📧 Email Report
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
            const emailBtn = lastMessage.querySelector('.email-report-btn');
            if (emailBtn) {
                emailBtn.addEventListener('click', () => {
                    this.emailReport(filename);
                });
            }
        }
    },
    
    /**
     * Send report via email
     */
    async emailReport(filename) {
        const recipient = prompt('Enter recipient email address:');
        if (!recipient) return;

        const subject = prompt('Enter email subject:', `Data Report: ${filename}`);
        if (!subject) return;

        const body = prompt('Enter email message:', `Please find the attached data report.`);
        if (!body) return;

        console.log(`[ChatReport] Emailing report ${filename} to ${recipient}`);
        
        if (window.ChatUI) {
            window.ChatUI.addSystemMessage('📧 Sending email...', 'info');
        }

        try {
            const response = await fetch('/email_report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    to_email: recipient,
                    subject: subject,
                    body: body,
                    filename: filename
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                console.log('[ChatReport] Email sent successfully');
                if (window.ChatUI) {
                    window.ChatUI.addSystemMessage(`✅ Report sent to ${recipient}`, 'success');
                }
            } else {
                throw new Error(result.error || 'Failed to send email');
            }
        } catch (error) {
            console.error('[ChatReport] Email error:', error);
            if (window.ChatUI) {
                window.ChatUI.addSystemMessage(`❌ Failed to send email: ${error.message}`, 'error');
            }
        }
    }
};

window.ChatReport = ChatReport;
