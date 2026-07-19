import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import datetime

async def fetch_rss_feed(url: str) -> List[Dict[str, Any]]:
    """Fetch and parse an RSS/Atom feed."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            items = []
            
            # Atom
            for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                title = entry.find("{http://www.w3.org/2005/Atom}title")
                link = entry.find("{http://www.w3.org/2005/Atom}link")
                summary = entry.find("{http://www.w3.org/2005/Atom}summary")
                
                items.append({
                    "title": title.text if title is not None else "No Title",
                    "url": link.attrib.get('href') if link is not None else None,
                    "abstract": summary.text if summary is not None else None,
                    "authors": [],
                    "published_at": datetime.datetime.utcnow(),
                    "doi": None
                })
                
            # RSS 2.0
            for item in root.findall(".//item"):
                title = item.find("title")
                link = item.find("link")
                desc = item.find("description")
                
                items.append({
                    "title": title.text if title is not None else "No Title",
                    "url": link.text if link is not None else None,
                    "abstract": desc.text if desc is not None else None,
                    "authors": [],
                    "published_at": datetime.datetime.utcnow(),
                    "doi": None
                })
                
            return items
        except Exception as e:
            print(f"Error fetching RSS {url}: {e}")
            return []
