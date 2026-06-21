// Find the exact source of the line - FIXED VERSION
(function() {
    'use strict';
    
    console.log('[FIND-LINE] Starting comprehensive scan...');
    
    function findAllLines() {
        var foundLines = [];
        
        // Check all elements in search area
        var searchArea = document.getElementById('search');
        if (!searchArea) {
            console.log('[FIND-LINE] No search element found');
            return;
        }
        
        var allElements = searchArea.querySelectorAll('*');
        allElements = [searchArea].concat(Array.from(allElements));
        
        allElements.forEach(function(el) {
            var style = window.getComputedStyle(el);
            var tagName = el.tagName.toLowerCase();
            var id = el.id ? '#' + el.id : '';
            var classes = '';
            
            // FIX: Check if className is a string before splitting
            if (typeof el.className === 'string' && el.className) {
                classes = '.' + el.className.split(' ').join('.');
            }
            
            var selector = tagName + id + classes;
            
            // Check borders
            if (style.borderTopWidth !== '0px' || 
                style.borderBottomWidth !== '0px' || 
                style.borderLeftWidth !== '0px' || 
                style.borderRightWidth !== '0px') {
                console.log('[FIND-LINE] BORDER found on:', selector);
                console.log('  Top:', style.borderTopWidth, style.borderTopStyle, style.borderTopColor);
                console.log('  Bottom:', style.borderBottomWidth, style.borderBottomStyle, style.borderBottomColor);
                foundLines.push({type: 'border', element: selector, el: el});
            }
            
            // Check box-shadow
            if (style.boxShadow !== 'none') {
                console.log('[FIND-LINE] BOX-SHADOW found on:', selector);
                console.log('  Shadow:', style.boxShadow);
                foundLines.push({type: 'shadow', element: selector, el: el});
            }
        });
        
        if (foundLines.length === 0) {
            console.log('[FIND-LINE] ✅ No lines found! All clean.');
        } else {
            console.log('[FIND-LINE] ❌ Found', foundLines.length, 'potential line sources');
        }
        
        return foundLines;
    }
    
    // Run scan
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', findAllLines);
    } else {
        findAllLines();
    }
    
    setTimeout(findAllLines, 500);
    setTimeout(findAllLines, 1000);
})();
