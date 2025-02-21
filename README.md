# Enhanced Steam Game Data Processing System

This system processes Steam game data by filtering reviews for quality and generating comprehensive game summaries using AI. It handles various types of non-review content (like spam and troll reviews) and adapts its processing for both popular and niche games.

## Features

- Robust review filtering system that handles:
  - Troll reviews and spam
  - ASCII art and copypasta
  - Recipe posts and off-topic content
  - Low-quality or repetitive content
- Adaptive scoring for both popular and niche games
- AI-powered game summarization using OpenRouter
- Checkpoint system to track progress
- Detailed error handling and logging

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your OpenRouter credentials:
```env
MODE=api
OPENROUTER_API_URL=your_api_url
OPENROUTER_API_KEY=your_api_key
OPENROUTER_MODEL=your_chosen_model
```

4. Create the data directory:
```bash
mkdir data
```

## Usage

1. Ensure your Steam game data is in JSONL format in `data/steam_games_data.jsonl`

2. Run the processing script:
```bash
python main.py
```

The script will:
- Filter reviews for quality
- Generate summaries using AI
- Save processed data to `data/game_summaries.jsonl`
- Track progress in `data/processed_ids.txt`

## File Structure

- `config.py`: Configuration settings and constants
- `review_filtering.py`: Review quality assessment and filtering
- `summarization.py`: AI-powered game summarization
- `main.py`: Main processing script

## Output

The system generates a JSONL file where each line contains:
- Original game data
- Filtered high-quality reviews
- AI-generated game summary

## Error Handling

The system includes comprehensive error handling for:
- API failures
- Malformed input data
- Network issues
- Invalid content

Failed games are logged but don't stop the overall processing.

## Maintenance

To clear progress and start fresh:
```bash
rm data/processed_ids.txt
rm data/game_summaries.jsonl
```

## Notes

- The system uses OpenRouter for AI summarization. Ensure you have sufficient API credits.
- Processing speed is limited by API rate limits and includes intentional delays.
- Large datasets may take significant time to process.
- Consider running a small test batch first by limiting the input file size.