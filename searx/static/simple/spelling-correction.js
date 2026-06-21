/**
 * Spelling Correction Handler with Debounce
 */
(function() {
    'use strict';
    
    console.log('[SPELLING] Script loaded');
    
    let debounceTimer = null;
    const DEBOUNCE_DELAY = 1000; // Wait 1 second after user stops typing
    
    /**
     * Debounced spelling check
     */
    function debouncedCheckSpelling(query) {
        // Clear existing timer
        if (debounceTimer) {
            clearTimeout(debounceTimer);
        }
        
        // Set new timer
        debounceTimer = setTimeout(() => {
            checkAndCorrectSpelling(query);
        }, DEBOUNCE_DELAY);
    }
    
    /**
     * Check spelling for the current query and show suggestions if needed
     */
    async function checkAndCorrectSpelling(query) {
        if (!query || query.length < 5) {
            return; // Don't check very short queries
        }
        
        // Check if we're on a results page
        var isResultsPage = document.querySelector('#results') !== null;
        if (!isResultsPage) {
            return;
        }
        
        try {
            console.log('[SPELLING] Checking spelling for:', query);
            
            var response = await fetch('/api/spelling', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ query: query })
            });
            
            if (!response.ok) {
                console.warn('[SPELLING] API error:', response.status);
                return;
            }
            
            var data = await response.json();
            console.log('[SPELLING] Result:', data);
            
            // Only show suggestion if has corrections and not skipped
            if (data.has_corrections && data.corrected !== query && !data.skipped) {
                console.log('[SPELLING] Correction found:', query, '→', data.corrected);
                showSuggestion(query, data);
            } else if (data.suggestions && data.suggestions.length > 0 && !data.skipped) {
                console.log('[SPELLING] Suggestions available');
                showSuggestion(query, data);
            } else {
                // Remove any existing suggestion
                var existing = document.getElementById('spelling-suggestion');
                if (existing) {
                    existing.remove();
                }
            }
            
        } catch (error) {
            console.error('[SPELLING] Error:', error);
        }
    }
    
    /**
     * Display the spelling suggestion to the user
     */
    function showSuggestion(originalQuery, data) {
        // Remove any existing suggestion
        var existing = document.getElementById('spelling-suggestion');
        if (existing) {
            existing.remove();
        }
        
        // Create suggestion element
        var suggestionDiv = document.createElement('div');
        suggestionDiv.id = 'spelling-suggestion';
        suggestionDiv.style.cssText = 'background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px; padding: 12px 16px; margin: 10px 0; font-size: 14px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;';
        
        // Build suggestion text
        var message = '';
        if (data.has_corrections && data.corrected) {
            message = `Showing results for <strong style="color: #0066cc; cursor: pointer; text-decoration: underline;" onclick="window.location.href='/search?q=' + encodeURIComponent('${data.corrected.replace(/'/g, "\\'")}')">${escapeHtml(data.corrected)}</strong>`;
            
            // Add "Search instead for" link
            message += ` <span style="color: #666; margin: 0 8px;">|</span> `;
            message += `Search instead for <strong style="color: #666; cursor: pointer; text-decoration: underline;" onclick="window.location.href='/search?q=' + encodeURIComponent('${originalQuery.replace(/'/g, "\\'")}')">${escapeHtml(originalQuery)}</strong>`;
        } else if (data.suggestions && data.suggestions.length > 0) {
            message = `Did you mean: `;
            message += data.suggestions.slice(0, 3).map(function(suggestion) {
                return `<strong style="color: #0066cc; cursor: pointer; text-decoration: underline; margin-right: 10px;" onclick="window.location.href='/search?q=' + encodeURIComponent('${suggestion.replace(/'/g, "\\'")}')">${escapeHtml(suggestion)}</strong>`;
            }).join('');
        }
        
        suggestionDiv.innerHTML = message;
        
        // Insert before results
        var resultsDiv = document.getElementById('results');
        if (resultsDiv && resultsDiv.parentNode) {
            resultsDiv.parentNode.insertBefore(suggestionDiv, resultsDiv);
            console.log('[SPELLING] Suggestion displayed');
        }
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Monitor search input for changes
     */
    function monitorSearchInput() {
        var searchInput = document.getElementById('q') || document.querySelector('input[name="q"]');
        if (!searchInput) return;
        
        // Listen for input changes
        searchInput.addEventListener('input', function(e) {
            var query = e.target.value.trim();
            if (query.length >= 5) {
                debouncedCheckSpelling(query);
            }
        });
        
        // Also check on page load (for direct URL searches)
        var initialQuery = searchInput.value.trim();
        if (initialQuery.length >= 5) {
            // Delay initial check to ensure page is fully loaded
            setTimeout(() => {
                checkAndCorrectSpelling(initialQuery);
            }, 1000);
        }
    }
    
    // Initialize after page loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', monitorSearchInput);
    } else {
        monitorSearchInput();
    }
})();
