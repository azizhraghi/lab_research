from typing import List, Dict, Any
import asyncio

async def fetch_scholar_works(scholar_id: str) -> List[Dict[str, Any]]:
    """
    Fetch works (publications) for a given Google Scholar ID using the scholarly library.
    Note: scholarly is synchronous and blocks, so we run it in a threadpool.
    """
    def _fetch():
        try:
            from scholarly import scholarly
            
            # NOTE: In production, you would configure proxies here to avoid IP bans.
            # scholarly.use_proxy(...)
            
            author = scholarly.search_author_id(scholar_id)
            author = scholarly.fill(author, sections=['publications'])
            
            works = []
            # We don't fetch full details for all publications immediately due to rate limits/time
            for pub in author.get('publications', []):
                bib = pub.get('bib', {})
                
                # Try to extract year safely
                year = None
                pub_year_raw = bib.get('pub_year')
                if pub_year_raw:
                    try:
                        year = int(pub_year_raw)
                    except ValueError:
                        pass
                
                works.append({
                    "title": bib.get('title', 'Unknown Title'),
                    "year": year,
                    "type": "article", 
                    "journal": bib.get('journal') or bib.get('citation', ''),
                    "doi": bib.get('doi'),
                    "citation_count": pub.get('num_citations', 0),
                    "source": "scholar"
                })
            return works
        except Exception as e:
            print(f"Error fetching from Scholar for {scholar_id}: {e}")
            return []

    # scholarly is completely synchronous and blocking
    return await asyncio.to_thread(_fetch)
