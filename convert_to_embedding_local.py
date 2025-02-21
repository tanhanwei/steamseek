import os
import json
import re
import numpy as np
import logging
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def split_into_sentences(text):
    """Splits text into sentences using a simple regex."""
    return re.split(r'(?<=[.!?]) +', text)

def chunk_text(text, tokenizer, max_tokens=512):
    """
    Splits text into chunks so that each chunk's token count is below max_tokens.
    Uses sentence boundaries and the tokenizer to manage chunk sizes.
    """
    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        temp_chunk = f"{current_chunk} {sentence}".strip() if current_chunk else sentence
        tokens = tokenizer.encode(temp_chunk, add_special_tokens=False)
        
        if len(tokens) > max_tokens:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                # If a single sentence is too long, truncate it.
                tokens = tokenizer.encode(sentence, add_special_tokens=False)
                truncated_tokens = tokens[:max_tokens]
                truncated_sentence = tokenizer.decode(truncated_tokens)
                chunks.append(truncated_sentence.strip())
                current_chunk = ""
        else:
            current_chunk = temp_chunk

    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def compute_embedding(text, model, tokenizer, max_tokens=512):
    """
    Computes an embedding for the given text.
    If the text exceeds max_tokens, it is split into chunks and their embeddings are averaged.
    """
    tokens = tokenizer.encode(text, add_special_tokens=False)
    token_count = len(tokens)
    
    if token_count <= max_tokens:
        return model.encode(text)
    else:
        chunks = chunk_text(text, tokenizer, max_tokens)
        logger.info(f"Text exceeds {max_tokens} tokens (actual: {token_count}). Splitting into {len(chunks)} chunk(s).")
        embeddings = [model.encode(chunk) for chunk in chunks]
        return np.mean(embeddings, axis=0)

def main():
    # Use a model known to work well (all-MiniLM-L6-v2)
    model_id = "all-MiniLM-L6-v2"
    logger.info(f"Loading model: {model_id}")
    model = SentenceTransformer(model_id)  # Let SentenceTransformer handle the download and caching.
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    input_file = "summaries.jsonl"
    output_file = "summaries_with_embeddings.jsonl"
    
    logger.info(f"Starting processing of file: {input_file}")
    count = 0
    with open(input_file, "r", encoding="utf-8") as fin, \
         open(output_file, "w", encoding="utf-8") as fout:
        for line in tqdm(fin, desc="Processing summaries"):
            data = json.loads(line)
            ai_summary = data.get("ai_summary", "")
            
            if ai_summary:
                tokens = tokenizer.encode(ai_summary, add_special_tokens=False)
                token_count = len(tokens)
                if token_count > 512:
                    logger.info(f"AppID {data.get('appid')} summary token count: {token_count} > 512. Will be chunked.")
                else:
                    logger.debug(f"AppID {data.get('appid')} summary token count: {token_count}")
                    
                emb = compute_embedding(ai_summary, model, tokenizer, max_tokens=512)
                data["embedding"] = emb.tolist()
            else:
                logger.warning(f"AppID {data.get('appid')} has no ai_summary field.")
            
            fout.write(json.dumps(data) + "\n")
            count += 1
            if count % 100 == 0:
                logger.info(f"Processed {count} summaries.")
    
    logger.info(f"Finished processing {count} summaries. Output saved to {output_file}")

if __name__ == "__main__":
    main()
