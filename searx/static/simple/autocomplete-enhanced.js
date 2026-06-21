// Enhanced Autocomplete with Spelling Correction
(function() {
    'use strict';
    
    console.log('[AUTOCOMPLETE] Script loaded');
    
    const searchInput = document.getElementById('q');
    if (!searchInput) {
        console.log('[AUTOCOMPLETE] Search input not found');
        return;
    }
    
    // Create autocomplete container
    let autocompleteContainer = document.getElementById('autocomplete-dropdown');
    if (!autocompleteContainer) {
        autocompleteContainer = document.createElement('div');
        autocompleteContainer.id = 'autocomplete-dropdown';
        autocompleteContainer.className = 'autocomplete-dropdown';
        searchInput.parentNode.appendChild(autocompleteContainer);
    }
    
    // Create spelling suggestion container
    let spellingContainer = document.getElementById('spelling-suggestion');
    if (!spellingContainer) {
        spellingContainer = document.createElement('div');
        spellingContainer.id = 'spelling-suggestion';
        spellingContainer.className = 'spelling-suggestion';
        searchInput.parentNode.insertBefore(spellingContainer, searchInput.nextSibling);
    }
    
    let debounceTimer;
    let currentQuery = '';
    
    // Debounce function
    function debounce(func, wait) {
        return function(...args) {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => func.apply(this, args), wait);
        };
    }
    
    // Fetch autocomplete suggestions
    async function fetchSuggestions(query) {
        if (query.length < 2) {
            hideAutocomplete();
            return;
        }
        
        try {
            const response = await fetch(`/autocompleter?q=${encodeURIComponent(query)}`);
            if (response.ok) {
                const data = await response.json();
                if (data && data.length > 0) {
                    showAutocomplete(data, query);
                } else {
                    hideAutocomplete();
                }
            }
        } catch (error) {
            console.error('[AUTOCOMPLETE] Error fetching suggestions:', error);
            hideAutocomplete();
        }
    }
    
    // Fetch spelling corrections
    async function checkSpelling(query) {
        if (query.length < 3) {
            hideSpellingSuggestion();
            return;
        }
        
        try {
            const response = await fetch('/api/spelling', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.has_corrections) {
                    showSpellingSuggestion(data);
                } else {
                    hideSpellingSuggestion();
                }
            }
        } catch (error) {
            console.error('[SPELLING] Error checking spelling:', error);
            hideSpellingSuggestion();
        }
    }
    
    // Show autocomplete dropdown
    function showAutocomplete(suggestions, query) {
        autocompleteContainer.innerHTML = '';
        
        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            
            // Highlight matching text
            const highlighted = suggestion.replace(
                new RegExp(query, 'gi'),
                match => `<strong>${match}</strong>`
            );
            
            item.innerHTML = `
                <span class="autocomplete-icon">🔍</span>
                <span class="autocomplete-text">${highlighted}</span>
            `;
            
            item.addEventListener('click', () => {
                searchInput.value = suggestion;
                hideAutocomplete();
                // Submit the form
                const form = searchInput.closest('form');
                if (form) {
                    form.submit();
                }
            });
            
            autocompleteContainer.appendChild(item);
        });
        
        autocompleteContainer.style.display = 'block';
    }
    
    // Hide autocomplete dropdown
    function hideAutocomplete() {
        autocompleteContainer.style.display = 'none';
    }
    
    // Show spelling suggestion
    function showSpellingSuggestion(data) {
        spellingContainer.innerHTML = `
            <span class="spelling-text">Did you mean:</span>
            <a href="#" class="spelling-link" data-corrected="${data.corrected}">
                ${data.corrected}
            </a>
        `;
        
        // Add click handler for correction link
        const link = spellingContainer.querySelector('.spelling-link');
        if (link) {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                searchInput.value = data.corrected;
                const form = searchInput.closest('form');
                if (form) {
                    form.submit();
                }
            });
        }
        
        spellingContainer.style.display = 'block';
    }
    
    // Hide spelling suggestion
    function hideSpellingSuggestion() {
        spellingContainer.style.display = 'none';
    }
    
    // Handle input changes
    const handleInput = debounce(function(e) {
        const query = e.target.value.trim();
        
        if (query !== currentQuery) {
            currentQuery = query;
            fetchSuggestions(query);
            checkSpelling(query);
        }
    }, 300);
    
    searchInput.addEventListener('input', handleInput);
    
    // Hide autocomplete when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !autocompleteContainer.contains(e.target)) {
            hideAutocomplete();
        }
    });
    
    // Hide autocomplete on escape
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideAutocomplete();
        }
    });
    
    console.log('[AUTOCOMPLETE] Initialization complete');
})();
