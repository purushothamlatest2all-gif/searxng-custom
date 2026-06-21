// Aggressively remove ALL borders, shadows, and backgrounds
(function() {
    'use strict';
    
    console.log('[REMOVE-BORDERS] Script loaded');
    
    function removeAllLines() {
        // Get all elements in search area
        var searchArea = document.getElementById('search');
        if (!searchArea) return;
        
        var allElements = searchArea.querySelectorAll('*');
        allElements = [searchArea].concat(Array.from(allElements));
        
        var count = 0;
        
        allElements.forEach(function(el) {
            var style = window.getComputedStyle(el);
            var changed = false;
            
            // Remove borders
            if (style.borderTopWidth !== '0px' || 
                style.borderBottomWidth !== '0px' || 
                style.borderLeftWidth !== '0px' || 
                style.borderRightWidth !== '0px') {
                el.style.border = 'none';
                el.style.borderTop = 'none';
                el.style.borderBottom = 'none';
                el.style.borderLeft = 'none';
                el.style.borderRight = 'none';
                changed = true;
            }
            
            // Remove box-shadow
            if (style.boxShadow !== 'none') {
                el.style.boxShadow = 'none';
                changed = true;
            }
            
            // Remove background-image (gradients)
            if (style.backgroundImage !== 'none') {
                el.style.backgroundImage = 'none';
                el.style.background = 'transparent';
                changed = true;
            }
            
            // Remove outline
            if (style.outlineWidth !== '0px') {
                el.style.outline = 'none';
                changed = true;
            }
            
            if (changed) count++;
        });
        
        console.log('[REMOVE-BORDERS] Removed lines from', count, 'elements');
    }
    
    // Run multiple times to catch all elements
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', removeAllLines);
    } else {
        removeAllLines();
    }
    
    setTimeout(removeAllLines, 100);
    setTimeout(removeAllLines, 500);
    setTimeout(removeAllLines, 1000);
    setTimeout(removeAllLines, 2000);
})();
