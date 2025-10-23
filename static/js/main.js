/**
 * main.js - Main application initialization
 * Loads and initializes all chat modules
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Main] DOM loaded, initializing application...');
    
    // Initialize all modules in order
    initializeApp();
});

/**
 * Initialize all application modules
 */
function initializeApp() {
    console.log('[Main] Starting application initialization');
    
    try {
        // 1. Initialize utilities (context, language)
        if (window.ChatUtils) {
            window.ChatUtils.init();
            console.log('[Main] ✓ ChatUtils initialized');
        } else {
            console.error('[Main] ✗ ChatUtils not loaded');
        }
        
        // 2. Initialize UI (message area, input, buttons)
        if (window.ChatUI) {
            window.ChatUI.init();
            console.log('[Main] ✓ ChatUI initialized');
        } else {
            console.error('[Main] ✗ ChatUI not loaded');
        }
        
        // 3. Initialize audio (microphone, TTS)
        if (window.ChatAudio) {
            window.ChatAudio.init();
            console.log('[Main] ✓ ChatAudio initialized');
        } else {
            console.error('[Main] ✗ ChatAudio not loaded');
        }
        
        // 4. Initialize email module (Phase 3)
        if (window.ChatEmail) {
            window.ChatEmail.init();
            console.log('[Main] ✓ ChatEmail initialized');
        } else {
            console.error('[Main] ✗ ChatEmail not loaded');
        }
        
        // 5. Initialize report module (Phase 4)
        if (window.ChatReport) {
            window.ChatReport.init();
            console.log('[Main] ✓ ChatReport initialized');
        } else {
            console.error('[Main] ✗ ChatReport not loaded');
        }
        
        // 6. Initialize upload module (Document Upload)
        if (window.ChatUpload) {
            window.ChatUpload.init();
            console.log('[Main] ✓ ChatUpload initialized');
        } else {
            console.error('[Main] ✗ ChatUpload not loaded');
        }
        
        // 7. Initialize core chat functionality
        if (window.ChatCore) {
            window.ChatCore.init();
            console.log('[Main] ✓ ChatCore initialized');
        } else {
            console.error('[Main] ✗ ChatCore not loaded');
        }
        
        console.log('[Main] ✓ Application initialized successfully');
        
        // Restore chat history after all modules are loaded
        if (window.ChatUI && window.ChatUI.restoreChatHistory) {
            window.ChatUI.restoreChatHistory();
            console.log('[Main] Chat history restored');
        }
        
        // Display welcome message only if no history
        const hasHistory = localStorage.getItem('chatHistory');
        if (!hasHistory) {
            displayWelcomeMessage();
        }
        
    } catch (error) {
        console.error('[Main] Error initializing application:', error);
    }
}

/**
 * Display welcome message in chat
 */
function displayWelcomeMessage() {
    if (window.ChatUI) {
        window.ChatUI.addBotMessage('👋 Hello! I\'m your AI assistant. How can I help you today?');
        console.log('[Main] Welcome message displayed');
    }
}

// Export for debugging
window.App = {
    version: '4.0.0 - Phase 4 (Report Generation)',
    reinitialize: initializeApp
};

console.log('[Main] main.js loaded');
