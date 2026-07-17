import logging
import time
import urllib.request
import urllib.parse
import json
from typing import List, Dict, Any

logger = logging.getLogger("IdeationGOAT.ScholarClient")

class ScholarClient:
    """
    Client for querying the Semantic Scholar API to retrieve academic research papers.
    Includes timeout, exponential backoff retries, and error handling.
    """
    def __init__(self, timeout: int = 8):
        self.timeout = timeout

    def search(self, query_term: str, max_results: int = 5, retries: int = 2) -> List[Dict[str, Any]]:
        """
        Queries the Semantic Scholar search endpoint with retries and exponential backoff.
        """
        formatted_query = urllib.parse.quote(query_term)
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={formatted_query}&limit={max_results}&fields=title,abstract,url,citationCount"
        
        for attempt in range(retries + 1):
            try:
                logger.info(f"Querying Semantic Scholar API (Attempt {attempt+1}/{retries+1}): {query_term}")
                req = urllib.request.Request(url, headers={'User-Agent': 'IdeationGOAT/1.2.0'})
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode('utf-8'))
                
                papers = []
                for item in data.get('data', []):
                    title = item.get('title', 'Unknown Title')
                    abstract = item.get('abstract') or 'No abstract available.'
                    url_link = item.get('url') or f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}"
                    citations = item.get('citationCount', 0)
                    
                    papers.append({
                        "source": "Semantic Scholar",
                        "title": title,
                        "url": url_link,
                        "summary": abstract,
                        "citations": citations
                    })
                return papers
            except Exception as e:
                logger.warning(f"Semantic Scholar request failed on attempt {attempt+1}: {str(e)}")
                if attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                else:
                    logger.error(f"All Semantic Scholar API queries failed for term: {query_term}")
                    return []
        return []
