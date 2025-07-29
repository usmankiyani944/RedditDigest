import os
import logging
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
reddit = praw.Reddit(client_id=os.getenv("REDDIT_CLIENT_ID",
                                         "enV_6R0duS_8lzN2DLgikw"),
                     client_secret=os.getenv("REDDIT_CLIENT_SECRET",
                                             "CK6fVQjjBoF3Qfr7fyYja6FjlSpwmw"),
                     user_agent=os.getenv(
                         "REDDIT_USER_AGENT",
                         "CommentsFetcher by /u/Real_Instance_7489"))


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

        # Search Reddit for posts
        posts = []
        search_results = reddit.subreddit('all').search(keyword,
                                                        limit=10,
                                                        sort='top',
                                                        time_filter='all')

        for submission in search_results:
            post_data = extract_post_data(submission)
            if post_data:
                posts.append(post_data)

        if not posts:
            return jsonify({'error':
                            f'No posts found for keyword: {keyword}'}), 404

        return jsonify({'success': True, 'posts': posts, 'count': len(posts)})

    except Exception as e:
        logging.error(f"Error in search_keyword: {str(e)}")
        return jsonify({'error': f'Failed to search Reddit: {str(e)}'}), 500


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
