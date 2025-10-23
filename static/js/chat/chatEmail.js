/**
 * chatEmail.js - Email draft handling and sending
 * Phase 3: Email automation frontend with AI modification
 */

const ChatEmail = {
    drafts: new Map(), // Store multiple drafts by ID
    draftCounter: 0,

    init() {
        console.log('[ChatEmail] Email module initialized');
    },

    /**
     * Store email draft with unique ID
     */
    setDraft(draft) {
        const draftId = ++this.draftCounter;
        draft.id = draftId;
        this.drafts.set(draftId, draft);
        console.log('[ChatEmail] Draft stored with ID:', draftId);
        return draftId;
    },

    /**
     * Get draft by ID
     */
    getDraft(draftId) {
        return this.drafts.get(draftId);
    },

    /**
     * Send email via backend
     */
    async sendEmail(to, subject, body) {
        console.log(`[ChatEmail] Sending email to: ${to}`);
        
        try {
            const response = await fetch('/send_email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    to_email: to,
                    subject: subject,
                    body: body
                })
            });
            
            const result = await response.json();
            console.log('[ChatEmail] Send result:', result);
            
            if (result.status === 'success') {
                if (window.ChatUI) {
                    window.ChatUI.addSystemMessage('✅ Email sent successfully!', 'success');
                }
                return true;
            } else {
                if (window.ChatUI) {
                    window.ChatUI.addSystemMessage(`❌ Failed to send email: ${result.error}`, 'error');
                }
                return false;
            }
        } catch (error) {
            console.error('[ChatEmail] Error sending email:', error);
            if (window.ChatUI) {
                window.ChatUI.addSystemMessage('❌ Error sending email', 'error');
            }
            return false;
        }
    },

    /**
     * Modify email draft using AI
     */
    async modifyDraft(draftId, modifications) {
        console.log(`[ChatEmail] Modifying draft ${draftId} with: ${modifications}`);
        
        const draft = this.getDraft(draftId);
        if (!draft) {
            console.error('[ChatEmail] Draft not found:', draftId);
            return null;
        }
        
        try {
            if (window.ChatUI) {
                window.ChatUI.addSystemMessage('🤖 AI is modifying your draft...', 'info');
            }
            
            const response = await fetch('/modify_email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    draft: {
                        subject: draft.subject,
                        body: draft.body,
                        to_email: draft.to_email
                    },
                    modifications: modifications
                })
            });
            
            const result = await response.json();
            console.log('[ChatEmail] Modify result:', result);
            
            if (result.status === 'success') {
                // Update stored draft
                const modifiedDraft = result.draft;
                modifiedDraft.id = draftId;
                this.drafts.set(draftId, modifiedDraft);
                
                if (window.ChatUI) {
                    window.ChatUI.addSystemMessage('✅ Draft modified successfully!', 'success');
                }
                return modifiedDraft;
            }
                if (window.ChatUI) {
                    window.ChatUI.addSystemMessage(`❌ Failed to modify draft: ${result.error}`, 'error');
                }
                return null;
            }
        } catch (error) {
            console.error('[ChatEmail] Error modifying draft:', error);
            if (window.ChatUI) {
                window.ChatUI.addSystemMessage('❌ Error modifying draft', 'error');
            }
            return null;
        }
    }
};

// Export to global scope
window.ChatEmail = ChatEmail;
