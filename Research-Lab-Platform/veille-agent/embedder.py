import os                          # lets us read environment variables (like your API key)
from dotenv import load_dotenv     # reads your .env file and loads the variables into the environment
from mistralai.client import Mistral  # the Mistral client we'll use to call the API
from mistralai.client.errors import SDKError  # error type thrown on API failures
import json                        # lets us convert Python lists to JSON for storage
import time                        # lets us pause execution for a set number of seconds

load_dotenv()                      # actually loads the .env file — must run before os.getenv()

# creates the Mistral client using your API key from .env
client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

def retry_on_rate_limit(func, max_retries=5, initial_wait=2):
    """Decorator: retries the function with exponential backoff on 429 rate-limit errors."""
    def wrapper(*args, **kwargs):
        wait = initial_wait
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except SDKError as e:
                if "429" in str(e) or "rate_limited" in str(e).lower():
                    print(f"  ⏳ Rate limited — waiting {wait}s before retry ({attempt + 1}/{max_retries})...")
                    time.sleep(wait)
                    wait *= 2          # exponential backoff: 2 → 4 → 8 → 16 → 32s
                else:
                    raise              # re-raise non-rate-limit errors immediately
        # if all retries exhausted, make one last attempt (will raise if it fails)
        return func(*args, **kwargs)
    return wrapper

@retry_on_rate_limit
def get_embedding(text):
    time.sleep(1)    
    # calls Mistral's embedding API with your text
    response = client.embeddings.create(
        model="mistral-embed",     # the model that converts text to vectors
        inputs=[text]              # list of texts to embed — we send one at a time
    )
    return response.data[0].embedding  # returns the vector (list of 1024 numbers)

@retry_on_rate_limit
def get_topic(title, summary):
    time.sleep(1)    
    # builds the prompt we send to Mistral for classification
    prompt = f"""Given this scientific paper, assign it ONE topic from this list:
[hydrology, agronomy, irrigation, water quality, climate, AI/ML, hydraulics, other]

Title: {title}
Abstract: {summary[:300]}

Reply with just the topic word, nothing else."""

    # calls mistral-small to classify the paper (cheaper model, simple task)
    response = client.chat.complete(
        model="mistral-small",         # smaller/cheaper model — enough for classification
        messages=[
            {"role": "user", "content": prompt}   # sends our prompt as a user message
        ]
    )
    # extracts the text reply and removes any extra spaces
    return response.choices[0].message.content.strip().lower()

@retry_on_rate_limit
def get_summary(title, abstract):
    time.sleep(2)    # waits 2 seconds before calling the API to avoid rate limiting
    # builds a prompt asking Mistral to simplify the abstract
    prompt = f"""You are a scientific assistant for an agricultural research laboratory.

A researcher just found this paper. Write a 3-sentence plain-language summary 
that a non-specialist can understand. Focus on: what the paper does, 
why it matters, and how it relates to agriculture, water, or environmental research.

Title: {title}
Abstract: {abstract}

Write only the 3-sentence summary, nothing else."""

    # calls mistral-large — more powerful model, better at nuanced writing
    response = client.chat.complete(
        model="mistral-large-latest",      # larger model for higher quality summaries
        messages=[
            {"role": "user", "content": prompt}    # sends our prompt as a user message
        ]
    )

    # extracts and returns the summary text
    return response.choices[0].message.content.strip()