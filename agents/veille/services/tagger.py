import json
from shared.llm_client import llm_client

async def tag_article(title: str, abstract: str) -> list[dict]:
    """Tag an article with relevant themes and confidence scores."""
    prompt = f"""
    Analyze the following scientific article and extract 1-3 key research themes or tags.
    Output JSON in this exact format:
    {{"tags": [{{"tag": "AI", "confidence": 0.95}}]}}
    
    Title: {title}
    Abstract: {abstract}
    """
    
    try:
        response_text = await llm_client.chat(
            messages=[{"role": "user", "content": prompt}]
        )
        # Often LLMs wrap JSON in markdown blocks like ```json ... ```
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        data = json.loads(response_text)
        return data.get("tags", [])
    except Exception as e:
        raise RuntimeError(f"Article tagging failed: {e}") from e
