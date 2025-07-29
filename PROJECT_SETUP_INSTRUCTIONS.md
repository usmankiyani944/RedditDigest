# Reddit AI Reply Generator - Complete Setup Instructions

## Project Overview
A powerful Flask web application that fetches Reddit posts and comments, analyzes sentiment/emotions, and generates intelligent AI-powered replies using Gemini API. Features include keyword search, URL fetching, comment analysis, and brand integration.

## 🚀 Quick Setup Guide

### 1. Create New Replit Project
1. Go to Replit.com and create a new Python project
2. Name it "Reddit AI Reply Generator" or similar

### 2. Required API Keys & Secrets
Add these to your Replit Secrets (Environment Variables):

```bash
# Reddit API Credentials (Required)
REDDIT_CLIENT_ID=enV_6R0duS_8lzN2DLgikw
REDDIT_CLIENT_SECRET=CK6fVQjjBoF3Qfr7fyYja6FjlSpwmw
REDDIT_USER_AGENT=CommentsFetcher by /u/Real_Instance_7489

# RapidAPI Key for Sentiment/Emotion Analysis (Required)
RAPIDAPI_KEY=38538528cOmsh7d6f7f60dea082ap107b14jsn2e9c1f2c1b54

# Optional - Session Secret (auto-generated if not provided)
SESSION_SECRET=your-secret-key-here
```

### 3. Install Dependencies
Create `pyproject.toml`:
```toml
[project]
name = "reddit-ai-reply-generator"
version = "0.1.0"
description = "AI-powered Reddit reply generator with sentiment analysis"
dependencies = [
    "flask",
    "flask-cors", 
    "praw",
    "requests",
    "google-genai",
    "gunicorn"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 4. Create Project Structure
```
project-root/
├── app.py                    # Main Flask application
├── main.py                   # Entry point
├── templates/
│   └── index.html           # Frontend interface
├── static/
│   ├── js/
│   │   └── app.js          # JavaScript functionality
│   └── css/
│       └── style.css       # Custom styles
└── replit.md               # Project documentation
```

### 5. Backend Files

#### `main.py`
```python
from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

#### `app.py`
```python
import os
import logging
import requests
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import praw
from urllib.parse import urlparse
import re
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Enable CORS
CORS(app)

# Reddit API configuration
client_id = os.getenv("REDDIT_CLIENT_ID", "enV_6R0duS_8lzN2DLgikw").strip('"')
client_secret = os.getenv("REDDIT_CLIENT_SECRET", "CK6fVQjjBoF3Qfr7fyYja6FjlSpwmw").strip('"')
user_agent = os.getenv("REDDIT_USER_AGENT", "CommentsFetcher by /u/Real_Instance_7489").strip('"')

logging.info(f"Reddit API Config - Client ID: {client_id[:8]}... User Agent: {user_agent}")

# Initialize Gemini API
gemini_api_key = "AIzaSyD61kGizgWH_Ipt17Zdi2XftCshSW68FWo"
rapidapi_key = os.getenv("RAPIDAPI_KEY")

client = genai.Client(api_key=gemini_api_key)

# [Continue with rest of app.py content...]
```

### 6. Frontend Files

#### `templates/index.html`
```html
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reddit AI Reply Generator</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="{{ url_for('static', filename='css/style.css') }}" rel="stylesheet">
</head>
<body>
    <!-- [HTML content] -->
    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
</body>
</html>
```

#### `static/js/app.js`
```javascript
class RedditFetcher {
    constructor() {
        this.init();
    }

    init() {
        // Initialize DOM elements and event listeners
        // [JavaScript functionality]
    }

    // [Methods for search, reply generation, etc.]
}

// Initialize when DOM loads
let redditFetcher;
document.addEventListener('DOMContentLoaded', () => {
    redditFetcher = new RedditFetcher();
});
```

#### `static/css/style.css`
```css
/* Enhanced styling for better UX */
.comments-section {
    max-height: 400px;
    overflow-y: auto;
}

.comment-item {
    border-left: 3px solid var(--bs-secondary);
    padding-left: 15px;
    margin-bottom: 15px;
}

/* Loading animations and responsive design */
```

## 🔧 Core Features Implemented

