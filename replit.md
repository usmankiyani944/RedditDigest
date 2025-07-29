# Reddit Posts & Comments Fetcher

## Overview

This is a Flask-based web application that allows users to search for Reddit posts by keyword or fetch specific Reddit threads by URL. The application uses the PRAW (Python Reddit API Wrapper) library to interact with Reddit's API and presents the data through a Bootstrap-styled dark theme interface.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology**: Vanilla JavaScript with Bootstrap 5 (dark theme)
- **Structure**: Single-page application with dynamic content loading
- **Styling**: Bootstrap CSS framework with custom CSS for enhanced UI/UX
- **Icons**: Font Awesome for iconography
- **Approach**: Client-side JavaScript handles API calls to the Flask backend and dynamically renders results

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **API Integration**: PRAW library for Reddit API interaction
- **CORS**: Enabled for cross-origin requests
- **Logging**: Basic Python logging configured at DEBUG level
- **Environment Configuration**: Uses environment variables for sensitive configuration

## Key Components

### Flask Application (`app.py`)
- Main Flask application with Reddit API integration
- Handles environment configuration for Reddit API credentials
- Implements data extraction logic for Reddit submissions
- CORS-enabled for frontend communication

### Frontend Interface
- **HTML Template** (`templates/index.html`): Bootstrap-based UI with search form and results display
- **JavaScript Module** (`static/js/app.js`): RedditFetcher class handling user interactions and API calls
- **Custom Styling** (`static/css/style.css`): Enhanced UI components including hover effects and scrollable comments sections

### Entry Point (`main.py`)
- Simple application entry point importing the Flask app

## Data Flow

1. **User Input**: User enters either a keyword for search or a Reddit URL
2. **Frontend Processing**: JavaScript validates input and determines search type
3. **API Request**: Frontend makes request to Flask backend
4. **Reddit API Integration**: Backend uses PRAW to fetch data from Reddit
5. **Data Processing**: Backend extracts relevant post data and top comments (limited to 3)
6. **Response Formatting**: Data is structured and returned to frontend
7. **UI Rendering**: JavaScript dynamically renders posts and comments in the interface

## External Dependencies

### Python Packages
- **Flask**: Web framework for backend API
- **Flask-CORS**: Cross-origin resource sharing support
- **PRAW**: Python Reddit API Wrapper for Reddit integration

### Frontend Dependencies (CDN)
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome 6**: Icon library

### API Integration
- **Reddit API**: Through PRAW library using client credentials
- **Authentication**: Uses Reddit app client ID and secret for API access

## Deployment Strategy

### Environment Configuration
- Uses environment variables for sensitive data (Reddit API credentials, session secrets)
- Fallback default values provided for development
- Session secret key configured via environment variable

### Current Setup
- Designed for Replit deployment (evidenced by Bootstrap CDN link)
- No database dependency - stateless application
- Simple Flask development server setup through main.py

### Scalability Considerations
- Stateless design allows for easy horizontal scaling
- Reddit API rate limiting handled by PRAW library
- CORS enabled for potential frontend separation
- No persistent data storage - all data fetched in real-time from Reddit

## Notable Design Decisions

### Reddit Data Extraction
- **Problem**: Managing Reddit's complex comment structure and API limits
- **Solution**: Limited to top 3 comments per post, with comment truncation at 500 characters
- **Rationale**: Improves performance and user experience by preventing overwhelming data display

### Frontend Architecture Choice
- **Problem**: Need for responsive, interactive UI without complex framework overhead
- **Solution**: Vanilla JavaScript with Bootstrap for rapid development
- **Rationale**: Reduces complexity while maintaining professional appearance and functionality

### API Integration Strategy
- **Problem**: Reddit API complexity and authentication requirements
- **Solution**: PRAW library abstraction with environment-based configuration
- **Rationale**: Simplified Reddit integration while maintaining security best practices