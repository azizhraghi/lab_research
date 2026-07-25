import requests                                    # lets us make HTTP calls to arXiv
import xml.etree.ElementTree as ET                 # parses the XML response from arXiv
from database import Paper, get_engine, init_db    # imports our database models and setup functions
from embedder import get_embedding, get_topic, get_summary    # imports all three Mistral functions
from sqlalchemy.orm import Session                 # lets us open a session to read/write the database
import math                                        # gives us math functions — needed for cosine similarity

def cosine_similarity(vec1, vec2):
    # multiplies each pair of numbers and adds them up (dot product)
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # calcule de la norme des vecteurs
    norme1 = math.sqrt(sum(a * a for a in vec1))
    norme2 = math.sqrt(sum(b * b for b in vec2))
    
    # divides dot product by both lengths — result is between 0 and 1
    # 1 means identical meaning, 0 means completely unrelated
    return dot_product / (norme1 * norme2)

def is_duplicate(new_embedding, session, threshold=0.92):
    # loads all papers that already have an embedding stored
    existing_papers = session.query(Paper).filter(Paper.embedding != None).all()
    
    for paper in existing_papers:
        # compares the new paper's vector against each stored vector
        similarity = cosine_similarity(new_embedding, paper.embedding)
        
        if similarity > threshold:    # if more than 92% similar, it's a duplicate
            return True               # stop checking and say "yes this is a duplicate"
    
    return False                      # checked everything — not a duplicate

def fetch_papers(query, max_results=5):
    url = "https://export.arxiv.org/api/query"    # arXiv API endpoint
    params = {
        "search_query": f'ti:"{query}"',           # search by title for exact phrase
        "start": 0,                                # start from the first result
        "max_results": max_results                 # how many papers to fetch
    }

    response = requests.get(url, params=params)    # sends the request to arXiv

    if response.status_code != 200:                # anything other than 200 means something went wrong
        print("Error:", response.status_code)
        return []

    root = ET.fromstring(response.text)            # parses the XML string into a tree we can navigate
    namespace = {"atom": "http://www.w3.org/2005/Atom"}    # arXiv uses this namespace prefix

    papers = []
    for entry in root.findall("atom:entry", namespace):    # loops over each paper in the response
        arxiv_id = entry.find("atom:id", namespace).text.strip()        # unique arXiv ID
        title    = entry.find("atom:title", namespace).text.strip()     # paper title
        summary  = entry.find("atom:summary", namespace).text.strip()   # abstract
        authors  = [a.find("atom:name", namespace).text
                    for a in entry.findall("atom:author", namespace)]   # list of author names

        print(f"Processing: {title[:60]}...")

        # combines title and summary for a richer embedding
        text_to_embed = f"{title}. {summary}"
        embedding = get_embedding(text_to_embed)    # converts text to a vector using Mistral

        topic = get_topic(title, summary)           # classifies the paper into a topic
        print(f"  Topic: {topic}")

        plain_summary = get_summary(title, summary)         # generates plain-language summary
        print(f"  Summary: {plain_summary[:80]}...")        # prints first 80 chars so we can see it working

        paper = Paper(
            id        = arxiv_id,
            title     = title,
            authors   = ", ".join(authors),         # joins list of authors into one string
            summary   = summary,
            embedding = embedding,                  # stores the vector
            topic     = topic,                       # stores the topic tag
            plain_summary = plain_summary           # plain-language summary for non-specialists
        )
        papers.append(paper)

    return papers

# --- main pipeline ---
if __name__ == "__main__":
    engine = get_engine()       # creates/connects to papers.db
    init_db(engine)             # creates tables if they don't exist yet

    # imports the topic list from config instead of hardcoding one query
    from config import TOPICS

    # loops over every topic and fetches papers for each one
    for topic in TOPICS:
        print(f"\n🔍 Fetching papers for topic: {topic}")
        results = fetch_papers(topic, max_results=3)    # 3 papers per topic to stay within rate limits

        with Session(engine) as session:
            for paper in results:
                existing = session.get(Paper, paper.id)
                if existing:
                    print(f"  Skipped (same ID): {paper.title[:60]}")
                    continue

                if is_duplicate(paper.embedding, session):
                    print(f"  Skipped (too similar): {paper.title[:60]}")
                    continue

                session.add(paper)
                print(f"  Saved: {paper.title[:60]}")

            session.commit()    # saves all new papers for this topic

    print("\n✅ Done! All topics processed.")