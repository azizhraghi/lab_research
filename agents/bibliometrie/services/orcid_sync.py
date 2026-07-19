import httpx
from typing import List, Dict, Any

ORCID_API_BASE = "https://pub.orcid.org/v3.0"

async def fetch_orcid_works(orcid_id: str) -> List[Dict[str, Any]]:
    """
    Fetch works (publications) for a given ORCID ID.
    Using the public API which does not require authentication for public data.
    """
    url = f"{ORCID_API_BASE}/{orcid_id}/works"
    headers = {"Accept": "application/json"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch ORCID data for {orcid_id}: {response.status_code}")
            return []
            
        data = response.json()
        works = []
        
        # Parse the ORCID XML-to-JSON structure
        group = data.get("group", [])
        for item in group:
            work_summary = item.get("work-summary", [])
            if not work_summary:
                continue
                
            # Usually take the first summary for the work
            summary = work_summary[0]
            
            title_info = summary.get("title", {}) or {}
            title = title_info.get("title", {}).get("value", "Unknown Title")
            
            pub_date = summary.get("publication-date", {}) or {}
            year = pub_date.get("year", {}).get("value")
            
            type_name = summary.get("type", "unknown")
            journal_info = summary.get("journal-title", {})
            journal = journal_info.get("value") if isinstance(journal_info, dict) else None
            
            # Find DOI
            doi = None
            ext_ids = summary.get("external-ids", {}).get("external-id", [])
            for ext in ext_ids:
                if ext.get("external-id-type") == "doi":
                    doi = ext.get("external-id-value")
                    break
            
            works.append({
                "title": title,
                "year": int(year) if year else None,
                "type": type_name,
                "journal": journal,
                "doi": doi,
                "source": "orcid"
            })
            
        return works
