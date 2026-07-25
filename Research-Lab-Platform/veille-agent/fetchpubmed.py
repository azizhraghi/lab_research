from Bio import Entrez                             # Entrez is NCBI/PubMed's API client
from database import Paper, get_engine, init_db    # our database models
from embedder import get_embedding, get_topic, get_summary    # our Mistral functions
from sqlalchemy.orm import Session                 # database session
import math                                        # for cosine similarity
import time                                        # for rate limiting

# required by PubMed — they want to know who is making requests
Entrez.email = "garmayosr@gmail.com"    

def cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    return dot_product / (magnitude1 * magnitude2)

def is_duplicate(new_embedding, session, threshold=0.92):
    # checks new paper against all stored embeddings
    existing_papers = session.query(Paper).filter(Paper.embedding != None).all()
    for paper in existing_papers:
        if cosine_similarity(new_embedding, paper.embedding) > threshold:
            return True
    return False

def fetch_pubmed(query, max_results=3):
    print(f"  Searching PubMed for: {query}")

    # step 1: search PubMed and get a list of matching paper IDs
    search_handle = Entrez.esearch(
        db="pubmed",               # the PubMed database
        term=query,                # our search query
        retmax=max_results         # maximum number of results to return
    )
    search_results = Entrez.read(search_handle)    # parses the response
    search_handle.close()                          # always close handles after reading

    ids = search_results["IdList"]    # list of PubMed IDs matching our query
    if not ids:
        print("  No results found.")
        return []

    # step 2: fetch the actual paper details using those IDs
    fetch_handle = Entrez.efetch(
        db="pubmed",               # same database
        id=",".join(ids),          # comma-separated list of IDs to fetch
        rettype="abstract",        # we want the abstract format
        retmode="xml"              # XML format so we can parse it
    )
    records = Entrez.read(fetch_handle)    # parses the XML response
    fetch_handle.close()

    papers = []
    # loops over each paper in the response
    for record in records["PubmedArticle"]:
        try:
            # navigates the nested XML structure to get each field
            article = record["MedlineCitation"]["Article"]

            pubmed_id = str(record["MedlineCitation"]["PMID"])    # unique PubMed ID
            title     = str(article["ArticleTitle"])               # paper title

            # abstract might be missing for some papers — handle that gracefully
            if "Abstract" not in article:
                print(f"  Skipped (no abstract): {title[:60]}")
                continue

            abstract = str(article["Abstract"]["AbstractText"][0])    # first abstract paragraph

            # authors might be missing too — use empty list as fallback
            authors = []
            if "AuthorList" in article:
                for author in article["AuthorList"]:
                    # each author has LastName and ForeName fields
                    name = f"{author.get('ForeName', '')} {author.get('LastName', '')}".strip()
                    authors.append(name)

            print(f"  Processing: {title[:60]}...")

            time.sleep(1)    # pause before embedding to respect Mistral rate limits
            embedding = get_embedding(f"{title}. {abstract}")    # generates vector
            topic     = get_topic(title, abstract)               # classifies topic
            plain_summary = get_summary(title, abstract)         # generates plain summary

            paper = Paper(
                id            = f"pubmed:{pubmed_id}",    # prefix with "pubmed:" to avoid ID clashes with arXiv
                title         = title,
                authors       = ", ".join(authors),
                summary       = abstract,
                embedding     = embedding,
                topic         = topic,
                plain_summary = plain_summary
            )
            papers.append(paper)

        except Exception as e:
            # if one paper fails, log it and continue with the rest
            print(f"  Error processing paper: {e}")
            continue

    return papers

# --- main pipeline ---
if __name__ == "__main__":
    engine = get_engine()
    init_db(engine)

    from config import TOPICS    # reuses the same topic list as arXiv

    for topic in TOPICS:
        print(f"\n🔍 PubMed — topic: {topic}")
        results = fetch_pubmed(topic, max_results=3)

        with Session(engine) as session:
            for paper in results:
                # checks by ID first
                existing = session.get(Paper, paper.id)
                if existing:
                    print(f"  Skipped (same ID): {paper.title[:60]}")
                    continue

                # checks by meaning
                if is_duplicate(paper.embedding, session):
                    print(f"  Skipped (too similar): {paper.title[:60]}")
                    continue

                session.add(paper)
                print(f"  Saved: {paper.title[:60]}")

            session.commit()

    print("\n✅ Done! PubMed papers processed.")