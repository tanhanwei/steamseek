import requests
import json
import time
import argparse
import os
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

########################################
# CONFIGURATION: MODE & API SETTINGS
########################################
# MODE can be "local" or "api"
MODE = os.getenv("MODE", "local").lower()

if MODE == "api":
    API_URL = os.getenv("OPENROUTER_API_URL")  # e.g., "https://openrouter.ai/api/v1/chat/completions"
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
else:
    API_URL = "http://127.0.0.1:1234/v1/completions"

# Global cost tracker (used in API mode)
total_cost = 0.0
num_requests = 0

########################################
# PROMPT & CALL FUNCTIONS
########################################
def create_prompt(record):
    """
    Build a prompt for summarizing the game record.
    Uses the game's description and (if available) its reviews.
    Instructs the model to return ONLY a final summary (max 100 words)
    focusing on gameplay mechanics, unique features, and overall tone.
    """
    description = record.get("detailed_description") or record.get("short_description", "")
    reviews = record.get("reviews", [])
    # Use up to 3 reviews (if available) for context.
    review_texts = []
    if isinstance(reviews, list):
        review_texts = [r.get("review", "") for r in reviews[:100]]
    review_block = "\n".join(review_texts)
    
    prompt = (
        "Based on the following Steam game information, provide a single, concise summary in no more than 500 words "
        "that focuses solely on the gameplay mechanics, game pace, unique features, theme, genre, and overall tone. For example, is it a funny game? Has it got crafting mechanics? "
        "Also, try to figure out if there are any use of unique, hilarious or unusual weapons."
        "Return only the final summary as plain text with no headings, bullet points, or internal chain-of-thought details.\n\n"
        "Game Description:\n"
        f"{description}\n\n"
        f"{'User Reviews (sample):\n' + review_block + '\n\n' if review_block else 'none'}"
        "Final Summary:"
    )
    return prompt

