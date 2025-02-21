import json
import os
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import argparse

def load_summarized_data(input_file):
    """Reads the JSONL file and returns a list of records."""
    records = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
                records.append(record)
            except Exception as e:
                print(f"Error parsing line: {e}")
    return records

def compute_embeddings(records, 
                       model_name="sentence-transformers/all-MiniLM-L6-v2", 
                       cache_dir="./cache"):

    import os
    from sentence_transformers import SentenceTransformer

    # Make sure your cache folder exists
    cache_dir = os.path.abspath(cache_dir)
    os.makedirs(cache_dir, exist_ok=True)

    # Let SentenceTransformer handle the download
    print(f"Loading model '{model_name}' with cache folder '{cache_dir}'...")
    model = SentenceTransformer(model_name, cache_folder=cache_dir)

    texts, metadata = [], []
    for record in records:
        summary = record.get("summary", "").strip()
        if not summary:
            continue
        texts.append(summary)
        metadata.append({
            "appid": record.get("appid"),
            "name": record.get("name"),
            "release_date": record.get("release_date")
        })

    if texts:
        embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    else:
        embeddings = np.array([])

    return embeddings, metadata



def build_faiss_index(embeddings, index_file="faiss_index.index"):
    """
    Builds a FAISS index from the embeddings (assumed to be a NumPy array of shape (N, D)).
    Saves the index to disk.
    Returns the FAISS index.
    """
    if embeddings.size == 0:
        print("No embeddings to index.")
        return None
    d = embeddings.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(embeddings)
    faiss.write_index(index, index_file)
    print(f"FAISS index with {index.ntotal} vectors saved to {index_file}")
    return index

def save_metadata(metadata, metadata_file="metadata.json"):
    """Saves the metadata list to a JSON file."""
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"Metadata for {len(metadata)} records saved to {metadata_file}")

def main(input_file, model_name, index_file, metadata_file, cache_dir):
    print(f"Loading summarized data from {input_file}...")
    records = load_summarized_data(input_file)
    print(f"Loaded {len(records)} records.")

    print("Computing embeddings...")
    embeddings, metadata = compute_embeddings(records, model_name=model_name, cache_dir=cache_dir)
    if embeddings.size == 0:
        print("No embeddings computed. Exiting.")
        return

    print("Building FAISS index...")
    index = build_faiss_index(embeddings, index_file=index_file)
    
    print("Saving metadata...")
    save_metadata(metadata, metadata_file=metadata_file)
    print("Embedding generation and indexing complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate embeddings and build a FAISS index from summarized game data.")
    parser.add_argument("--input", type=str, default="my_games_with_summaries.jsonl", help="Input JSONL file with minimal summarized data")
    parser.add_argument("--model", type=str, default="all-MiniLM-L6-v2", help="SentenceTransformer model name")
    parser.add_argument("--index", type=str, default="faiss_index.index", help="Output file for FAISS index")
    parser.add_argument("--metadata", type=str, default="metadata.json", help="Output file for metadata")
    parser.add_argument("--cache_dir", type=str, default="./cache", help="Cache directory for the model")
    args = parser.parse_args()
    
    main(input_file=args.input, model_name=args.model, index_file=args.index, metadata_file=args.metadata, cache_dir=args.cache_dir)
