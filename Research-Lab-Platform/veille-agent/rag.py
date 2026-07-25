import os                                          # reads environment variables
from dotenv import load_dotenv                     # loads your .env file
from mistralai.client import Mistral                    # Mistral client
from database import Paper, get_engine             # database models
from sqlalchemy.orm import Session                 # database session
import math                                        # for cosine similarity

load_dotenv()                                      # loads your API key from .env

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))    # creates Mistral client

def cosine_similarity(vec1, vec2):
    # measures how similar two vectors are — 1 means identical meaning, 0 means unrelated
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    return dot_product / (magnitude1 * magnitude2)

def retrieve_relevant_papers(question, top_k=3):
    # step 1: convert the question into a vector using the same model we used for papers
    response = client.embeddings.create(
        model="mistral-embed",                     # must use the same model as when we stored papers
        inputs=[question]                          # embeds the question
    )
    question_embedding = response.data[0].embedding    # extracts the question vector

    # step 2: load all papers that have embeddings stored
    with Session(get_engine()) as session:
        papers = session.query(Paper).filter(Paper.embedding != None).all()

        # step 3: score each paper by similarity to the question
        scored = []
        for paper in papers:
            score = cosine_similarity(question_embedding, paper.embedding)    # compares vectors
            scored.append((score, paper.title, paper.plain_summary, paper.topic, paper.authors))

        # step 4: sort by score descending — most relevant first
        scored.sort(key=lambda x: x[0], reverse=True)

        # step 5: return only the top_k most relevant papers
        return scored[:top_k]

def answer_question(question):
    print(f"\n🔍 Searching for relevant papers...")
    relevant = retrieve_relevant_papers(question, top_k=3)    # finds top 3 papers

    if not relevant:
        print("No relevant papers found in the database.")
        return

    # builds a context block from the retrieved papers
    context = ""
    for i, (score, title, summary, topic, authors) in enumerate(relevant, 1):
        context += f"""
Paper {i} (relevance: {score:.2f}):
Title: {title}
Authors: {authors}
Topic: {topic}
Summary: {summary}
---"""

    # builds the prompt — this is the core of RAG
    # we give Mistral the question AND the retrieved papers
    prompt = f"""You are a scientific assistant for an agricultural research laboratory.
Answer the researcher's question using ONLY the papers provided below.
For each point you make, cite which paper it comes from (e.g. "According to Paper 1...").
If the papers don't contain enough information to answer, say so clearly.

Retrieved papers:
{context}

Researcher's question: {question}

Provide a clear, concise answer with citations."""

    print(f"📚 Found {len(relevant)} relevant papers. Generating answer...\n")

    # sends the question + context to mistral-large for grounded answer generation
    response = client.chat.complete(
        model="mistral-large-latest",              # powerful model for nuanced answers
        messages=[
            {"role": "user", "content": prompt}    # our full prompt with context
        ]
    )

    answer = response.choices[0].message.content.strip()    # extracts the answer text

    # prints the sources used
    print("📄 Sources used:")
    for i, (score, title, summary, topic, authors) in enumerate(relevant, 1):
        print(f"  [{i}] {title[:70]} (score: {score:.2f})")

    print(f"\n💬 Answer:\n{answer}")

# --- simple interactive loop ---
# keeps asking for questions until the user types 'quit'
print("🌱 Veille Scientifique — RAG Search")
print("   Ask any question about the papers in your database.")
print("   Type 'quit' to exit.\n")

while True:
    question = input("Your question: ").strip()    # reads input from the terminal

    if question.lower() == "quit":                 # exits if user types quit
        print("Goodbye!")
        break

    if not question:                               # skips empty input
        continue

    answer_question(question)                      # runs the full RAG pipeline
    print("\n" + "="*60 + "\n")                   # separator between questions