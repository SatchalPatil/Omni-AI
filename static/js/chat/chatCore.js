/**
 * chatCore.js - Core chat functionality for /chat endpoint communication
 */

const ChatCore = {
    /**
     * Initialize core chat functionality
     */
    init() {
        console.log('[ChatCore] Initializing chat core');
    },

    /**
     * Send message to chat endpoint
     * @param {boolean} enableTTS - Whether to enable TTS for response (for voice input)
     */
    async sendMessage(enableTTS = false) {
        try {
            // Get message from input
            const message = window.ChatUI ? window.ChatUI.getInput() : '';
            
            if (!message) {
                console.log('[ChatCore] Empty message, ignoring');
                return;
            }
            
            console.log(`[ChatCore] Sending message: ${message.substring(0, 50)}... (TTS: ${enableTTS})`);
            
            // Add user message to UI
            if (window.ChatUI) {
                window.ChatUI.addUserMessage(message);
                window.ChatUI.clearInput();
                window.ChatUI.disableInput();
                window.ChatUI.showTypingIndicator();
            }
            
            // Add to context
            if (window.ChatUtils) {
                window.ChatUtils.addToContext('user', message);
            }
            
            // Get context for API call
            const context = window.ChatUtils ? window.ChatUtils.getContext() : [];
            
            // Send to backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    context: context,
                    enable_tts: enableTTS
                })
            });
            
            const result = await response.json();
            console.log('[ChatCore] Response received:', result);
            
            // Hide typing indicator
            if (window.ChatUI) {
                window.ChatUI.hideTypingIndicator();
            }
            
            // Handle response
            if (result.status === 'success') {
                this.handleSuccessResponse(result, enableTTS);
            } else {
                this.handleErrorResponse(result);
            }
            
        } catch (error) {
            console.error('[ChatCore] Error sending message:', error);
            
            if (window.ChatUI) {
                window.ChatUI.hideTypingIndicator();
                window.ChatUI.addSystemMessage('Failed to send message. Please try again.', 'error');
                window.ChatUI.enableInput();
            }
        }
    },

    /**
     * Handle successful response from chat endpoint
     * @param {Object} result - Response data
     * @param {boolean} enableTTS - Whether TTS is enabled
     */
    handleSuccessResponse(result, enableTTS) {
        console.log('[ChatCore] Handling success response');
        console.log('[ChatCore] Response keys:', Object.keys(result));
        
        const responseText = result.text || 'No response received';
        
        // Add bot message to UI
        if (window.ChatUI) {
            window.ChatUI.addBotMessage(responseText);
            
            // Phase 2: Handle SQL response with summary, data table and chart
            // Show summary first for quick insights
            if (result.summary) {
                console.log(`[ChatCore] Rendering AI summary`);
                window.ChatUI.addDataSummary(result.summary);
            }
            
            if (result.data && result.show_table) {
                console.log(`[ChatCore] Rendering data table with ${result.data.length} rows`);
                window.ChatUI.addDataTable(result.data, result.sql);
            }
            
            if (result.chart_html) {
                console.log(`[ChatCore] Rendering Plotly chart (${result.chart_html.length} chars)`);
                window.ChatUI.addChart(result.chart_html);
                
                // Phase 5: Add pin button if pin_option is true
                if (result.pin_option) {
                    console.log('[ChatCore] Adding pin button to chart');
                    this.addPinButton(result, 'chart');
                }
            }
            
            // Phase 3: Handle email draft response
            if (result.draft) {
                console.log('[ChatCore] Email draft received');
                window.ChatUI.addEmailDraft(result.draft);
                // Draft is stored in addEmailDraft via setDraft
            }
            
            // Phase 4: Handle report preview response
            if (result.preview) {
                console.log('[ChatCore] Report preview received');
                window.ChatUI.addReportPreview(result.preview);
                if (window.ChatReport) {
                    window.ChatReport.setPreview(result.preview);
                }
            }
            
            window.ChatUI.enableInput();
        }
        
        // Add to context
        if (window.ChatUtils) {
            window.ChatUtils.addToContext('assistant', responseText);
        }
        
        // Play TTS audio if available and enabled
        if (enableTTS && result.audio_url && window.ChatAudio) {
            console.log(`[ChatCore] Playing TTS audio: ${result.audio_url}`);
            window.ChatAudio.playTTS(result.audio_url);
        }
    },

    /**
     * Handle error response from chat endpoint
     * @param {Object} result - Error response data
     */
    handleErrorResponse(result) {
        console.error('[ChatCore] Error response:', result);
        
        const errorMessage = result.error || 'An error occurred';
        
        if (window.ChatUI) {
            window.ChatUI.addSystemMessage(`Error: ${errorMessage}`, 'error');
            window.ChatUI.enableInput();
        }
    },

    /**
     * Add pin button to chart or report
     * Phase 5: Dashboard pin functionality
     * @param {Object} result - Response data containing chart/report info
     * @param {string} type - Type of content ('chart' or 'report')
     */
    addPinButton(result, type) {
        try {
            const messageArea = document.getElementById('messageArea');
            if (!messageArea) return;
            
            const lastMessage = messageArea.lastElementChild;
            if (!lastMessage) return;
            
            // Create pin button
            const pinButtonDiv = document.createElement('div');
            pinButtonDiv.className = 'action-buttons';
            pinButtonDiv.innerHTML = `
                <button class="pin-chart-btn" data-type="${type}" title="Pin to dashboard">
                    📌 Pin to Dashboard
                </button>
            `;
            
            lastMessage.appendChild(pinButtonDiv);
            
            // Add event listener
            const pinBtn = pinButtonDiv.querySelector('.pin-chart-btn');
            if (pinBtn) {
                pinBtn.addEventListener('click', () => {
                    this.pinToDashboard(result, type);
                });
            }
            
            console.log('[ChatCore] Pin button added');
        } catch (error) {
            console.error('[ChatCore] Error adding pin button:', error);
        }
    },
    
    /**
     * Pin chart or report to dashboard
     * Phase 5: Send pin data to backend
     * @param {Object} result - Response data containing chart/report info
     * @param {string} type - Type of content ('chart' or 'report')
     */
    async pinToDashboard(result, type) {
        try {
            console.log(`[ChatCore] Pinning ${type} to dashboard`);
            console.log('[ChatCore] Full result object:', result);
            console.log('[ChatCore] chart_data exists:', !!result.chart_data);
            console.log('[ChatCore] chart_data value:', result.chart_data);
            
            // Extract chart data
            let pinData = {};
            let title = 'Untitled';
            
            if (type === 'chart' && result.chart_data) {
                console.log('[ChatCore] Extracting chart data...');
                console.log('[ChatCore] chart_data.data:', result.chart_data.data);
                console.log('[ChatCore] chart_data.layout:', result.chart_data.layout);
                
                pinData = {
                    plotly_data: result.chart_data.data || [],
                    plotly_layout: result.chart_data.layout || {},
                    sql: result.sql || '',
                    summary: result.summary || ''
                };
                title = result.chart_data.layout?.title?.text || result.summary?.substring(0, 50) || 'Data Chart';
                
                console.log('[ChatCore] Prepared pinData:', pinData);
                console.log('[ChatCore] Title:', title);
            } else if (type === 'report' && result.preview) {
                pinData = result.preview;
                title = result.preview.title || 'Data Report';
            } else {
                console.error('[ChatCore] No chart_data found in result!');
                if (window.ChatUI) {
                    window.ChatUI.addSystemMessage('Error: Chart data not available', 'error');
                }
                return;
            }
            
            // Send pin request
            const response = await fetch('/pin_chart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: title,
                    type: type,
                    data: pinData
                })
            });
            
            const pinResult = await response.json();
            
            if (pinResult.status === 'success') {
                console.log('[ChatCore] Pinned successfully:', pinResult.pin_id);
                if (window.ChatUI) {
                    window.ChatUI.addSystemMessage('📌 Item pinned to dashboard!', 'success');
                }
            } else {
                console.error('[ChatCore] Failed to pin:', pinResult.error);
                if (window.ChatUI) {
                    window.ChatUI.addSystemMessage('Failed to pin item', 'error');
                }
            }
            
        } catch (error) {
            console.error('[ChatCore] Error pinning to dashboard:', error);
            if (window.ChatUI) {
                window.ChatUI.addSystemMessage('Error pinning item', 'error');
            }
        }
    },

    /**
     * Clear chat history
     */
    clearChat() {
        console.log('[ChatCore] Clearing chat');
        
        if (window.ChatUI) {
            window.ChatUI.clearMessages();
        }
        
        if (window.ChatUtils) {
            window.ChatUtils.clearContext();
        }
        
        console.log('[ChatCore] Chat cleared');
    }
};

// Export for use in other modules
window.ChatCore = ChatCore;
