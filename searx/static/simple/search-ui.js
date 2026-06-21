// Search UI Enhancement - Loading Indicator
(function() {
    'use strict';
    
    console.log('[SEARCH-UI] Script loaded');
    
    function initSearchUI() {
        var searchForm = document.getElementById('search');
        if (!searchForm) {
            console.log('[SEARCH-UI] Search form not found');
            return;
        }
        
        var searchInput = document.getElementById('q');
        var isSubmitting = false;
        
        // Create loading overlay
        var loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'search-loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="search-loading-content">
                <div class="search-loading-spinner"></div>
                <div class="search-loading-text">Searching...</div>
                <div class="search-loading-subtext">Finding the best results for you</div>
            </div>
        `;
        document.body.appendChild(loadingOverlay);
        
        // Add CSS for loading overlay
        var style = document.createElement('style');
        style.textContent = `
            #search-loading-overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(255, 255, 255, 0.95);
                z-index: 99999;
                justify-content: center;
                align-items: center;
                backdrop-filter: blur(5px);
            }
            
            #search-loading-overlay.active {
                display: flex !important;
            }
            
            .search-loading-content {
                text-align: center;
                padding: 40px;
            }
            
            .search-loading-spinner {
                width: 60px;
                height: 60px;
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                animation: searchSpin 1s linear infinite;
                margin: 0 auto 20px;
            }
            
            @keyframes searchSpin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .search-loading-text {
                color: #667eea;
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 10px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .search-loading-subtext {
                color: #888;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            /* Mobile Responsive */
            @media (max-width: 768px) {
                .search-loading-spinner {
                    width: 50px;
                    height: 50px;
                }
                .search-loading-text {
                    font-size: 20px;
                }
                .search-loading-subtext {
                    font-size: 14px;
                }
            }
            
            /* Dark Mode */
            @media (prefers-color-scheme: dark) {
                #search-loading-overlay {
                    background: rgba(30, 30, 30, 0.95);
                }
                .search-loading-spinner {
                    border-color: #444;
                    border-top-color: #8b9dc3;
                }
                .search-loading-text {
                    color: #8b9dc3;
                }
                .search-loading-subtext {
                    color: #aaa;
                }
            }
        `;
        document.head.appendChild(style);
        
        // Handle form submission
        searchForm.addEventListener('submit', function(e) {
            if (isSubmitting) {
                e.preventDefault();
                console.log('[SEARCH-UI] Already submitting, preventing duplicate');
                return false;
            }
            
            var query = searchInput ? searchInput.value.trim() : '';
            if (!query) {
                e.preventDefault();
                console.log('[SEARCH-UI] Empty query, preventing submission');
                return false;
            }
            
            isSubmitting = true;
            loadingOverlay.classList.add('active');
            console.log('[SEARCH-UI] Search submitted, showing loading overlay');
            
            // Safety timeout - hide after 30 seconds
            setTimeout(function() {
                loadingOverlay.classList.remove('active');
                isSubmitting = false;
            }, 30000);
        });
        
        // Handle Enter key in search input
        if (searchInput) {
            searchInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && isSubmitting) {
                    e.preventDefault();
                    console.log('[SEARCH-UI] Enter pressed while submitting, preventing duplicate');
                    return false;
                }
            });
        }
        
        // Hide loading overlay when page loads (in case of back button)
        window.addEventListener('pageshow', function() {
            loadingOverlay.classList.remove('active');
            isSubmitting = false;
        });
        
        console.log('[SEARCH-UI] Initialization complete');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSearchUI);
    } else {
        initSearchUI();
    }
})();
