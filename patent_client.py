import logging
import time
import urllib.request
import urllib.parse
import json
from typing import List, Dict, Any

logger = logging.getLogger("IdeationGOAT.PatentClient")

class PatentClient:
    """
    Client for querying the PatentsView (USPTO) API to retrieve patent documents.
    Includes timeout, exponential backoff retries, and error handling.
    """
    def __init__(self, timeout: int = 8):
        self.timeout = timeout

    def search(self, query_term: str, max_results: int = 5, retries: int = 2) -> List[Dict[str, Any]]:
        """
        Queries the USPTO PatentsView search endpoint with retries and exponential backoff.
        """
        # Format query to PatentsView DSL
        # Search for query words in patent_title or patent_abstract
        query_dsl = {
            "_or": [
                {"_text_any": {"patent_title": query_term}},
                {"_text_any": {"patent_abstract": query_term}}
            ]
        }
        query_str = json.dumps(query_dsl)
        fields = ["patent_number", "patent_title", "patent_abstract", "patent_date"]
        fields_str = json.dumps(fields)
        
        params = urllib.parse.urlencode({
            "q": query_str,
            "f": fields_str,
            "o": json.dumps({"limit": max_results})
        })
        
        url = f"https://api.patentsview.org/patents/query?{params}"
        
        for attempt in range(retries + 1):
            try:
                logger.info(f"Querying USPTO PatentsView API (Attempt {attempt+1}/{retries+1}): {query_term}")
                req = urllib.request.Request(url, headers={'User-Agent': 'IdeationGOAT/1.2.0'})
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode('utf-8'))
                
                patents = []
                for item in data.get('patents', []) or []:
                    if not item:
                        continue
                    num = item.get('patent_number', 'Unknown')
                    title = item.get('patent_title', 'Unknown Title')
                    abstract = item.get('patent_abstract') or 'No abstract available.'
                    date = item.get('patent_date', 'Unknown')
                    
                    patents.append({
                        "source": "US Patent Office",
                        "patent_number": num,
                        "title": title,
                        "url": f"https://patents.google.com/patent/US{num}/en",
                        "summary": abstract,
                        "date": date
                    })
                return patents
            except Exception as e:
                logger.warning(f"PatentsView request failed on attempt {attempt+1}: {str(e)}")
                if attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                else:
                    logger.error(f"All PatentsView API queries failed for term: {query_term}")
                    return []
        return []
