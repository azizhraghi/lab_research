from typing import List, Dict

def compute_h_index(citations: List[int]) -> int:
    """
    Compute the h-index from a list of citation counts.
    A scientist has index h if h of their N papers have at least h citations each.
    """
    citations.sort(reverse=True)
    h_index = 0
    for i, c in enumerate(citations):
        if c >= i + 1:
            h_index = i + 1
        else:
            break
    return h_index

def compute_i10_index(citations: List[int]) -> int:
    """
    Compute the i10-index (number of publications with at least 10 citations).
    """
    return sum(1 for c in citations if c >= 10)

def compute_total_citations(citations: List[int]) -> int:
    """Compute total citations."""
    return sum(citations)

def compute_all_indicators(citations: List[int]) -> Dict[str, float]:
    """Compute all standard bibliometric indicators."""
    if not citations:
        return {
            "h_index": 0.0,
            "i10_index": 0.0,
            "total_citations": 0.0
        }
        
    return {
        "h_index": float(compute_h_index(citations)),
        "i10_index": float(compute_i10_index(citations)),
        "total_citations": float(compute_total_citations(citations))
    }
