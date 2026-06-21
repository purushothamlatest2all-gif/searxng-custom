"""
Spelling Correction API - Using SymSpell for context-aware corrections
"""

from flask import Blueprint, request, jsonify
import sys

spelling_api = Blueprint('spelling_api', __name__)


@spelling_api.route('/api/spelling', methods=['POST'])
def check_spelling_endpoint():
    """Check spelling for a query using SymSpell context-aware correction."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query parameter'}), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({
                'original': '',
                'corrected': '',
                'corrections': {},
                'has_corrections': False,
                'confidence': 'none',
                'suggestions': []
            })
        
        try:
            from searx.spell_checker import fix_query, get_suggestions
            
            result = fix_query(query)
            suggestions = get_suggestions(query, max_suggestions=3)
            
            if result['corrected'] in suggestions:
                suggestions.remove(result['corrected'])
            
            if result['has_corrections'] and result['corrected'] not in suggestions:
                suggestions.insert(0, result['corrected'])
            
            response = {
                'original': result['original'],
                'corrected': result['corrected'],
                'corrections': result['corrections'],
                'has_corrections': result['has_corrections'],
                'confidence': result['confidence'],
                'suggestions': suggestions[:5]
            }
            
            if result['has_corrections']:
                print(f"[SPELLING API] Corrected: '{query}' → '{result['corrected']}'", file=sys.stderr)
            
            return jsonify(response)
            
        except ImportError as e:
            print(f"[SPELLING API] ❌ Spell checker module not found: {e}", file=sys.stderr)
            return jsonify({
                'original': query,
                'corrected': query,
                'corrections': {},
                'has_corrections': False,
                'confidence': 'none',
                'suggestions': [],
                'error': 'Spell checker not available'
            })
            
    except Exception as e:
        print(f"[SPELLING API] ❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': f'Internal error: {str(e)}'}), 500
