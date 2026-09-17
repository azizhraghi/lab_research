"""PubMed fetcher for the veille (scientific watch) agent.

PubMed is the NIH/NLM database for biomedical and life-sciences literature —
relevant to LRSTE for water-quality, public-health and eco-toxicology angles.
The API is two-step:
  1. esearch.fcgi  → returns a list of PMIDs for a query
  2. efetch.fcgi → returns metadata and available abstracts for those PMIDs

Both are XML over HTTP, no API key required (a key raises the rate limit but the
NCBI E-utilities have a public tier of 3 req/s without one).

Output shape matches the RSS scraper / ArXiv fetcher so VeilleAgent.run_collection
can treat every source type identically.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List

import httpx
import xml.etree.ElementTree as ET

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


_MONTHS = {m.lower(): i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def _parse_pubmed_date(raw: str | None) -> datetime.datetime | None:
    """Parse a PubMed PubDate string, e.g. "2025 Mar 6", "2025 Mar", "2025 Apr-May", "2026".

    PubMed returns these as free-form strings in the esummary <Item Name="PubDate">.
    Month abbreviations or month ranges are accepted; day is optional. Season-only
    or season-range strings (e.g. "2025 Winter") fall back to January 1st of the year.
    """
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
    parts = raw.split()
    try:
        year = int(parts[0])
    except (ValueError, IndexError):
        return None
    # Month: second token if it's a word, else default to January.
    month = 1
    if len(parts) >= 2:
        token = parts[1].lower()
        # Handle ranges like "apr-may" by taking the first month.
        token = token.split("-")[0].split("–")[0]
        month = int(token) if token.isdigit() else _MONTHS.get(token[:3], 1)
    # Day: third token if present and numeric.
    day = 1
    if len(parts) >= 3:
        try:
            day = int(parts[2])
        except ValueError:
            day = 1
    try:
        return datetime.datetime(year, month, day)
    except ValueError:
        return None


async def _esearch(term: str, max_results: int) -> List[str]:
    params = {
        "db": "pubmed",
        "term": term,
        "retmax": max_results,
        "sort": "pub_date",
        "retmode": "xml",
    }
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            resp = await client.get(ESEARCH_URL, params=params, timeout=30.0)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
        except Exception as e:
            raise RuntimeError(f"PubMed search failed: {e}") from e
    if root.findall(".//ERROR"):
        raise RuntimeError("PubMed search returned an error response.")
    return [id_el.text.strip() for id_el in root.findall(".//Id") if id_el.text]


async def _esummary(pmids: List[str]) -> Dict[str, Dict[str, Any]]:
    if not pmids:
        return {}
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            resp = await client.get(ESUMMARY_URL, params=params, timeout=30.0)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
        except Exception as e:
            raise RuntimeError(f"PubMed summary retrieval failed: {e}") from e

    out: Dict[str, Dict[str, Any]] = {}
    for doc in root.findall(".//DocSum"):
        pmid_el = doc.find("Id")
        if pmid_el is None or not pmid_el.text:
            continue
        pmid = pmid_el.text.strip()
        title = None
        authors: List[str] = []
        pubdate_raw = None
        doi = None
        for item in doc.findall("Item"):
            name = item.attrib.get("Name", "")
            if name == "Title" and item.text:
                title = item.text.strip()
            elif name == "AuthorList":
                # Nested list of <Item Name="Author">...</Item> children.
                for child in item.findall("Item"):
                    if child.attrib.get("Name") == "Author" and child.text:
                        authors.append(child.text.strip())
            elif name == "PubDate" and item.text:
                pubdate_raw = item.text.strip()
            elif name == "ArticleIds":
                for child in item.findall("Item"):
                    if child.attrib.get("Name") == "doi" and child.text:
                        doi = child.text.strip()
            elif name == "DOI" and item.text and not doi:
                # Top-level DOI Item is present on some records; prefer ArticleIds.
                doi = item.text.strip()
        out[pmid] = {
            "title": title or "No Title",
            "authors": authors,
            "pubdate_raw": pubdate_raw,
            "doi": doi,
        }
    return out


def parse_pubmed_records(xml: str) -> List[Dict[str, Any]]:
    """Preserve structured abstract labels and inline scientific text."""
    root = ET.fromstring(xml)
    errors = root.findall(".//ERROR")
    if errors:
        raise RuntimeError("PubMed returned an error: " + "; ".join("".join(e.itertext()) for e in errors))
    items = []
    for record in root.findall(".//PubmedArticle"):
        pmid = record.findtext("./MedlineCitation/PMID")
        article = record.find("./MedlineCitation/Article")
        if not pmid or article is None:
            continue
        title = "".join(article.find("ArticleTitle").itertext()).strip() if article.find("ArticleTitle") is not None else ""
        if not title:
            continue
        abstracts = []
        for section in article.findall("./Abstract/AbstractText"):
            text = "".join(section.itertext()).strip()
            label = section.get("Label") or section.get("NlmCategory")
            if text:
                abstracts.append(f"{label}: {text}" if label and label != "UNASSIGNED" else text)
        authors = []
        for author in article.findall("./AuthorList/Author"):
            name = author.findtext("CollectiveName") or " ".join(filter(None, [author.findtext("ForeName"), author.findtext("LastName")]))
            if name: authors.append(name)
        doi = next((node.text for node in record.findall("./PubmedData/ArticleIdList/ArticleId") if node.get("IdType") == "doi"), None)
        pubdate = article.find("./Journal/JournalIssue/PubDate")
        date_text = None
        if pubdate is not None:
            date_text = pubdate.findtext("MedlineDate") or " ".join(filter(None, [pubdate.findtext("Year"),pubdate.findtext("Month"),pubdate.findtext("Day")]))
        items.append(dict(title=title, url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", abstract="\n".join(abstracts) or None,
                          authors=authors, doi=doi, published_at=_parse_pubmed_date(date_text), source_type="pubmed"))
    return items


async def fetch_pubmed(term: str, max_results: int = 25) -> List[Dict[str, Any]]:
    """Search then retrieve PubMed XML including abstracts, when publicly available."""
    pmids = await _esearch(term, max_results)
    if not pmids:
        return []
    import asyncio
    await asyncio.sleep(0.35)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            response = await client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                params={"db":"pubmed", "id":",".join(pmids), "retmode":"xml", "tool":"LRSTEWatch"})
            response.raise_for_status()
        return parse_pubmed_records(response.text)
    except Exception as exc:
        raise RuntimeError(f"PubMed abstract retrieval failed ({type(exc).__name__}): {exc}") from exc
