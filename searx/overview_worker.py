"""
AI Overview Worker - Enhanced with Fallback Content
"""
import sys
import re
import hashlib
import traceback
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import redis

class OverviewWorker:
    def __init__(self):
        self._initialized = False
        self._lex_rank = None
        self._lsa = None
        self._text_rank = None
        self._tokenizer = None
        self._parser_class = None
        self._redis = None
        
        self.CACHE_TTL = 3600
        self.MAX_URLS_TO_FETCH = 3
        self.URL_TIMEOUT = 3  # Increased from 2
        self.API_TIMEOUT = 1.5  # Increased from 1.5
        self.MAX_WORKERS = 5
        self.MIN_CONTENT_LENGTH = 30  # Reduced from 50
        
        self.INTENT_PATTERNS = {
            'news': [r'\bnews\b', r'\blatest\b', r'\bupdate[s]?\b', r'\bbreaking\b',
                    r'\bcurrent\b', r'\btoday\b', r'\byesterday\b', r'\bthis week\b',
                    r'\bwar\b', r'\bconflict\b', r'\bcrisis\b', r'\belection\b',
                    r'\battack\b', r'\bincident\b', r'\bevent[s]?\b',
                    r'\bwhat happened\b', r'\bwhat is happening\b', r'\brecent\b'],
            'action': [r'\border\b', r'\bbuy\b', r'\bpurchase\b', r'\bdownload\s+free\b',
                      r'\border\s+now\b', r'\bbook\s+(flight|hotel|ticket)\b',
                      r'\bregister\s+now\b', r'\bsign\s+up\b', r'\bsubscribe\b'],
            'local': [r'\bnear\s+me\b', r'\bnearby\b', r'\baround\s+me\b',
                     r'\bin\s+my\s+area\b', r'\bclose\s+to\s+me\b',
                     r'\bweather\b', r'\btemperature\b', r'\btraffic\b'],
            'comparison': [r'\bvs\.?\b', r'\bversus\b', r'\bcompare\b', r'\bcomparison\b',
                          r'\bdifference\s+between\b', r'\bbetter\s+than\b',
                          r'\bworse\s+than\b', r'\bpros\s+and\s+cons\b'],
            'recommendation': [r'\bbest\b', r'\btop\s+\d+\b', r'\btop\s+\w+\b',
                              r'\brecommended\b', r'\brecommend\b', r'\bsuggest\b',
                              r'\bshould\s+i\s+use\b', r'\bmost\s+popular\b'],
            'informational': [r'\bwhat\s+is\b', r'\bwho\s+(is|invented|created)\b',
                             r'\bwhen\s+(was|did|is)\b', r'\bwhere\s+is\b',
                             r'\bwhy\s+(is|do|does|are)\b', r'\bhow\s+(does|do|is|to)\b',
                             r'\bdefine\b', r'\bdefinition\b', r'\bexplain\b']
        }
        
        self.SAFETY_BLACKLIST = [
            r'\bfree\s+(movie|music|software|game|ebook|book)s?\s+download\b',
            r'\bdownload\s+(movie|music|software|game|ebook|book)s?\s+free\b',
            r'\btorrent\b.*\b(site|website|download)\b',
            r'\bpirate\s+(bay|site)\b', r'\bcracked\s+software\b',
            r'\bkeygen\b', r'\bserial\s+key\b',
            r'\bhow\s+to\s+hack\b', r'\bhack\s+(facebook|instagram|gmail|account|wifi)\b',
            r'\bcrack\s+password\b', r'\bsteal\s+(data|password|credit)\b',
            r'\bhow\s+to\s+(make|build|create)\s+bomb\b',
            r'\bhow\s+to\s+(kill|murder)\b',
            r'\bdrugs?\s+(buy|purchase|order)\b',
            r'\bweapons?\s+(buy|purchase)\b',
            r'\bcounterfeit\b', r'\bfake\s+(id|passport|license)\b'
        ]
        
        self.TRUSTED_DOMAINS = [
            'wikipedia.org', 'wikibooks.org', 'wiktionary.org', 'britannica.com',
            'python.org', 'cprogramming.com', 'geeksforgeeks.org', 'tutorialspoint.com',
            'w3schools.com', 'programiz.com', 'stackoverflow.com', 'stackexchange.com',
            'github.com', 'gitlab.com', 'freecodecamp.org', 'codecademy.com',
            'tomshardware.com', 'cnet.com', 'techradar.com', 'theverge.com', 'wired.com',
            'pcmag.com', 'zdnet.com', 'engadget.com', 'arstechnica.com',
            'medium.com', 'dev.to', 'docs.microsoft.com', 'docs.oracle.com',
            'coursera.org', 'edx.org', 'arxiv.org', 'ieee.org', 'acm.org',
            'bbc.com', 'bbc.co.uk', 'reuters.com', 'apnews.com', 'aljazeera.com',
            'cnn.com', 'nytimes.com', 'washingtonpost.com', 'theguardian.com',
            'ft.com', 'bloomberg.com', 'wsj.com', 'economist.com', 'time.com',
            'usatoday.com', 'nbcnews.com', 'cbsnews.com', 'abcnews.go.com',
            'npr.org', 'techcrunch.com', 'theregister.com',
            'timesofindia.com', 'hindustantimes.com', 'thehindu.com',
            'indianexpress.com', 'ndtv.com', 'indiatoday.in', 'firstpost.com',
            'forbes.com', 'businessinsider.com', 'inc.com', 'entrepreneur.com',
            'nature.com', 'science.org', 'sciencedaily.com', 'phys.org',
            'goodreads.com', 'amazon.com', 'reddit.com'
        ]
        
        self.TYPO_CORRECTIONS = {
            'pyton': 'python', 'pyhton': 'python', 'jva': 'java',
            'javasript': 'javascript', 'machne': 'machine', 'lerning': 'learning',
            'databse': 'database', 'algoritm': 'algorithm', 'programe': 'program',
            'programing': 'programming', 'softwere': 'software', 'hardwere': 'hardware',
            'inteligence': 'intelligence', 'artifical': 'artificial',
            'blockhain': 'blockchain', 'quantam': 'quantum'
        }

    def _ensure_initialized(self):
        if self._initialized:
            return
        try:
            import nltk
            from sumy.parsers.plaintext import PlaintextParser
            from sumy.nlp.tokenizers import Tokenizer
            from sumy.summarizers.lex_rank import LexRankSummarizer
            from sumy.summarizers.lsa import LsaSummarizer
            from sumy.summarizers.text_rank import TextRankSummarizer
            from sumy.nlp.stemmers import Stemmer
            from sumy.utils import get_stop_words
            
            nltk.data.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'nltk_data'))
            
            stemmer = Stemmer("english")
            stop_words = get_stop_words("english")
            
            self._lex_rank = LexRankSummarizer(stemmer)
            self._lex_rank.stop_words = stop_words
            self._lsa = LsaSummarizer(stemmer)
            self._lsa.stop_words = stop_words
            self._text_rank = TextRankSummarizer(stemmer)
            self._text_rank.stop_words = stop_words
            self._tokenizer = Tokenizer("english")
            self._parser_class = PlaintextParser
            
            try:
                self._redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                self._redis.ping()
                print("[OVERVIEW WORKER] ✅ Redis cache connected", file=sys.stderr)
            except Exception as e:
                print(f"[OVERVIEW WORKER] ⚠️  Redis unavailable: {e}", file=sys.stderr)
                self._redis = None
            
            self._initialized = True
            print("[OVERVIEW WORKER] ✅ Initialized", file=sys.stderr)
        except Exception as e:
            print(f"[OVERVIEW WORKER] ❌ Init failed: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

    def _get_cache_key(self, query):
        return f"overview:{hashlib.md5(query.lower().encode()).hexdigest()}"

    def _get_cached_overview(self, query):
        if not self._redis:
            return None
        try:
            cache_key = self._get_cache_key(query)
            cached = self._redis.get(cache_key)
            if cached:
                print(f"[OVERVIEW WORKER] ✅ Cache hit for: {query}", file=sys.stderr)
                return cached
        except Exception as e:
            print(f"[OVERVIEW WORKER] Cache error: {e}", file=sys.stderr)
        return None

    def _set_cached_overview(self, query, html):
        if not self._redis:
            return
        try:
            cache_key = self._get_cache_key(query)
            self._redis.setex(cache_key, self.CACHE_TTL, html)
            print(f"[OVERVIEW WORKER] ✅ Cached overview for: {query}", file=sys.stderr)
        except Exception as e:
            print(f"[OVERVIEW WORKER] Cache error: {e}", file=sys.stderr)

    def _ensemble_summarize(self, text, sentence_count=3):
        try:
            parser = self._parser_class.from_string(text, self._tokenizer)
            document = parser.document
            if not document.sentences:
                return []
            if len(document.sentences) <= sentence_count:
                return [str(s) for s in document.sentences]

            n_candidates = min(len(document.sentences), sentence_count * 2)
            try:
                lex_sents = self._lex_rank(document, n_candidates)
            except:
                lex_sents = []
            try:
                lsa_sents = self._lsa(document, n_candidates)
            except:
                lsa_sents = []
            try:
                tr_sents = self._text_rank(document, n_candidates)
            except:
                tr_sents = []
            
            sent_to_idx = {str(sent): idx for idx, sent in enumerate(document.sentences)}
            votes = {}
            for sent_list in [lex_sents, lsa_sents, tr_sents]:
                for sent in sent_list:
                    s_str = str(sent)
                    votes[s_str] = votes.get(s_str, 0) + 1
            
            candidates = list(votes.keys())
            candidates.sort(key=lambda s: sent_to_idx.get(s, 9999))
            candidates.sort(key=lambda s: votes[s], reverse=True)
            selected = candidates[:sentence_count]
            selected.sort(key=lambda s: sent_to_idx.get(s, 9999))
            return selected
        except Exception as e:
            print(f"[OVERVIEW WORKER] Ensemble error: {e}", file=sys.stderr)
            return []

    def _correct_typos(self, query):
        query_lower = query.lower()
        corrected = query_lower
        was_corrected = False
        for typo, correction in self.TYPO_CORRECTIONS.items():
            if typo in corrected:
                corrected = corrected.replace(typo, correction)
                was_corrected = True
        return corrected, was_corrected

    def _classify_intent(self, query):
        query_lower = query.lower()
        for pattern in self.SAFETY_BLACKLIST:
            if re.search(pattern, query_lower):
                return 'safety_violation'
        for pattern in self.INTENT_PATTERNS['news']:
            if re.search(pattern, query_lower):
                return 'news'
        for pattern in self.INTENT_PATTERNS['action']:
            if re.search(pattern, query_lower):
                return 'action'
        for pattern in self.INTENT_PATTERNS['local']:
            if re.search(pattern, query_lower):
                return 'local'
        for pattern in self.INTENT_PATTERNS['comparison']:
            if re.search(pattern, query_lower):
                return 'comparison'
        for pattern in self.INTENT_PATTERNS['recommendation']:
            if re.search(pattern, query_lower):
                return 'recommendation'
        for pattern in self.INTENT_PATTERNS['informational']:
            if re.search(pattern, query_lower):
                return 'informational'
        return 'informational'

    def _generate_decline_message(self, intent, query):
        messages = {
            'safety_violation': '<div class="overview-section"><h3 class="overview-heading">⚠️ Unable to Process This Query</h3><p class="overview-text">This query appears to involve activities that may be illegal or harmful.</p></div>',
            'action': f'<div class="overview-section"><h3 class="overview-heading">🛒 Action Required</h3><p class="overview-text">Your query "<strong>{query}</strong>" appears to be a request to perform an action.</p></div>',
            'local': f'<div class="overview-section"><h3 class="overview-heading">📍 Location-Based Query</h3><p class="overview-text">Your query "<strong>{query}</strong>" appears to be location-specific.</p></div>'
        }
        return messages.get(intent, '')

    def _is_trusted_domain(self, url):
        domain = urlparse(url).netloc.lower()
        for trusted in self.TRUSTED_DOMAINS:
            if trusted in domain:
                return True
        return False

    def _fetch_url_content(self, url, title, query):
        """Fetch content from URL with detailed logging"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        try:
            print(f"[OVERVIEW WORKER] 🌐 Fetching: {url[:60]}", file=sys.stderr)
            resp = requests.get(url, headers=headers, timeout=self.URL_TIMEOUT, allow_redirects=True)
            
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type or not content_type:
                    text = self._extract_clean_content(resp.text)
                    if len(text) >= self.MIN_CONTENT_LENGTH:
                        print(f"[OVERVIEW WORKER] ✅ Success: {len(text)} chars from {url[:50]}", file=sys.stderr)
                        return {'url': url, 'title': title, 'content': text[:1500]}
                    else:
                        print(f"[OVERVIEW WORKER] ⚠️  Content too short: {len(text)} chars from {url[:50]}", file=sys.stderr)
                else:
                    print(f"[OVERVIEW WORKER] ⚠️  Not HTML: {content_type} from {url[:50]}", file=sys.stderr)
            else:
                print(f"[OVERVIEW WORKER] ❌ HTTP {resp.status_code} from {url[:50]}", file=sys.stderr)
        except requests.exceptions.Timeout:
            print(f"[OVERVIEW WORKER] ⏱️  Timeout: {url[:50]}", file=sys.stderr)
        except requests.exceptions.ConnectionError:
            print(f"[OVERVIEW WORKER] 🔌 Connection error: {url[:50]}", file=sys.stderr)
        except Exception as e:
            print(f"[OVERVIEW WORKER] ❌ Error: {str(e)[:80]} from {url[:50]}", file=sys.stderr)
        
        return None

    def _fetch_wikipedia(self, query):
        api_data = {}
        headers = {'User-Agent': 'SearXNG-AI-Overview/1.0 (educational)'}
        try:
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(query)}"
            resp = requests.get(wiki_url, headers=headers, timeout=self.API_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('extract') and len(data['extract']) > 100:
                    api_data['wikipedia'] = data
        except:
            pass
        return api_data

    def _fetch_from_apis_parallel(self, query):
        api_data = {'duckduckgo': None}
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            futures.append(executor.submit(self._fetch_wikipedia, query))
            
            def fetch_ddg():
                headers = {'User-Agent': 'SearXNG-AI-Overview/1.0 (educational)'}
                try:
                    ddg_url = f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json&no_html=1"
                    resp = requests.get(ddg_url, headers=headers, timeout=self.API_TIMEOUT)
                    if resp.status_code in (200, 202):
                        return resp.json()
                except:
                    pass
                return None
            
            futures.append(executor.submit(fetch_ddg))
            results = [f.result() for f in futures]
            if results[0]:
                api_data.update(results[0])
            if results[1]:
                api_data['duckduckgo'] = results[1]
        return api_data

    def _extract_clean_content(self, html):
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return ""
        soup = BeautifulSoup(html, 'lxml')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'form', 'button', 'input', 'select', 'noscript']):
            tag.decompose()
        for element in soup.find_all(class_=re.compile(r'ad|banner|popup|cookie|social|share|comment|related|sidebar|menu|nav|footer|header|widget', re.I)):
            element.decompose()
        main_content = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile(r'^(content|article|post|entry|main)$', re.I)) or soup.find('body')
        if not main_content:
            return ""
        text = main_content.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        for pattern in [r'Share this:.*', r'Photo credit:.*', r'Copyright ©.*', r'All rights reserved', r'Advertisement.*']:
            text = re.sub(pattern, '', text, flags=re.I)
        return text.strip()

    def _process_results(self, results, query):
        """Process results with fallback to snippet content"""
        quality_texts = []
        
        print(f"[OVERVIEW WORKER] Processing {len(results)} results", file=sys.stderr)
        
        # First, try to fetch full content from URLs
        selected_results = []
        for result in results[:10]:
            url = result.get('url')
            if url:
                selected_results.append(result)
                if len(selected_results) >= self.MAX_URLS_TO_FETCH:
                    break
        
        # Fetch URLs in parallel
        if selected_results:
            with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
                futures = []
                for result in selected_results:
                    futures.append(executor.submit(
                        self._fetch_url_content,
                        result.get('url'),
                        result.get('title', ''),
                        query
                    ))
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        quality_texts.append(result)
        
        # FALLBACK: If no URLs worked, use snippet content from search results
        if len(quality_texts) == 0:
            print(f"[OVERVIEW WORKER] 🔄 Using fallback: snippet content from search results", file=sys.stderr)
            for result in results[:5]:
                title = result.get('title', '')
                content = result.get('content', '')
                url = result.get('url', '')
                
                if content and len(content) >= self.MIN_CONTENT_LENGTH:
                    print(f"[OVERVIEW WORKER] ✅ Using snippet: {title[:50]}", file=sys.stderr)
                    quality_texts.append({
                        'url': url,
                        'title': title,
                        'content': content
                    })
        
        print(f"[OVERVIEW WORKER] 📚 Total quality sources: {len(quality_texts)}", file=sys.stderr)
        return quality_texts

    def _structure_html(self, query, intent, api_data, full_texts):
        html_parts = []
        
        combined_text = " ".join([t['content'] for t in full_texts[:3]])
        intro_sentences = self._ensemble_summarize(combined_text, sentence_count=3)
        
        intro_parts = []
        if api_data.get('wikipedia') and api_data['wikipedia'].get('extract'):
            intro_parts.append(api_data['wikipedia']['extract'])
        elif api_data.get('duckduckgo') and api_data['duckduckgo'].get('Abstract'):
            intro_parts.append(api_data['duckduckgo']['Abstract'])
        
        if not intro_parts and full_texts:
            intro_parts.append(full_texts[0]['content'][:500])
        
        intro_parts.extend(intro_sentences)
        
        if intro_parts:
            html_parts.append('<div class="overview-section">')
            if intent == 'news':
                html_parts.append(f'<h3 class="overview-heading">📰 Latest News: {query.title()}</h3>')
            elif intent == 'informational':
                html_parts.append(f'<h3 class="overview-heading">What is {query.title()}?</h3>')
            elif intent == 'recommendation':
                html_parts.append(f'<h3 class="overview-heading">Top Recommendations</h3>')
            else:
                html_parts.append(f'<h3 class="overview-heading">About {query.title()}</h3>')
            html_parts.append(f'<p class="overview-text">{" ".join(intro_parts)}</p>')
            html_parts.append('</div>')
        
        if full_texts:
            html_parts.append('<div class="overview-section">')
            if intent == 'news':
                html_parts.append('<h3 class="overview-heading">📰 News Coverage</h3>')
            else:
                html_parts.append('<h3 class="overview-heading">Detailed Analysis</h3>')
            for text_data in full_texts[:3]:
                content = text_data['content']
                if len(content) > 50:
                    summary_sentences = self._ensemble_summarize(content, sentence_count=2)
                    summary_text = " ".join(summary_sentences)
                    if summary_text:
                        html_parts.append('<div class="overview-subsection">')
                        html_parts.append(f'<h4 class="overview-subheading">{text_data["title"]}</h4>')
                        html_parts.append(f'<p class="overview-text">{summary_text}</p>')
                        html_parts.append('</div>')
            html_parts.append('</div>')
        
        if full_texts:
            html_parts.append('<div class="overview-section">')
            html_parts.append('<h3 class="overview-heading">Sources</h3>')
            html_parts.append('<ol class="overview-sources">')
            for text_data in full_texts[:5]:
                html_parts.append(f'<li><a href="{text_data["url"]}" target="_blank">{text_data["title"]}</a></li>')
            html_parts.append('</ol>')
            html_parts.append('</div>')
        
        return '\n'.join(html_parts)

    def generate_overview(self, query, results):
        """Main entry point"""
        try:
            self._ensure_initialized()
            if not self._initialized:
                print("[OVERVIEW WORKER] ❌ Not initialized", file=sys.stderr)
                return None
            
            corrected_query, was_corrected = self._correct_typos(query)
            if was_corrected:
                print(f"[OVERVIEW WORKER] 🔧 Typo corrected", file=sys.stderr)
            
            intent = self._classify_intent(corrected_query)
            print(f"[OVERVIEW WORKER] 🎯 Intent: {intent}", file=sys.stderr)
            
            if intent in ['safety_violation', 'action', 'local']:
                return self._generate_decline_message(intent, query)
            
            cached = self._get_cached_overview(corrected_query)
            if cached:
                return cached
            
            if not results:
                print(f"[OVERVIEW WORKER] ⚠️  No results", file=sys.stderr)
                return None
            
            quality_texts = self._process_results(results, corrected_query)
            api_data = self._fetch_from_apis_parallel(corrected_query)
            
            has_wikipedia = api_data.get('wikipedia') is not None
            
            if not quality_texts and not has_wikipedia:
                print(f"[OVERVIEW WORKER] ⚠️  No quality content", file=sys.stderr)
                return None
            
            overview_html = self._structure_html(corrected_query, intent, api_data, quality_texts)
            self._set_cached_overview(corrected_query, overview_html)
            
            word_count = len(overview_html.split())
            print(f"[OVERVIEW WORKER] ✅ Generated {word_count} words", file=sys.stderr)
            
            return overview_html
            
        except Exception as e:
            print(f"[OVERVIEW WORKER] ❌ Error: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return None
