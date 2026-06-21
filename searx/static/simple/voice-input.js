// Voice Input for Search Bar
(function() {
    'use strict';
    
    console.log('[VOICE] Script loaded');
    
    function initVoiceInput() {
        var voiceBtn = document.getElementById('voice_btn');
        var searchInput = document.getElementById('q');
        
        if (!voiceBtn || !searchInput) {
            console.log('[VOICE] Voice button or search input not found');
            return;
        }
        
        console.log('[VOICE] Initializing voice input');
        
        // Check for browser support
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.log('[VOICE] Speech recognition not supported');
            voiceBtn.style.display = 'none';
            return;
        }
        
        var recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        var isListening = false;
        
        recognition.onstart = function() {
            isListening = true;
            voiceBtn.classList.add('listening');
            voiceBtn.title = 'Listening... Click to stop';
            console.log('[VOICE] Listening started');
        };
        
        recognition.onresult = function(event) {
            var transcript = event.results[0][0].transcript;
            console.log('[VOICE] Recognized: ' + transcript);
            searchInput.value = transcript;
            voiceBtn.classList.remove('listening');
            isListening = false;
            
            // Auto-submit after short delay
            setTimeout(function() {
                var form = searchInput.closest('form');
                if (form) {
                    form.submit();
                }
            }, 500);
        };
        
        recognition.onerror = function(event) {
            console.error('[VOICE] Error: ' + event.error);
            voiceBtn.classList.remove('listening');
            isListening = false;
            
            if (event.error === 'not-allowed') {
                alert('Please allow microphone access to use voice search.');
            } else if (event.error === 'no-speech') {
                console.log('[VOICE] No speech detected');
            }
        };
        
        recognition.onend = function() {
            voiceBtn.classList.remove('listening');
            isListening = false;
            voiceBtn.title = 'Search by voice';
            console.log('[VOICE] Listening ended');
        };
        
        voiceBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            if (isListening) {
                recognition.stop();
            } else {
                try {
                    recognition.start();
                } catch (err) {
                    console.error('[VOICE] Failed to start recognition:', err);
                }
            }
        });
        
        console.log('[VOICE] Voice input initialized successfully');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initVoiceInput);
    } else {
        initVoiceInput();
    }
})();
