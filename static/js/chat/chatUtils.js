/**
 * chatUtils.js - Context storage and language switching utilities
 */

const ChatUtils = {
    // Conversation context storage
    context: [],
    maxContextSize: 10, // Keep last 10 messages for context
    currentLanguage: 'en',

    /**
     * Initialize utilities
     */
    init() {
        console.log('[ChatUtils] Initializing utilities');
        this.loadContext();
        this.loadLanguage();
    },

    /**
     * Add message to context
     * @param {string} role - 'user' or 'assistant'
     * @param {string} content - Message content
     */
    addToContext(role, content) {
        console.log(`[ChatUtils] Adding to context - Role: ${role}, Content: ${content.substring(0, 50)}...`);
        
        this.context.push({
            role: role,
            content: content,
            timestamp: new Date().toISOString()
        });

        // Keep only last N messages
        if (this.context.length > this.maxContextSize) {
            this.context = this.context.slice(-this.maxContextSize);
            console.log(`[ChatUtils] Context trimmed to ${this.maxContextSize} messages`);
        }

        this.saveContext();
    },

    /**
     * Get current context
     * @returns {Array} Context array
     */
    getContext() {
        return this.context;
    },

    /**
     * Clear context
     */
    clearContext() {
        console.log('[ChatUtils] Clearing context');
        this.context = [];
        this.saveContext();
    },

    /**
     * Save context to localStorage
     */
    saveContext() {
        try {
            localStorage.setItem('chatContext', JSON.stringify(this.context));
            console.log(`[ChatUtils] Context saved (${this.context.length} messages)`);
        } catch (error) {
            console.error('[ChatUtils] Error saving context:', error);
        }
    },

    /**
     * Load context from localStorage
     */
    loadContext() {
        try {
            const saved = localStorage.getItem('chatContext');
            if (saved) {
                this.context = JSON.parse(saved);
                console.log(`[ChatUtils] Context loaded (${this.context.length} messages)`);
            }
        } catch (error) {
            console.error('[ChatUtils] Error loading context:', error);
            this.context = [];
        }
    },

    /**
     * Set current language
     * @param {string} lang - Language code (e.g., 'en', 'hi', 'mr')
     */
    setLanguage(lang) {
        console.log(`[ChatUtils] Setting language to: ${lang}`);
        this.currentLanguage = lang;
        localStorage.setItem('chatLanguage', lang);
    },

    /**
     * Get current language
     * @returns {string} Current language code
     */
    getLanguage() {
        return this.currentLanguage;
    },

    /**
     * Load language from localStorage
     */
    loadLanguage() {
        try {
            const saved = localStorage.getItem('chatLanguage');
            if (saved) {
                this.currentLanguage = saved;
                console.log(`[ChatUtils] Language loaded: ${this.currentLanguage}`);
            }
        } catch (error) {
            console.error('[ChatUtils] Error loading language:', error);
        }
    },

    /**
     * Format timestamp for display
     * @param {string} timestamp - ISO timestamp
     * @returns {string} Formatted time
     */
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    },

    /**
     * Escape HTML to prevent XSS
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
window.ChatUtils = ChatUtils;
