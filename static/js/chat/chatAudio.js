/**
 * chatAudio.js - Voice recording (STT) and TTS playback
 */

const ChatAudio = {
    mediaRecorder: null,
    audioChunks: [],
    isRecording: false,
    audioContext: null,
    currentAudio: null,

    /**
     * Initialize audio system
     */
    init() {
        console.log('[ChatAudio] Initializing audio system');
        
        // Check browser support
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            console.error('[ChatAudio] MediaDevices API not supported');
            return;
        }
        
        console.log('[ChatAudio] Audio system initialized');
    },

    /**
     * Toggle recording on/off
     */
    async toggleRecording() {
        console.log(`[ChatAudio] Toggle recording - Current state: ${this.isRecording}`);
        
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    },

    /**
     * Start recording audio
     */
    async startRecording() {
        try {
            console.log('[ChatAudio] Starting recording...');
            
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            console.log('[ChatAudio] Microphone access granted');
            
            // Create media recorder
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            // Collect audio data
            this.mediaRecorder.addEventListener('dataavailable', (event) => {
                console.log(`[ChatAudio] Audio data chunk received: ${event.data.size} bytes`);
                this.audioChunks.push(event.data);
            });
            
            // Handle recording stop
            this.mediaRecorder.addEventListener('stop', () => {
                console.log('[ChatAudio] Recording stopped, processing audio...');
                this.processRecording();
            });
            
            // Start recording
            this.mediaRecorder.start();
            this.isRecording = true;
            
            // Update UI
            if (window.ChatUI) {
                window.ChatUI.updateMicButton(true);
                window.ChatUI.addSystemMessage('🎤 Recording...', 'info');
            }
            
            console.log('[ChatAudio] Recording started successfully');
            
        } catch (error) {
            console.error('[ChatAudio] Error starting recording:', error);
            if (window.ChatUI) {
                window.ChatUI.addSystemMessage('Failed to access microphone', 'error');
            }
        }
    },

    /**
     * Stop recording audio
     */
    stopRecording() {
        console.log('[ChatAudio] Stopping recording...');
        
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Stop all tracks
            if (this.mediaRecorder.stream) {
                this.mediaRecorder.stream.getTracks().forEach(track => {
                    track.stop();
                    console.log('[ChatAudio] Audio track stopped');
                });
            }
            
            // Update UI
            if (window.ChatUI) {
                window.ChatUI.updateMicButton(false);
            }
        }
    },

    /**
     * Process recorded audio and send to STT
     */
    async processRecording() {
        try {
            console.log(`[ChatAudio] Processing ${this.audioChunks.length} audio chunks`);
            
            // Create audio blob
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            console.log(`[ChatAudio] Audio blob created: ${audioBlob.size} bytes`);
            
            // Send to STT endpoint
            await this.sendToSTT(audioBlob);
            
        } catch (error) {
            console.error('[ChatAudio] Error processing recording:', error);
            if (window.ChatUI) {
                window.ChatUI.addSystemMessage('Failed to process audio', 'error');
            }
        }
    },

    /**
     * Send audio to STT endpoint
     * @param {Blob} audioBlob - Recorded audio blob
     */
    async sendToSTT(audioBlob) {
        try {
            console.log('[ChatAudio] Sending audio to STT endpoint...');
            
            if (window.ChatUI) {
                window.ChatUI.addSystemMessage('🔄 Converting speech to text...', 'info');
                window.ChatUI.disableInput();
            }
            
            // Create form data
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            
            // Send to server
            const response = await fetch('/stt', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            console.log('[ChatAudio] STT response:', result);
            
            if (result.status === 'success' && result.text) {
                console.log(`[ChatAudio] Transcribed text: ${result.text}`);
                
                // Set transcribed text in input
                if (window.ChatUI) {
                    window.ChatUI.setInput(result.text);
                }
                
                // Auto-send the transcribed message with TTS enabled
                if (window.ChatCore) {
                    window.ChatCore.sendMessage(true); // true = enable TTS
                }
            } else {
                console.error('[ChatAudio] STT failed:', result.error);
                if (window.ChatUI) {
                    window.ChatUI.addSystemMessage('Failed to convert speech to text', 'error');
                    window.ChatUI.enableInput();
                }
            }
            
        } catch (error) {
            console.error('[ChatAudio] Error sending to STT:', error);
            if (window.ChatUI) {
                window.ChatUI.addSystemMessage('Failed to convert speech to text', 'error');
                window.ChatUI.enableInput();
            }
        }
    },

    /**
     * Play TTS audio from URL
     * @param {string} audioUrl - URL to audio file
     */
    async playTTS(audioUrl) {
        try {
            console.log(`[ChatAudio] Playing TTS audio from: ${audioUrl}`);
            
            // Stop current audio if playing
            if (this.currentAudio) {
                this.currentAudio.pause();
                this.currentAudio = null;
            }
            
            // Create and play new audio
            this.currentAudio = new Audio(audioUrl);
            
            this.currentAudio.addEventListener('play', () => {
                console.log('[ChatAudio] TTS audio started playing');
            });
            
            this.currentAudio.addEventListener('ended', () => {
                console.log('[ChatAudio] TTS audio finished playing');
                this.currentAudio = null;
            });
            
            this.currentAudio.addEventListener('error', (error) => {
                console.error('[ChatAudio] Error playing TTS audio:', error);
                this.currentAudio = null;
            });
            
            await this.currentAudio.play();
            
        } catch (error) {
            console.error('[ChatAudio] Error playing TTS:', error);
        }
    },

    /**
     * Stop current audio playback
     */
    stopAudio() {
        if (this.currentAudio) {
            console.log('[ChatAudio] Stopping current audio');
            this.currentAudio.pause();
            this.currentAudio = null;
        }
    }
};

// Export for use in other modules
window.ChatAudio = ChatAudio;
