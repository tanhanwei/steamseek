#!/usr/bin/env python
"""
steam_game_search.py

A simple command-line Steam game search assistant that:
- Reads game summaries from a JSONL file ("my_games_with_summaries.jsonl")
- Generates text embeddings using SentenceTransformer (all-MiniLM-L6-v2)
- Stores the embeddings in a local Chroma vector database
- Provides a command-line interface to search for games by semantic similarity
"""

import os
import json

# Optional: Set HF_HOME so that Hugging Face caches models in a local folder.
os.environ["HF_HOME"] = os.path.abspath("./my_cache")

# Attempt to import torch_directml for AMD GPU acceleration on Windows.
try:
    import torch_directml
    device = torch_directml.device()
    print("Using AMD GPU via DirectML!")
except ImportError:
    device = "cpu"
    print("torch_directml not available, using CPU.")

print("Device being used:", device)

from sentence_transformers import SentenceTransformer

# Load the model directly by its identifier.
# (This will download the model in the expected format and cache it.)
model_name = "all-MiniLM-L6-v2"
print(f"Loading SentenceTransformer model: {model_name} ...")
model = SentenceTransformer(model_name, device=device)
print("Model loaded successfully.")

# Read game summaries from the JSONL file.
games_file = "my_games_with_summaries.jsonl"
game_ids = []        # unique identifier for each game (using the game name)
game_summaries = []  # the summary text of each game
game_metadata = []   # additional metadata (e.g. name, release_date)

print(f"Loading game summaries from {games_file}...")
with open(games_file, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        # Use "name" if available; if not, use "appid" or a generated ID.
        game_title = data.get("name") or data.get("appid") or f"game_{len(game_ids)}"
        summary = data["summary"]
        game_ids.append(str(game_title))
        game_summaries.append(summary)
        game_metadata.append({
            "name": game_title,
            "release_date": data.get("release_date", "Unknown")
        })
print(f"Loaded {len(game_summaries)} game summaries.")

# Generate embeddings for all game summaries.
print("Generating embeddings for game summaries...")
embeddings = model.encode(game_summaries, batch_size=32, show_progress_bar=True)
print(f"Generated {len(embeddings)} embedding vectors (each of dimension {len(embeddings[0])}).")

# Initialize Chroma (an in-memory vector database).
import chromadb
client = chromadb.Client()

# Create a collection for our game embeddings.
collection_name = "game_embeddings"
try:
    client.delete_collection(collection_name)
except Exception:
    pass  # Ignore if collection doesn't exist.

collection = client.create_collection(name=collection_name)
print(f"Created Chroma collection: {collection_name}")

# Add all game embeddings to the collection.
collection.add(
    ids=game_ids,
    documents=game_summaries,
    metadatas=game_metadata,
    embeddings=embeddings.tolist()  # Convert to list of lists if needed.
)
print("Added game embeddings to the collection.")

# --- Command-line Search Interface ---
print("\n=== Steam Game Search Assistant ===")
print("Enter your search query (or type 'quit' to exit).")
while True:
    user_query = input("Search games: ").strip()
    if user_query.lower() in {"quit", "exit", ""}:
        print("Exiting search.")
        break

    # Generate an embedding for the user's query.
    query_embedding = model.encode([user_query])
    
    # Query the Chroma collection for the top 5 most similar games.
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=5,
        include=["metadatas", "documents", "distances"]
    )
    
    # Extract and display the results.
    top_ids = results.get("ids", [])[0]
    top_metadatas = results.get("metadatas", [])[0]
    top_documents = results.get("documents", [])[0]
    top_distances = results.get("distances", [])[0]

    print("\nTop results:")
    for idx, (game_id, meta, doc, dist) in enumerate(zip(top_ids, top_metadatas, top_documents, top_distances), start=1):
        # Here, lower cosine distance means higher similarity.
        similarity = 1 - dist
        name = meta.get("name", game_id)
        release_date = meta.get("release_date", "Unknown")
        snippet = doc[:100].strip() + "..." if len(doc) > 100 else doc
        print(f"{idx}. {name} (Release: {release_date}) - Similarity: {similarity:.2f}")
        print(f"   Summary: {snippet}")
    print("-" * 40)
