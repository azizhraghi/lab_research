import os
from datetime import datetime

# Simple HTML template for the CV
CV_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>CV - {name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            color: #333;
            line-height: 1.6;
            margin: 20px;
        }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
        h2 {{ color: #2980b9; margin-top: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .contact-info {{ font-size: 0.9em; color: #7f8c8d; }}
        .publication {{ margin-bottom: 10px; }}
        .pub-title {{ font-weight: bold; }}
        .indicators {{ display: flex; justify-content: space-around; background: #ecf0f1; padding: 15px; border-radius: 5px; }}
        .indicator-box {{ text-align: center; }}
        .indicator-value {{ font-size: 1.5em; font-weight: bold; color: #2c3e50; }}
        .indicator-label {{ font-size: 0.8em; color: #7f8c8d; text-transform: uppercase; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{name}</h1>
        <div class="contact-info">
            {role} • {department}<br>
            {email}
        </div>
    </div>
    
    <h2>Bibliometric Indicators</h2>
    <div class="indicators">
        {indicators_html}
    </div>
    
    <h2>Selected Publications</h2>
    {publications_html}
</body>
</html>
"""

async def generate_cv_pdf(researcher_data: dict, output_path: str) -> str:
    """Generate a PDF CV for a researcher using WeasyPrint (if available)."""
    
    # Format indicators
    indicators_html = ""
    for ind in researcher_data.get("indicators", []):
        indicators_html += f"""
        <div class="indicator-box">
            <div class="indicator-value">{ind['value']}</div>
            <div class="indicator-label">{ind['metric_name']}</div>
        </div>
        """
        
    # Format publications
    pubs = researcher_data.get("publications", [])
    pubs.sort(key=lambda x: (x.get("year") or 0), reverse=True)
    
    publications_html = ""
    for pub in pubs[:20]: # Limit to top 20 for CV
        year_str = f"({pub['year']})" if pub.get('year') else ""
        journal_str = f" - <i>{pub['journal']}</i>" if pub.get('journal') else ""
        citations_str = f" [Citations: {pub['citation_count']}]" if pub.get('citation_count', 0) > 0 else ""
        
        publications_html += f"""
        <div class="publication">
            <span class="pub-title">{pub['title']}</span> {year_str}{journal_str}{citations_str}
        </div>
        """
        
    if not publications_html:
        publications_html = "<p>No publications found.</p>"
        
    # Render HTML
    html_content = CV_TEMPLATE.format(
        name=researcher_data.get("name", "Unknown"),
        role=researcher_data.get("role", "Researcher"),
        department=researcher_data.get("department", "Unknown Department"),
        email=researcher_data.get("email", ""),
        indicators_html=indicators_html,
        publications_html=publications_html
    )
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Try generating PDF
    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(output_path)
    except (ImportError, OSError) as e:
        print(f"Warning: WeasyPrint dependencies missing on this OS. Falling back to HTML. Error: {e}")
        output_path = output_path.replace(".pdf", ".html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
    return output_path
