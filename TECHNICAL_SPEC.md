# SteamSeek Technical Specification

This document provides detailed technical information about the SteamSeek application architecture, data flow, and implementation details.

## Architecture Overview

SteamSeek is a Flask-based web application with the following key components:

1. **Frontend**: HTML/CSS/JavaScript with Bootstrap 5
2. **Backend**: Python Flask web server
3. **Authentication**: Firebase Authentication with Google OAuth
4. **Database**: Firebase Firestore for user data
5. **AI Integration**: OpenRouter API for LLM capabilities
6. **Search**: Local vector embeddings for semantic search

## Data Flow

### Search Flow

1. User enters a search query and optionally selects filters
2. Depending on search type:
   - **Standard Search**: Immediate processing in the main request thread
   - **AI-Enhanced**: Background thread with status polling
   - **Deep Search**: Background thread with status polling
3. Search processing:
   - Semantic search against game embeddings
   - Optional AI optimization and re-ranking
   - Filtering by user criteria
   - Sorting by user preference
4. Results are rendered or returned via AJAX

### Game Analysis Flow

1. User views game details page
2. System checks for cached analysis
3. If not cached or refresh requested:
   - Retrieves game data and reviews
   - Sends to LLM for detailed analysis
   - Caches results for future use
4. Renders analysis with interactive elements

### Lists and Notes Flow

1. User interacts with lists or notes UI
2. AJAX requests to backend endpoints
3. Backend performs Firestore operations
4. Response with success/failure and updated data
5. Frontend updates UI accordingly

## Core Components

### Data Loader (`data_loader.py`)

Responsible for:
- Loading game data from JSONL
- Building indexes for fast lookup
- Extracting game information for display

Key functions:
- `build_steam_data_index`: Creates lookup maps for game data
- `load_summaries`: Loads pre-generated game summaries
- `get_game_data_by_appid`: Retrieves specific game information

### LLM Processor (`llm_processor.py`)

Handles all interactions with the LLM service:
- Query optimization
- Result re-ranking
- Deep search variation generation
- Game analysis
- List name generation

Key functions:
- `generate_completion`: Base function for LLM requests
- `optimize_search_query`: Improves search queries
- `rerank_search_results`: Re-orders search results by relevance
- `deep_search_generate_variations`: Creates query variations
- `generate_game_analysis`: Creates detailed game analysis

### Firebase Config (`firebase_config.py`)

Manages Firebase integration:
- Authentication
- User model
- Firestore operations for lists and notes

Key classes and functions:
- `User` class: Represents a user with authentication and data methods
- Firebase initialization and configuration
- CRUD operations for lists and notes

### Semantic Search (`game_chatbot.py`)

Performs vector-based search:
- Converts queries to embeddings
- Finds similar games based on semantic meaning
- Returns ranked results

Key functions:
- `semantic_search_query`: Main search function

### Flask App (`app.py`)

The central application containing:
- Route definitions
- Request handling
- Session management
- Background task coordination
- Template rendering

Key routes:
- `/search`: Main search functionality
- `/detail/<appid>`: Game detail pages
- `/user/lists`: List management
- Various API endpoints for AJAX operations

## Session and State Management

Three-tiered approach to manage state:

1. **Server-side session (Flask session)**:
   - User authentication state
   - Search parameters and filters
   - Small preference data
   - *Note*: Large data sets (like search results) are NOT stored in session to avoid `ERR_RESPONSE_HEADERS_TOO_BIG` errors

2. **Browser localStorage**:
   - Search result caching
   - Deep search and regular search state preservation
   - Pending search restoration

3. **Database (Firestore)**:
   - User lists
   - Game notes
   - Persistent user preferences

## Background Processing

Two types of background processing:

1. **AI-Enhanced Search Background Task**:
   - Function: `regular_search_background_task`
   - State tracking: `regular_search_status` dictionary
   - Status endpoint: `/search_status`
   - Flow: Query optimization → Semantic search → LLM reranking → Filtering → Results

2. **Deep Search Background Task**:
   - Function: `deep_search_background_task`
   - State tracking: `deep_search_status` dictionary
   - Status endpoint: `/deep_search_status`
   - Flow: Query variation generation → Multiple searches → Results combination → Summary generation

## Data Models

### Game Data Structure

