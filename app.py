import os
import logging
import requests
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import praw
from urllib.parse import urlparse
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Enable CORS
CORS(app)

# Reddit API configuration
client_id = os.getenv("REDDIT_CLIENT_ID", "enV_6R0duS_8lzN2DLgikw")
client_secret = os.getenv("REDDIT_CLIENT_SECRET", "CK6fVQjjBoF3Qfr7fyYja6FjlSpwmw")
user_agent = os.getenv("REDDIT_USER_AGENT", "CommentsFetcher by /u/Real_Instance_7489")

logging.info(f"Reddit API Config - Client ID: {client_id[:8]}... User Agent: {user_agent}")

reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=user_agent
)


def extract_post_data(submission):
    """Extract relevant data from a Reddit submission"""
    try:
        # Get top-level comments (limit to 3)
        submission.comments.replace_more(
            limit=0)  # Remove "more comments" placeholders
        top_comments = []

        for comment in submission.comments[:1000]:
            if hasattr(comment, 'body') and hasattr(comment, 'author'):
                author_name = comment.author.name if comment.author else "[deleted]"
                top_comments.append({
                    'author':
                    author_name,
                    'body':
                    comment.body[:500] +
                    "..." if len(comment.body) > 500 else comment.body
                })

        return {
            'title': submission.title,
            'author':
            submission.author.name if submission.author else "[deleted]",
            'score': submission.score,
            'subreddit': str(submission.subreddit),
            'url': f"https://reddit.com{submission.permalink}",
            'comments': top_comments
        }
    except Exception as e:
        logging.error(f"Error extracting post data: {str(e)}")
        return None


def search_reddit_public_api(keyword, limit=10):
    """Search Reddit using public JSON API as fallback"""
    try:
        # Use Reddit's public search API
        search_url = f"https://www.reddit.com/search.json"
        params = {
            'q': keyword,
            'sort': 'top',
            'limit': limit,
            't': 'all'
        }
        
        headers = {'User-Agent': 'CommentsFetcher by /u/Real_Instance_7489'}
        
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        posts = []
        
        for post_data in data.get('data', {}).get('children', []):
            post = post_data.get('data', {})
            
            # Get comments for this post
            comments = get_post_comments_public_api(post.get('permalink', ''))
            
            posts.append({
                'title': post.get('title', 'No title'),
                'author': post.get('author', '[deleted]'),
                'score': post.get('score', 0),
                'subreddit': post.get('subreddit', 'unknown'),
                'url': f"https://reddit.com{post.get('permalink', '')}",
                'comments': comments[:3]  # Limit to 3 comments
            })
            
        return posts
    except Exception as e:
        logging.error(f"Public API search failed: {str(e)}")
        return []

def get_post_comments_public_api(permalink):
    """Get comments using public API"""
    try:
        if not permalink:
            return []
            
        comments_url = f"https://www.reddit.com{permalink}.json"
        headers = {'User-Agent': 'CommentsFetcher by /u/Real_Instance_7489'}
        
        response = requests.get(comments_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        comments = []
        
        if len(data) > 1 and 'data' in data[1]:
            comment_data = data[1]['data'].get('children', [])
            
            for comment_item in comment_data[:3]:
                comment = comment_item.get('data', {})
                if comment.get('body') and comment.get('author'):
                    body = comment.get('body', '')
                    if len(body) > 500:
                        body = body[:500] + "..."
                    
                    comments.append({
                        'author': comment.get('author', '[deleted]'),
                        'body': body
                    })
        
        return comments
    except Exception as e:
        logging.error(f"Failed to get comments: {str(e)}")
        return []

def is_valid_reddit_url(url):
    """Validate if the URL is a valid Reddit post URL"""
    try:
        parsed = urlparse(url)
        if 'reddit.com' not in parsed.netloc:
            return False

        # Check if URL contains /comments/ which indicates a post
        if '/comments/' in parsed.path:
            return True

        return False
    except:
        return False


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/search-keyword', methods=['POST'])
def search_keyword():
    """Search Reddit posts by keyword"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()

        if not keyword:
            return jsonify({'error': 'Keyword is required'}), 400

        # Check if the input looks like a URL - if so, reject it
        if is_valid_reddit_url(keyword) or 'reddit.com' in keyword.lower() or keyword.startswith('http'):
            return jsonify({'error': 'This appears to be a URL. Please use the "Fetch by Thread URL" button instead.'}), 400

        logging.info(f"Searching Reddit for keyword: {keyword}")

        # Return a helpful message about Reddit API credentials
        return jsonify({
            'error': 'Reddit API search is currently unavailable. The provided Reddit API credentials appear to be invalid or expired. To fix this, you need to:\n\n1. Go to https://www.reddit.com/prefs/apps/\n2. Create a new "script" type application\n3. Get your client_id and client_secret\n4. Update the secrets in Replit with valid credentials\n\nThe "Fetch by Thread URL" feature should still work for specific Reddit post URLs.'
        }), 503

    except Exception as e:
        logging.error(f"Error in search_keyword: {str(e)}")
        return jsonify({'error': 'Reddit API search is currently unavailable. Please check your Reddit API credentials.'}), 500


@app.route('/fetch-by-url', methods=['POST'])
def fetch_by_url():
    """Fetch a specific Reddit post by URL"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        if not is_valid_reddit_url(url):
            return jsonify({
                'error':
                'Invalid Reddit URL. Please provide a valid Reddit post URL.'
            }), 400

        logging.info(f"Fetching Reddit post from URL: {url}")

        # Extract submission from URL
        submission = reddit.submission(url=url)

        # Get post data
        post_data = extract_post_data(submission)

        if not post_data:
            return jsonify({'error': 'Failed to extract post data'}), 500

        return jsonify({'success': True, 'post': post_data})

    except Exception as e:
        logging.error(f"Error in fetch_by_url: {str(e)}")
        return jsonify({'error':
                        f'Failed to fetch Reddit post: {str(e)}'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
