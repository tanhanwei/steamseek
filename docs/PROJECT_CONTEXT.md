# SteamSeek Project Context

This document serves as the primary context provider for LLM sessions. Include this at the beginning of new LLM conversations to ensure continuity and context awareness.

## Project Overview

SteamSeek is an AI-powered Steam game discovery platform that uses semantic search, deep search, and AI analysis to help users find games that truly match what they're looking for.

### Core Features
- **Semantic Search**: Find games based on meaning, not just keywords
- **AI-Enhanced Search**: Optimized queries for better results
- **Deep Search**: Multiple search variations to find hidden gems
- **Game Analysis**: AI-generated analysis of games including sentiment, features, and market positioning
- **Personal Lists**: Create and manage game collections
- **Game Notes**: Add personal markdown notes to games

## Architecture

- **Backend**: Python with Flask (using Blueprint structure)
- **Authentication**: Firebase Authentication (Google Sign-in)
- **Database**: Firebase Firestore (for user data, lists, notes)
- **Search**: Local vector embeddings for semantic search 
- **AI Integration**: OpenRouter API for LLM capabilities
- **Frontend**: Bootstrap 5, JavaScript, HTML/CSS

## Current Development Status

| Component | Status | Notes |
|-----------|--------|-------|
| Core Search | ✅ Complete | Basic, AI-enhanced, and deep search implemented |
| Blueprint Refactoring | ✅ Complete | Code organized into modular blueprints |
| Game Details | ✅ Complete | Game detail pages with AI analysis |
| User Lists | ✅ Complete | Creating and managing game lists |
| Game Notes | ✅ Complete | Adding and viewing notes for games |
| Background Processing | ⚠️ Needs Improvement | Currently using threads, consider job queue later |
| Testing | 🔄 In Progress | Basic tests implemented, need more coverage |
| Error Handling | ⚠️ Needs Improvement | Basic handling in place, needs standardization |
| Documentation | 🔄 In Progress | Technical specs and user docs partially complete |

## Technical Debt

- Deep search background task could use more robust implementation
- Thread-based background processing may have scalability limitations
- Missing comprehensive error handling in some areas
- No rate limiting on API endpoints
- Limited test coverage

## Recent Changes

- Refactored monolithic app.py into blueprint structure (search, auth, games, lists)
- Implemented core search functionality in search blueprint
- Created a new application entry point (app_refactored.py)
- Added structured documentation system

## Testing Status

- Unit tests: Initial set implemented for search functionality
- Integration tests: Basic endpoint tests for search and auth
- Functional tests: None implemented yet
- Current coverage: Approximately 30% of codebase

## Deployment Information

- Development: Local Flask development server
- Planned Production: Render.com web service
- Target Scale: Small proof-of-concept (5 concurrent users max)

## Current Development Priorities

1. Increase test coverage for critical paths
2. Improve error handling and user feedback
3. Enhance search result quality and performance
4. Optimize for deployment on Render.com

## Known LLM Challenges

- Generating complex background task implementations
- Handling Firebase authentication edge cases
- Managing global state in multiple threads
- Creating complex frontend interactions with vanilla JS

---

*Last Updated: [Date]* 