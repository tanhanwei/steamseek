import os
import json
import time
import sys
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("Error: OPENAI_API_KEY not found in .env file.")
    sys.exit(1)

# Configuration
INPUT_FILE = "data/summaries.jsonl"     # Adjust path as needed
OUTPUT_FILE = "embeddings.jsonl"
CHECKPOINT_FILE = "checkpoint.txt"
EMBEDDING_MODEL = "text-embedding-3-large"
SLEEP_SECONDS = 0.1

def load_checkpoint():
    """Load the last processed index from the checkpoint file."""
    try:
        with open(CHECKPOINT_FILE, "r") as f:
            idx = int(f.read().strip())
            print(f"[Checkpoint] Resuming from entry index {idx}.")
            return idx
    except FileNotFoundError:
        print("[Checkpoint] No checkpoint found. Starting from the beginning.")
        return 0
    except Exception as e:
        print(f"[Checkpoint] Error reading checkpoint file: {e}")
        return 0

def save_checkpoint(idx):
    """Save the current index to the checkpoint file."""
    try:
        with open(CHECKPOINT_FILE, "w") as f:
            f.write(str(idx))
    except Exception as e:
        print(f"[Checkpoint] Error saving checkpoint: {e}")

def load_input_data():
    """Load game data from the input JSON Lines file."""
    data = []
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    data.append(entry)
        print(f"[Data] Loaded {len(data)} entries from {INPUT_FILE}.")
        return data
    except Exception as e:
        print(f"[Data] Error loading input file: {e}")
        sys.exit(1)

def process_entry(entry):
    text = entry.get("ai_summary", "")
    if not text:
        print(f"[Process] Skipping entry {entry.get('appid')} (no ai_summary found).")
        return None

    try:
        response = openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[text]
        )
        # Use dot notation to get the embedding
        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        print(f"[Process] Error processing entry {entry.get('appid')}: {e}")
        return None


def main():
    data = load_input_data()
    total_entries = len(data)
    start_idx = load_checkpoint()

    # Open the output file in append mode
    with open(OUTPUT_FILE, "a", encoding="utf-8") as out_file:
        try:
            for idx in range(start_idx, total_entries):
                entry = data[idx]
                appid = entry.get("appid", "Unknown")
                print(f"[{idx+1}/{total_entries}] Processing game ID {appid}...")

                embedding = process_entry(entry)
                if embedding is not None:
                    output_record = {
                        "appid": appid,
                        "name": entry.get("name", ""),
                        "ai_summary": entry.get("ai_summary", "No summary available"),
                        "embedding": embedding
                    }

                    out_file.write(json.dumps(output_record) + "\n")
                    out_file.flush()
                    print(f"[{idx+1}] Saved embedding for game ID {appid}.")
                else:
                    print(f"[{idx+1}] Failed to process game ID {appid}.")

                # Save progress after each entry
                save_checkpoint(idx + 1)
                time.sleep(SLEEP_SECONDS)

        except KeyboardInterrupt:
            print("\n[Interrupt] Process interrupted by user. Saving progress and exiting...")
            save_checkpoint(idx)  # Save current progress before exiting
            sys.exit(0)

if __name__ == "__main__":
    main()
