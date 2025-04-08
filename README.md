# SteamSeek

SteamSeek is an AI-powered Steam game discovery platform that uses semantic search, deep search, and AI analysis to help users find games that truly match what they're looking for.

## Features

- **Semantic Search**: Find games based on what you're actually looking for, not just keyword matching
- **AI-Enhanced Search**: Optimize your queries automatically for better results
- **Deep Search**: Use multiple search variations to find hidden gems that standard search might miss
- **Game Analysis**: View detailed AI-generated analysis of games, including:
  - Community sentiment analysis
  - Standout features
  - Market positioning
  - Quality assessment
- **Personal Lists**: Create and manage game collections for different purposes
- **Game Notes**: Add personal markdown notes to any game
- **Responsive Design**: Works well on both desktop and mobile devices

## Tech Stack

- **Backend**: Python with Flask
- **Authentication**: Firebase Authentication (Google Sign-in)
- **Database**: Firebase Firestore (for user data, lists, notes)
- **AI**: OpenRouter API for LLM capabilities
- **Search**: Local vector embeddings for semantic search
- **Frontend**: Bootstrap 5, JavaScript, HTML/CSS

## Setup

### Prerequisites

- Python 3.8+
- Node.js (optional, for development)
- Firebase project with Firestore and Authentication configured
- OpenRouter API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/steamseek.git
cd steamseek
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with required credentials:
```env
# Flask
FLASK_SECRET_KEY=your_secure_random_key

# OpenRouter API 
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions

# Firebase
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=credentials/firebase-service-account.json
```

5. Place your Firebase service account JSON in `credentials/firebase-service-account.json`

6. Ensure your Steam game data is in JSONL format in `data/steam_games_data.jsonl`

7. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`.

## Project Structure

```
steamseek/
├── app.py                   # Main Flask application
├── data_loader.py           # Loads game data and builds indexes
├── firebase_config.py       # Firebase configuration and user models
├── llm_processor.py         # Handles all LLM interactions
├── game_chatbot.py          # Semantic search functionality
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not in repo)
├── .gitignore               # Git ignore file
├── data/                    # Data files
│   ├── steam_games_data.jsonl  # Main game data
│   ├── summaries.jsonl         # Pre-generated game summaries
│   └── analysis_cache.jsonl    # Cached game analyses
├── templates/               # HTML templates
│   ├── base_with_sidebar.html  # Base template with sidebar
│   ├── search.html             # Search page
│   ├── detail.html             # Game detail page
│   ├── lists.html              # User lists page
│   ├── list_detail.html        # Individual list page
│   └── login.html              # Login page
├── static/                  # Static assets
    ├── css/                 # CSS files
    ├── js/                  # JavaScript files
    └── img/                 # Image files
```

## Features In Detail

### Search System

SteamSeek offers three search modes:

1. **Standard Search**: Quick search with immediate results
2. **AI-Enhanced Search**: Optimizes your query with AI before searching
3. **Deep Search**: Generates variations of your query to find more relevant games

All search types support filtering by:
- Genre
- Release Year
- Platform
- Price
- Sorting options (Relevance, Name, Date, Price, Reviews)

### User Account Features

- **Game Lists**: Create and manage multiple game collections
- **Game Notes**: Add markdown notes to any game
- **Recently Viewed**: Track recently viewed games
- **OAuth Authentication**: Secure login with Google

### Game Analysis

The detail page for each game provides:
- AI Summary of the game
- Feature sentiment analysis (what players like/dislike)
- Standout features
- Community feedback analysis
- Market positioning
- Quality assessment
- Playtime distribution
- Review sentiment

## API Endpoints

The application provides several API endpoints:

### Search
- `/search` - Main search endpoint
- `/search_status` - Status updates for AI-Enhanced searches
- `/deep_search_status` - Status updates for Deep searches

### Lists
- `/api/game_lists/<appid>` - Get all user lists and whether they contain a game
- `/api/save_results_as_list` - Save search results as a new list
- `/create_list` - Create a new list
- `/save_game/<appid>` - Save a game to one or more lists
- `/remove_game/<list_id>/<appid>` - Remove a game from a list
- `/api/update_list/<list_id>` - Update list metadata

### Notes
- `/api/game_note/<appid>` (GET) - Get a game note
- `/api/game_note/<appid>` (POST) - Save a game note
- `/api/game_note/<appid>` (DELETE) - Delete a game note
- `/api/render_markdown` - Render markdown to HTML

## LLM Integration

The app uses OpenRouter API for several AI functions:

1. **Search Query Optimization**: Improves user queries for better results
2. **Search Result Reranking**: Reorders search results by relevance
3. **Deep Search Query Variations**: Generates variations of search queries
4. **Game Analysis Generation**: Creates detailed game analyses
5. **List Name Generation**: Suggests names for lists based on content

## Session Management

The app uses a combination of:
- Server-side session for small user preferences and filters
- Client-side localStorage for caching search results and handling deep searches
- Database storage for persistent user data (lists, notes)

## Known Limitations

- Large sets of data can cause the `ERR_RESPONSE_HEADERS_TOO_BIG` error when stored in session cookies
- LLM requests may occasionally time out or return unexpected results
- Game data may become outdated over time and require refreshing

## Future Improvements

- Implement a job queue system for background processing
- Add more advanced filtering options
- Integrate with Steam's API for real-time data
- Allow users to share lists and notes
- Improve mobile UI

## Development Guidelines

1. Follow the existing code style and patterns
2. Use descriptive variable names and add comments for complex logic
3. Keep the UI responsive and accessible
4. Handle errors gracefully and provide feedback to users
5. Test thoroughly on different browsers and devices

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Steam for the game data
- OpenRouter for the AI capabilities
- Firebase for authentication and database services
- Bootstrap for the UI framework