### ✅ Reddit Integration
- **Keyword Search**: Search Reddit for top 10 posts by any keyword
- **URL Fetching**: Fetch specific Reddit threads by direct URL
- **Comment Analysis**: Display top 10 most upvoted comments with scores
- **Robust API**: Uses both direct Reddit API and PRAW fallback

### ✅ AI-Powered Reply Generation
- **Sentiment Analysis**: Uses RapidAPI Twinword services for sentiment detection
- **Emotion Analysis**: Analyzes emotional context of comments/posts
- **Gemini AI Integration**: Generates contextual replies using Google's Gemini 2.5 Flash
- **Brand Integration**: Optional brand name inclusion in replies
- **Main Post Replies**: Generate replies to main posts, not just comments
- **Regeneration**: Users can regenerate replies if unsatisfied

### ✅ Enhanced UI/UX
- **Bootstrap Dark Theme**: Professional dark mode interface
- **Real-time Loading**: Loading indicators and error handling
- **Score Display**: Visual upvote indicators for comments
- **Fresh Results**: Clears old results between searches
- **Responsive Design**: Works on all devices

## 🔑 API Endpoints

### `POST /search-keyword`
```json
{
  "keyword": "artificial intelligence"
}
```

### `POST /fetch-by-url`
```json
{
  "url": "https://reddit.com/r/programming/comments/xyz123/..."
}
```

### `POST /generate-reply`
```json
{
  "comment_text": "This is an amazing post!",
  "brand_name": "TechCorp",
  "is_main_post": false
}
```

## 🎯 Usage Instructions

### For Users:
1. **Search**: Enter any keyword to find relevant Reddit posts
2. **Fetch URL**: Paste a Reddit post URL to get specific thread details
3. **Brand Name**: Optionally enter your brand name for AI reply integration
4. **Generate Replies**: Click "Generate Reply" on any comment or main post
5. **Regenerate**: Click "Regenerate" if you want a different AI response

### For Developers:
1. All Reddit API calls are authenticated and rate-limited
2. Sentiment analysis provides fallback for API failures
3. Error handling ensures graceful degradation
4. Modular code structure for easy extensions

## 🚨 Troubleshooting

### Common Issues:
1. **403 Forbidden on RapidAPI**: Check your RapidAPI key in secrets
2. **No Reddit Results**: Verify Reddit API credentials
3. **JavaScript Errors**: Clear browser cache and check console
4. **Slow Loading**: Reddit API can be slow during peak times

### Debug Steps:
1. Check Replit console logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test API endpoints individually using curl
4. Ensure all dependencies are installed

## 🔄 Deployment

### Automatic Deployment:
1. The app runs on port 5000 by default
2. Gunicorn handles production serving
3. All static files are served by Flask
4. CORS is enabled for cross-origin requests

### Manual Testing:
```bash
# Test keyword search
curl -X POST http://localhost:5000/search-keyword \
  -H "Content-Type: application/json" \
  -d '{"keyword": "python programming"}'

# Test reply generation
curl -X POST http://localhost:5000/generate-reply \
  -H "Content-Type: application/json" \
  -d '{"comment_text": "Great post!", "brand_name": "MyBrand"}'
```

## 📈 Advanced Features

### Customization Options:
1. **Comment Limit**: Currently set to top 10, easily adjustable
2. **Reply Tone**: Modify Gemini prompts for different reply styles
3. **Brand Integration**: Smart, contextual brand mentions
4. **Sentiment Themes**: Visual indicators based on sentiment analysis

### Extension Ideas:
1. **User Authentication**: Add user accounts and saved replies
2. **Reply Templates**: Pre-defined reply templates by industry
3. **Analytics Dashboard**: Track reply performance and engagement
4. **Multi-Platform**: Extend to Twitter, LinkedIn, etc.

## 🎉 Success Confirmation

When setup is complete, you should be able to:
- ✅ Search Reddit posts by keyword and see results with 10 comments
- ✅ Fetch specific Reddit threads by URL
- ✅ Generate AI replies for both comments and main posts
- ✅ See sentiment/emotion analysis in reply details
- ✅ Use brand integration in replies
- ✅ Regenerate replies for different variations
- ✅ Experience smooth, refreshed results between searches

---

**🔗 Live Demo**: Your app will be available at your Replit URL once deployed!

**📞 Support**: Check console logs for detailed debugging information.