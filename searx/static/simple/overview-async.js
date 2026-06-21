// AI Overview Async Loader - Handles both GET and POST
(function() {
    'use strict';
    
    console.log('[OVERVIEW] Script loaded');
    
    function initOverview() {
        console.log('[OVERVIEW] Initializing...');
        
        // Check if we're on a search results page
        const resultsContainer = document.querySelector('#urls') || 
                                 document.querySelector('#results');
        
        if (!resultsContainer) {
            console.log('[OVERVIEW] Not a search results page');
            return;
        }
        
        // Try to get query from URL first (GET request)
        const urlParams = new URLSearchParams(window.location.search);
        let query = urlParams.get('q');
        
        // If not in URL, check the search input field (POST request)
        if (!query) {
            const searchInput = document.querySelector('input[name="q"]');
            if (searchInput && searchInput.value) {
                query = searchInput.value;
                console.log('[OVERVIEW] Query found in input field:', query);
            }
        }
        
        if (!query) {
            console.log('[OVERVIEW] No search query found');
            return;
        }
        
        console.log('[OVERVIEW] Search query:', query);
        
        // Create overview container
        const overviewContainer = document.createElement('div');
        overviewContainer.id = 'ai-overview';
        overviewContainer.className = 'ai-overview';
        overviewContainer.innerHTML = `
            <div class="overview-loading">
                <div class="loading-spinner"></div>
                <p>🤖 Generating AI overview...</p>
            </div>
        `;
        
        // Insert BEFORE the results
        if (resultsContainer.parentNode) {
            resultsContainer.parentNode.insertBefore(overviewContainer, resultsContainer);
            console.log('[OVERVIEW] Container inserted');
        }
        
        // Extract search results
        function extractSearchResults() {
            const results = [];
            const articles = document.querySelectorAll('article.result');
            
            console.log('[OVERVIEW] Found', articles.length, 'articles');
            
            articles.forEach((article, index) => {
                if (index >= 5) return;
                
                const titleEl = article.querySelector('h3 a');
                const contentEl = article.querySelector('.content, p');
                
                if (titleEl && contentEl) {
                    results.push({
                        title: titleEl.textContent.trim(),
                        content: contentEl.textContent.trim(),
                        url: titleEl.href || ''
                    });
                }
            });
            
            console.log('[OVERVIEW] Extracted', results.length, 'results');
            return results;
        }
        
        // Wait for results to load, then fetch overview
        setTimeout(() => {
            const searchResults = extractSearchResults();
            
            if (searchResults.length === 0) {
                console.log('[OVERVIEW] No results to summarize');
                overviewContainer.style.display = 'none';
                return;
            }
            
            console.log('[OVERVIEW] Fetching overview from API...');
            
            fetch('/api/overview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    query: query,
                    search_results: searchResults
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('[OVERVIEW] API response:', data);
                
                if (data && data.overview) {
                    let sourcesHtml = '';
                    if (data.sources && data.sources.length > 0) {
                        sourcesHtml = '<div class="overview-sources"><strong>Sources:</strong> ' + 
                            data.sources.map(s => `<a href="${s.url}" target="_blank">${s.title}</a>`).join(' • ') + 
                            '</div>';
                    }
                    
                    overviewContainer.innerHTML = `
                        <div class="overview-content">
                            <h3>🤖 AI Overview</h3>
                            <div class="overview-text">${data.overview}</div>
                            ${sourcesHtml}
                        </div>
                    `;
                    console.log('[OVERVIEW] ✅ Overview displayed');
                } else {
                    overviewContainer.style.display = 'none';
                    console.log('[OVERVIEW] No overview available');
                }
            })
            .catch(error => {
                console.error('[OVERVIEW] Error:', error);
                overviewContainer.style.display = 'none';
            });
        }, 1500);
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initOverview);
    } else {
        initOverview();
    }
})();
