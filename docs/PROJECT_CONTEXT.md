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
| Testing | 🔄 In Progress | Comprehensive test suite implemented, ~86% overall test coverage |
| Error Handling | ⚠️ Needs Improvement | Basic handling in place, needs standardization |
| Documentation | 🔄 In Progress | Technical specs and user docs partially complete |

## Technical Debt

- Deep search background task could use more robust implementation
- Thread-based background processing may have scalability limitations
- Missing comprehensive error handling in some areas
- No rate limiting on API endpoints
- Limited test coverage for non-search components

## Testing Status

- **Unit tests**: 
  - Search functionality fully covered with tests for filters, AI-enhanced search, deep search, and error handling
  - Authentication tests for User class, auth routes, and list management functionality
  - Lists API tests for list management routes, edge cases, and error handling
  - Games API tests for game detail pages, analysis generation/caching, and game notes functionality
  - Data Loader tests for index building, game data retrieval, and error handling

- **Integration tests**: 
  - Endpoint tests for search, auth, lists, and games functionality
  - Specialized fixtures for Flask context handling
  - Authentication context management with mock users

- **Functional tests**: 
  - Authentication workflows implemented and tested successfully
  - Test framework established in test_user_workflows.py and test_cross_component_workflows.py
  - Template rendering issues identified and documented
  - Simplified functional tests created that bypass template rendering
  - Created FUNCTIONAL_TESTING.md with detailed strategies for Flask application testing

- **Test coverage**: 
  - Search blueprint: ~78%
  - Auth functionality: ~90%
  - Lists functionality: ~95%
  - Games functionality: ~90%
  - Data Loader functionality: ~85%
  - Overall codebase: ~86%

- **Testing challenges**: 
  - Flask context and authentication in route handlers - mostly resolved with specialized fixtures
  - URL generation in templates during tests - partially resolved with render_template mocking
  - Jinja template rendering errors with mock data - mitigated with simplified API-focused tests
  - Cross-component workflow testing - implemented workarounds to test key interactions

## Deployment Information

- Development: Local Flask development server
- Planned Production: Render.com web service
- Target Scale: Small proof-of-concept (5 concurrent users max)

## Current Development Priorities

1. ✅ Design and implement functional test framework
2. ✅ Implement authentication workflow tests
3. 🔄 Refine approach to component testing with template rendering challenges
4. Improve error handling and user feedback
5. Enhance search result quality and performance
6. Optimize for deployment on Render.com
7. Implement stress testing for concurrent users
8. Add security testing for authentication and data access

## Known LLM Challenges

- Generating complex background task implementations
- Handling Firebase authentication edge cases
- Managing global state in multiple threads
- Creating complex frontend interactions with vanilla JS
- Testing Flask applications with complex templates

## Recent Changes

- Refactored monolithic app.py into blueprint structure (search, auth, games, lists)
- Implemented core search functionality in search blueprint
- Created a new application entry point (app_refactored.py)
- Added structured documentation system
- Implemented comprehensive unit tests for search functionality (filters, AI-enhanced, deep search, error handling)
- Improved error handling in search functionality, particularly for semantic search errors and invalid data
- Enhanced deep search implementation with proper background task processing
- Added unit tests for User class and authentication functionality
- Added unit and integration tests for list management functionality
- Created auth_client test fixture for authenticated route testing
- Implemented comprehensive test suite for games functionality including detail pages and notes
- Added advanced tests for list functionality with edge cases and error handling
- Created data loader tests for game data retrieval and index management
- Improved test fixtures with specialized context handling for Flask applications
- Implemented functional tests for authentication workflows
- Developed simplified functional testing approach to bypass template rendering issues
- Created FUNCTIONAL_TESTING.md guide with best practices for Flask application testing
- Documented challenges and solutions for testing Flask applications with complex templates

---

*Last Updated: 2023-10-25* 