"""
Async API endpoint for AI Overview - with comprehensive error handling
"""
from flask import Blueprint, request, jsonify
import sys
import traceback

overview_api = Blueprint('overview_api', __name__)

# Global worker instance (singleton)
_worker_instance = None

def get_worker():
    """Get or create worker instance"""
    global _worker_instance
    if _worker_instance is None:
        try:
            from searx.overview_worker import OverviewWorker
            _worker_instance = OverviewWorker()
            print("[OVERVIEW API] ✅ Worker instance created", file=sys.stderr)
        except Exception as e:
            print(f"[OVERVIEW API] ❌ Failed to create worker: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return None
    return _worker_instance

@overview_api.route('/api/overview', methods=['POST'])
def generate_overview():
    """Generate AI overview for a query with comprehensive error handling"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON', 'success': False}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided', 'success': False}), 400
        
        if 'query' not in data:
            return jsonify({'error': 'Missing query parameter', 'success': False}), 400
        
        query = data['query']
        results = data.get('results', [])
        
        if not isinstance(results, list):
            return jsonify({'error': 'Results must be a list', 'success': False}), 400
        
        print(f"[OVERVIEW API] Processing query: {query} with {len(results)} results", file=sys.stderr)
        
        # Get worker instance
        worker = get_worker()
        if worker is None:
            return jsonify({'error': 'Worker not initialized', 'success': False}), 500
        
        # Generate overview with timeout protection
        try:
            overview_html = worker.generate_overview(query, results)
        except Exception as e:
            print(f"[OVERVIEW API] ❌ Worker error: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return jsonify({
                'error': f'Error generating overview: {str(e)}',
                'success': False
            }), 500
        
        if overview_html:
            print(f"[OVERVIEW API] ✅ Overview generated successfully ({len(overview_html)} chars)", file=sys.stderr)
            return jsonify({
                'success': True,
                'overview': overview_html,
                'query': query
            })
        else:
            print(f"[OVERVIEW API] ⚠️  No overview generated for: {query}", file=sys.stderr)
            return jsonify({
                'success': False,
                'error': 'No overview could be generated',
                'query': query
            })
            
    except Exception as e:
        # Catch-all error handler
        print(f"[OVERVIEW API] ❌ Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'success': False
        }), 500