def call_lm_studio(prompt, max_tokens=8000, temperature=0.7, top_p=0.9, timeout=180):
    """
    Sends the prompt to the selected API.
    
    - In local mode (LM Studio), uses the payload with "prompt".
    - In API mode (OpenRouter), uses the chat completions payload with a "messages" array.
    
    Returns the generated text from the first choice.
    Also tracks cost if available.
    
    Added debug prints to show the raw response for troubleshooting.
    """
    global total_cost, num_requests
    headers = {}
    
    if MODE == "api":
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        headers["Authorization"] = f"Bearer {OPENROUTER_API_KEY}"
        current_api_url = API_URL  # e.g., "https://openrouter.ai/api/v1/chat/completions"
    else:
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        current_api_url = API_URL

    try:
        response = requests.post(current_api_url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        num_requests += 1
        # Debug: print part of the raw response
        print(f"Raw response: {json.dumps(data)[:500]}")  # prints first 500 characters
        
        if MODE == "api" and "usage" in data and "cost" in data["usage"]:
            cost = data["usage"]["cost"]
            total_cost += cost
            print(f"Cost for this request: {cost} (Total: {total_cost})")
        if MODE == "api":
            choices = data.get("choices", [])
            if choices and isinstance(choices, list):
                result = choices[0].get("message", {}).get("content", "").strip()
                print(f"Generated summary (API mode): {result}")
                return result
        else:
            choices = data.get("choices", [])
            if choices and isinstance(choices, list):
                result = choices[0].get("text", "").strip()
                print(f"Generated summary (Local mode): {result}")
                return result
        return ""
    except Exception as e:
        print(f"Error calling LM Studio API: {e}")
        return ""

########################################
# CHECKPOINTING & SANITIZATION FUNCTIONS
########################################
def load_processed_appids(checkpoint_file):
    """
    Load already processed app IDs from the checkpoint file.
    Returns a set of app IDs as strings.
    """
    processed_ids = set()
    if os.path.exists(checkpoint_file):
        print(f"Loading already processed app IDs from {checkpoint_file}...")
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            for line in f:
                processed_ids.add(line.strip())
    return processed_ids

def append_checkpoint(appid, checkpoint_file):
    """
    Append an appid to the checkpoint file.
    """
    try:
        with open(checkpoint_file, "a", encoding="utf-8") as f:
            f.write(str(appid) + "\n")
            f.flush()
    except Exception as e:
        print(f"Error writing appid {appid} to checkpoint: {e}")

def sanitize_text(text):
    """
    Replace unusual line terminators or other control characters in a string.
    """
    if not isinstance(text, str):
        return text
    return text.replace('\u2028', ' ').replace('\u2029', ' ')

def sanitize_data(obj):
    """
    Recursively sanitize all strings in a nested data structure.
    """
    if isinstance(obj, str):
        return sanitize_text(obj)
    elif isinstance(obj, list):
        return [sanitize_data(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: sanitize_data(value) for key, value in obj.items()}
    else:
        return obj

def save_minimal_record(record, output_file):
    """
    Save a minimal record with only key metadata and the summary.
    """
    minimal = {
        "appid": record.get("appid"),
        "name": record.get("name"),
        "release_date": record.get("release_date"),
        "summary": record.get("summary")
    }
    try:
        minimal = sanitize_data(minimal)
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(minimal, ensure_ascii=False) + "\n")
            f.flush()
    except Exception as e:
        print(f"Error saving minimal record for appid {record.get('appid')}: {e}")

########################################
# MAIN SUMMARIZATION LOGIC
########################################
def main(input_file, limit=None, sleep_time=1, output_file="my_games_with_summaries.jsonl", checkpoint_file="summaries_checkpoint.txt"):
    with open(input_file, "r", encoding="utf-8") as fin:
        lines = fin.readlines()
    total_count = len(lines)
    processed_ids = load_processed_appids(checkpoint_file)
    print(f"Total records in input: {total_count}")
    print(f"Already processed records: {len(processed_ids)}")

    new_summaries = 0
    for line in tqdm(lines, desc="Summarizing Records"):
        try:
            record = json.loads(line)
        except Exception as e:
            print(f"Skipping a line due to JSON error: {e}")
            continue

        appid = str(record.get("appid", ""))
        if not appid:
            continue
        if appid in processed_ids:
            continue

        # If summary is missing or empty, generate one.
        if "summary" not in record or not record["summary"]:
            prompt = create_prompt(record)
            print(f"\nPrompt for appid {appid} - {record.get('name')}:\n{prompt}\n")
            summary = call_lm_studio(prompt)
            if not summary:
                print(f"Warning: received empty summary for appid {appid}. Retrying with increased max_tokens...")
                summary = call_lm_studio(prompt, max_tokens=8000)
            record["summary"] = summary
            new_summaries += 1
        else:
            print(f"Appid {appid} already has a summary; skipping generation.")

        save_minimal_record(record, output_file)
        append_checkpoint(appid, checkpoint_file)
        processed_ids.add(appid)
        time.sleep(sleep_time)

    print(f"Finished processing records. New summaries generated: {new_summaries}.")
    if MODE == "api":
        print(f"Total cost incurred in API mode: ${total_cost:.4f} over {num_requests} requests.")
    print(f"Minimal summarized data saved to {output_file}")
    print(f"Checkpoint file updated: {checkpoint_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Incremental Summarization from Crawled Data with Minimal Output")
    parser.add_argument("--input", type=str, default="steam_games_data.jsonl", help="Input JSONL file with crawled game data")
    parser.add_argument("--limit", type=int, help="Limit the number of records to process", default=None)
    parser.add_argument("--sleep", type=float, help="Delay (in seconds) between summarization requests", default=1)
    parser.add_argument("--output", type=str, help="Output JSONL file path for minimal summarized data", default="my_games_with_summaries.jsonl")
    parser.add_argument("--checkpoint", type=str, help="Checkpoint file path", default="summaries_checkpoint.txt")
    args = parser.parse_args()
    main(input_file=args.input, limit=args.limit, sleep_time=args.sleep, output_file=args.output, checkpoint_file=args.checkpoint)