Core fields used from the Steam data:
- `appid`: Unique identifier
- `name`: Game title
- `short_description`: Brief game description
- `header_image`: Main image URL
- `screenshots`: Array of screenshot URLs
- `release_date`: When the game was released
- `store_data`: Contains platforms, price, genres, etc.
- `reviews`: Array of user reviews

### User Data in Firestore

Collections:
- `users`: Basic user information
- `user_lists`: Game lists created by users
- `list_games`: Games within lists
- `game_notes`: User notes for specific games

## Recent Changes and Fixes

1. **Session Handling**:
   - Removed storing large result sets in session
   - Implemented localStorage for result caching
   - Added session ID tracking for background tasks

2. **Save to Lists Functionality**:
   - Fixed AJAX/JSON content type handling
   - Improved error handling for list operations
   - Added visual indicators for games already in lists
   - Disabled checkboxes for games already in lists to prevent accidental removal

3. **UI Improvements**:
   - Better loading indicators
   - Toast notifications for user feedback
   - Responsive design adjustments

4. **Bug Fixes**:
   - Fixed `ERR_RESPONSE_HEADERS_TOO_BIG` error by removing large data from session
   - Fixed issue with list loading in modals
   - Fixed page reload issues when saving games to lists

## JavaScript Components

The frontend uses vanilla JavaScript with the following main components:

1. **Search Form Handling**:
   - Intercepts form submission
   - Handles different search types
   - Shows appropriate progress UI

2. **Background Task Polling**:
   - Regular polling of status endpoints
   - Updates progress UI
   - Handles completion and error states

3. **List and Note Management**:
   - AJAX operations for CRUD
   - Modal dialogs for interaction
   - Toast notifications for feedback

4. **Markdown Support**:
   - Preview functionality
   - Rendering via backend API

## API Response Formats

All API endpoints return JSON with a consistent structure:

```json
{
  "success": true|false,
  "message": "Human-readable message",
  "data": {
    // Optional endpoint-specific data
  }
}
```

Status endpoints have standardized fields:
```json
{
  "active": true|false,
  "progress": 0-100,
  "current_step": "Description of current step",
  "completed": true|false,
  "error": null|"Error message"
}
```

## Environment Variables

Required environment variables:
- Flask configuration
  - `FLASK_SECRET_KEY`
- OpenRouter API
  - `OPENROUTER_API_KEY`
  - `OPENROUTER_API_URL`
- Firebase Configuration
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
  - `FIREBASE_API_KEY`
  - `FIREBASE_AUTH_DOMAIN`
  - `FIREBASE_PROJECT_ID`
  - `FIREBASE_STORAGE_BUCKET`
  - `FIREBASE_MESSAGING_SENDER_ID`
  - `FIREBASE_APP_ID`
  - `FIREBASE_SERVICE_ACCOUNT_KEY_PATH`

## Known Issues and Limitations

1. **LLM Reliability**:
   - Occasional timeout or error responses
   - Inconsistent formatting in outputs
   - Rate limits affecting speed

2. **Scaling Concerns**:
   - Background tasks run in-process, limiting concurrency
   - No job queue system for distributed processing
   - Memory usage with large result sets

3. **UI Limitations**:
   - Some responsive design issues on very small screens
   - Modal interactions can be finicky on certain mobile browsers

## Development Workflow

1. **Local Development**:
   - Run with `python app.py` for debug mode
   - Access at http://localhost:5000
   - Flask debug mode provides auto-reload

2. **Deployment**:
   - Configured for deployment on Render
   - See `render_deployment.md` for details

3. **Data Updates**:
   - Place updated Steam data in `data/steam_games_data.jsonl`
   - Pre-generated summaries in `data/summaries.jsonl`

## Future Technical Considerations

1. **Performance Optimization**:
   - Move to a proper job queue (e.g., Celery, RQ)
   - Implement caching layer for frequent queries
   - Optimize JavaScript for larger result sets

2. **Architecture Improvements**:
   - Break up monolithic app.py into modular components
   - Separate API routes into blueprint structure
   - Move to async handling for background tasks (with ASGI)

3. **Features Roadmap**:
   - WebSocket for real-time updates
   - User preference learning
   - Social features for sharing lists
   - Improved mobile experience

4. **Security Enhancements**:
   - Add rate limiting
   - Implement CSRF protection
   - Add input validation middleware 