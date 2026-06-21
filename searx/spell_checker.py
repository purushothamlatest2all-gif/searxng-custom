import os, sys, threading
from typing import Dict, List

_spelling_instance = None
_custom_freq = {}
_lock = threading.Lock()
DICT_PATH = "os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spell_models", "")frequency_dictionary_en_82_765.txt"
CUSTOM_PATH = "os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spell_models", "")custom_freq.txt"

def get_checker():
    global _spelling_instance, _custom_freq
    if _spelling_instance is None:
        with _lock:
            if _spelling_instance is None:
                try:
                    from symspellpy import SymSpell, Verbosity
                    sym = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
                    sym.load_dictionary(DICT_PATH, term_index=0, count_index=1, separator=" ")
                    if os.path.exists(CUSTOM_PATH):
                        with open(CUSTOM_PATH) as f:
                            for line in f:
                                parts = line.strip().split()
                                if len(parts) == 2:
                                    _custom_freq[parts[0].lower()] = int(parts[1])
                    _spelling_instance = sym
                except Exception:
                    return None
    return _spelling_instance

def correct_word(word):
    checker = get_checker()
    if not checker: return word
    from symspellpy import Verbosity
    suggestions = checker.lookup(word, Verbosity.ALL, max_edit_distance=2)
    if not suggestions: return word
    best = suggestions[0]
    best_score = _custom_freq.get(best.term.lower(), best.count)
    for s in suggestions:
        score = _custom_freq.get(s.term.lower(), s.count)
        if score > best_score:
            best_score = score
            best = s
    return best.term

def fix_query(query):
    if not query or len(query.strip()) < 5:
        return {"original": query, "corrected": query, "has_corrections": False, "confidence": "none", "suggestions": []}
    checker = get_checker()
    if not checker:
        return {"original": query, "corrected": query, "has_corrections": False, "confidence": "none", "suggestions": [], "error": "unavailable"}
    try:
        words = query.split()
        corrected_words = []
        corrections = {}
        for word in words:
            corrected = correct_word(word)
            corrected_words.append(corrected)
            if corrected.lower() != word.lower():
                corrections[word.lower()] = corrected.lower()
        corrected = " ".join(corrected_words)
        if corrected.lower() == query.lower():
            return {"original": query, "corrected": query, "has_corrections": False, "confidence": "none", "suggestions": []}
        changes = len(corrections)
        conf = "high" if changes <= 2 else "medium" if changes <= 4 else "low"
        return {"original": query, "corrected": corrected, "corrections": corrections, "has_corrections": True, "confidence": conf, "suggestions": [corrected]}
    except Exception as e:
        return {"original": query, "corrected": query, "has_corrections": False, "confidence": "none", "suggestions": [], "error": str(e)}

def get_suggestions(query, max_suggestions=5):
    result = fix_query(query)
    return result.get("suggestions", [])
