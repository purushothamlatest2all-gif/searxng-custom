"""
AI Overview Backend for SearXNG
Uses symspell for spell correction + sumy with LexRank/LSA for summarization
"""
import re
from urllib.parse import unquote

# Import symspell for spell correction
try:
    from symspellpy import SymSpell, Verbosity
    SYMSPELL_AVAILABLE = True
except ImportError:
    SYMSPELL_AVAILABLE = False
    print("Warning: symspellpy not available")

# Import sumy for summarization
try:
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.lex_rank import LexRankSummarizer
    from sumy.summarizers.lsa import LsaSummarizer
    from sumy.nlp.stemmers import Stemmer
    from sumy.utils import get_stop_words
    SUMY_AVAILABLE = True
except ImportError:
    SUMY_AVAILABLE = False
    print("Warning: sumy not available")

# Initialize spell checker
spell_checker = None
if SYMSPELL_AVAILABLE:
    try:
        spell_checker = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        dictionary_path = "/usr/local/searxng/searxng/searx/data/frequency_dictionary_en_82_765.txt"
        if not spell_checker.load_dictionary(dictionary_path, term_index=0, count_index=1):
            print(f"Warning: Could not load spell dictionary from {dictionary_path}")
            spell_checker = None
    except Exception as e:
        print(f"Warning: Spell checker initialization failed: {e}")
        spell_checker = None

# Initialize summarizer
summarizer = None
LANGUAGE = 'english'
if SUMY_AVAILABLE:
    try:
        stemmer = Stemmer(LANGUAGE)
        summarizer = LexRankSummarizer(stemmer)
        summarizer.stop_words = get_stop_words(LANGUAGE)
    except Exception as e:
        print(f"Warning: Summarizer initialization failed: {e}")
        summarizer = None

def correct_spelling(query):
    """Correct spelling using symspell"""
    if not spell_checker:
        return query
    
    try:
        suggestions = spell_checker.lookup_compound(query, max_edit_distance=2)
        if suggestions and len(suggestions) > 0:
            return suggestions[0].term
    except Exception as e:
        print(f"Spelling correction error: {e}")
    
    return query

def summarize_text(text, sentences_count=3):
    """Summarize text using sumy LexRank"""
    if not summarizer or not text:
        return None
    
    try:
        parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))
        summary = summarizer(parser.document, sentences_count)
        
        # Convert summary to string
        summary_text = ' '.join([str(sentence) for sentence in summary])
        return summary_text
    except Exception as e:
        print(f"Summarization error: {e}")
        return None

def generate_overview(query, search_results=None):
    """Generate AI overview for a query"""
    if not query:
        return None
    
    # Correct spelling
    corrected_query = correct_spelling(query)
    if corrected_query != query:
        print(f"Query corrected: '{query}' -> '{corrected_query}'")
    
    # If we have search results, summarize them
    if search_results and len(search_results) > 0:
        # Combine content from top results
        combined_text = ''
        sources = []
        
        for i, result in enumerate(search_results[:5]):
            content = result.get('content', '') or result.get('snippet', '')
            title = result.get('title', '')
            url = result.get('url', '')
            
            if content:
                combined_text += f"{title}. {content} "
                if url:
                    sources.append({
                        'title': title,
                        'url': url
                    })
        
        if combined_text:
            # Summarize using LexRank
            summary = summarize_text(combined_text, sentences_count=3)
            
            if summary:
                return {
                    'overview': summary,
                    'source': 'AI Summary (LexRank)',
                    'url': sources[0]['url'] if sources else '',
                    'type': 'extractive',
                    'sources': sources[:3],  # Limit to top 3 sources
                    'corrected_query': corrected_query if corrected_query != query else None
                }
    
    # No overview available
    return None

# Test the function when run directly
if __name__ == '__main__':
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else 'python programming'
    print(f"Testing query: {query}")
    
    # Mock search results for testing
    mock_results = [
        {
            'title': 'Python Programming',
            'content': 'Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms.',
            'url': 'https://python.org'
        },
        {
            'title': 'Learn Python',
            'content': 'Python was created by Guido van Rossum and first released in 1991. It emphasizes code readability with its notable use of significant indentation.',
            'url': 'https://learnpython.org'
        }
    ]
    
    result = generate_overview(query, mock_results)
    if result:
        print(f"✅ Overview generated!")
        print(f"Overview: {result['overview']}")
        print(f"Source: {result['source']}")
        if result.get('corrected_query'):
            print(f"Corrected query: {result['corrected_query']}")
    else:
        print(f"❌ No overview available for: {query}")
