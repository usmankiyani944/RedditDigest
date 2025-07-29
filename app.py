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

# Sentiment and Emotion Analysis Functions
def analyze_sentiment(text):
    """Analyze sentiment using Twinword RapidAPI"""
    try:
        url = "https://twinword-sentiment-analysis.p.rapidapi.com/analyze/"
        querystring = {"text": text}
        
        headers = {
            "x-rapidapi-key": rapidapi_key,
            "x-rapidapi-host": "twinword-sentiment-analysis.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        logging.error(f"Sentiment analysis failed: {str(e)}")
        return {"type": "neutral", "score": 0.0}

def analyze_emotion(text):
    """Analyze emotion using Twinword RapidAPI"""
    try:
        url = "https://twinword-emotion-analysis-v1.p.rapidapi.com/analyze/"
        
        payload = f"text={text}"
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "x-rapidapi-key": rapidapi_key,
            "x-rapidapi-host": "twinword-emotion-analysis-v1.p.rapidapi.com"
        }
        
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        logging.error(f"Emotion analysis failed: {str(e)}")
        return {"emotions_detected": [{"emotion": "neutral", "score": 0.5}]}

def generate_reply_with_gemini(comment_text, sentiment_data, emotion_data, brand_name=None, is_main_post=False):
    """Generate a reply using Gemini API based on sentiment and emotion analysis"""
    try:
        # Extract key insights from analyses
        sentiment_type = sentiment_data.get("type", "neutral")
        sentiment_score = sentiment_data.get("score", 0.0)
        
        emotions = emotion_data.get("emotions_detected", [])
        primary_emotion = emotions[0]["emotion"] if emotions else "neutral"
        emotion_score = emotions[0]["score"] if emotions else 0.5
        
        # Determine content type
        content_type = "main post" if is_main_post else "comment"
        
        # Build brand context
        brand_context = ""
        if brand_name:
            brand_context = f"\n\nBrand Integration:\n- Naturally mention '{brand_name}' in your reply when relevant, but don't force it\n- If the content relates to your brand's domain, you can share insights from {brand_name}'s perspective\n- Keep the brand mention subtle and valuable, not promotional"
        
        # Create a comprehensive prompt
        prompt = f"""
You are an AI assistant helping to generate thoughtful Reddit replies. Based on the sentiment and emotion analysis below, create an appropriate response to this {content_type}:

Original {content_type.title()}: "{comment_text}"

Sentiment Analysis:
- Type: {sentiment_type}
- Score: {sentiment_score}

Emotion Analysis:
- Primary Emotion: {primary_emotion}
- Confidence: {emotion_score}{brand_context}

Instructions:
1. Match the tone appropriately - if the {content_type} is positive, be encouraging; if negative, be empathetic
2. Keep the reply conversational and natural, like a real Reddit user would write
3. Be helpful and add value to the discussion
4. Keep it concise (2-3 sentences max)
5. Avoid being overly formal or robotic
6. If the {content_type} expresses frustration, acknowledge it and offer support
7. If the {content_type} is excited/happy, share in their enthusiasm
8. {'For main posts, you can ask follow-up questions or share related insights' if is_main_post else 'For comments, build on the conversation naturally'}

Generate a genuine, helpful reply:
"""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return response.text.strip() if response.text else "Thanks for sharing your thoughts! That's an interesting perspective."
        
    except Exception as e:
        logging.error(f"Reply generation failed: {str(e)}")
        return "Thanks for sharing your thoughts! That's an interesting perspective."

# Initialize Reddit API with requests for better control
def get_reddit_access_token():
    """Get access token from Reddit API"""
    try:
        auth_url = "https://www.reddit.com/api/v1/access_token"
        auth_data = {"grant_type": "client_credentials"}
        auth_headers = {"User-Agent": user_agent}
        
        response = requests.post(
            auth_url,
            data=auth_data,
            headers=auth_headers,
            auth=(client_id, client_secret),
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            logging.error(f"Failed to get access token: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error getting access token: {str(e)}")
        return None

# Get access token for direct API calls
reddit_token = get_reddit_access_token()
if reddit_token:
    logging.info("Reddit API access token obtained successfully")
else:
    logging.error("Failed to obtain Reddit access token")

# Still initialize PRAW for compatibility
try:
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        check_for_async=False
    )
except Exception as reddit_error:
    logging.error(f"PRAW initialization failed: {str(reddit_error)}")
    reddit = None


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


def search_reddit_direct_api(keyword, access_token, limit=10, force_refresh=False):
    """Search Reddit using authenticated API with access token"""
    try:
        search_url = "https://oauth.reddit.com/search"
        headers = {
            'Authorization': f'bearer {access_token}',
            'User-Agent': user_agent
        }
        # Use different sorting based on force_refresh parameter
        sort_method = 'new' if force_refresh else 'top'
        time_filter = 'week' if force_refresh else 'month'
        
        params = {
            'q': keyword,
            'sort': sort_method,
            'limit': limit,
            't': time_filter,
            'raw_json': 1
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        posts = []
        
        for post_data in data.get('data', {}).get('children', []):
            post = post_data.get('data', {})
            
            # Get comments for this post
            comments = get_post_comments_direct_api(post.get('id', ''), access_token)
            
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
        logging.error(f"Direct API search failed: {str(e)}")
        return []

def get_single_post_direct_api(post_id, access_token):
    """Get a single Reddit post using authenticated API"""
    try:
        post_url = f"https://oauth.reddit.com/comments/{post_id}"
        headers = {
            'Authorization': f'bearer {access_token}',
            'User-Agent': user_agent
        }
        params = {
            'limit': 10,
            'sort': 'top',
            'raw_json': 1
        }
        
        response = requests.get(post_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if len(data) > 0 and 'data' in data[0]:
            post_data = data[0]['data']['children'][0]['data']
            
            # Get comments
            comments = []
            if len(data) > 1 and 'data' in data[1]:
                comment_data = data[1]['data'].get('children', [])
                
                for comment_item in comment_data[:10]:
                    comment = comment_item.get('data', {})
                    if comment.get('body') and comment.get('author'):
                        body = comment.get('body', '')
                        if len(body) > 500:
                            body = body[:500] + "..."
                        
                        comments.append({
                            'author': comment.get('author', '[deleted]'),
                            'body': body,
                            'score': comment.get('score', 0)
                        })
            
            return {
                'title': post_data.get('title', 'No title'),
                'author': post_data.get('author', '[deleted]'),
                'score': post_data.get('score', 0),
                'subreddit': post_data.get('subreddit', 'unknown'),
                'url': f"https://reddit.com{post_data.get('permalink', '')}",
                'comments': comments
            }
        
        return None
    except Exception as e:
        logging.error(f"Failed to get single post: {str(e)}")
        return None

def get_post_comments_direct_api(post_id, access_token, limit=10):
    """Get comments using authenticated API"""
    try:
        if not post_id:
            return []
            
        comments_url = f"https://oauth.reddit.com/comments/{post_id}"
        headers = {
            'Authorization': f'bearer {access_token}',
            'User-Agent': user_agent
        }
        params = {
            'limit': limit,
            'sort': 'top',
            'raw_json': 1
        }
        
        response = requests.get(comments_url, headers=headers, params=params, timeout=10)
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

def search_reddit_public_api(keyword, limit=10, force_refresh=False):
    """Search Reddit using public JSON API as fallback"""
    try:
        # Use Reddit's public search API
        search_url = f"https://www.reddit.com/search.json"
        # Use different sorting based on force_refresh parameter
        sort_method = 'new' if force_refresh else 'top'
        time_filter = 'week' if force_refresh else 'all'
        
        params = {
            'q': keyword,
            'sort': sort_method,
            'limit': limit,
            't': time_filter
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
        force_refresh = data.get('force_refresh', False)

        if not keyword:
            return jsonify({'error': 'Keyword is required'}), 400

        # Check if the input looks like a URL - if so, reject it
        if is_valid_reddit_url(keyword) or 'reddit.com' in keyword.lower() or keyword.startswith('http'):
            return jsonify({'error': 'This appears to be a URL. Please use the "Fetch by Thread URL" button instead.'}), 400

        logging.info(f"Searching Reddit for keyword: {keyword} (force_refresh: {force_refresh})")

        # Use direct Reddit API with requests since PRAW is having issues
        if reddit_token:
            logging.info("Using direct Reddit API for search")
            try:
                posts = search_reddit_direct_api(keyword, reddit_token, 10, force_refresh)
                if posts:
                    return jsonify({
                        'success': True,
                        'posts': posts,
                        'count': len(posts),
                        'refresh_mode': 'latest' if force_refresh else 'top'
                    })
                else:
                    return jsonify({'error': f'No posts found for keyword: {keyword}'}), 404
            except Exception as direct_error:
                logging.error(f"Direct API search failed: {str(direct_error)}")
        
        # Return error if no working method
        return jsonify({
            'error': 'Reddit API search is currently unavailable. Please try again later.'
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

        # Extract submission ID from URL
        url_parts = url.split('/')
        post_id = None
        for i, part in enumerate(url_parts):
            if part == 'comments' and i + 1 < len(url_parts):
                post_id = url_parts[i + 1]
                break
        
        if not post_id:
            return jsonify({'error': 'Could not extract post ID from URL'}), 400
        
        # Use direct API to get post data
        if reddit_token:
            try:
                post_data = get_single_post_direct_api(post_id, reddit_token)
                if post_data:
                    return jsonify({
                        'success': True,
                        'post': post_data
                    })
                else:
                    return jsonify({'error': 'Post not found or inaccessible'}), 404
            except Exception as direct_error:
                logging.error(f"Direct API fetch failed: {str(direct_error)}")
        
        # Fallback to PRAW if available
        if reddit:
            try:
                submission = reddit.submission(url=url)
                post_data = extract_post_data(submission)
                
                if not post_data:
                    return jsonify({'error': 'Failed to extract post data'}), 500
                
                return jsonify({'success': True, 'post': post_data})
            except Exception as praw_error:
                logging.error(f"PRAW fetch also failed: {str(praw_error)}")
        
        return jsonify({'error': 'Failed to fetch Reddit post'}), 500

    except Exception as e:
        logging.error(f"Error in fetch_by_url: {str(e)}")
        return jsonify({'error':
                        f'Failed to fetch Reddit post: {str(e)}'}), 500


@app.route('/generate-reply', methods=['POST'])
def generate_reply():
    """Generate a reply for a Reddit comment using sentiment analysis and Gemini AI"""
    try:
        data = request.get_json()
        comment_text = data.get('comment_text', '').strip()
        brand_name = data.get('brand_name', '').strip()
        is_main_post = data.get('is_main_post', False)
        
        if not comment_text:
            return jsonify({'error': 'Comment text is required'}), 400
        
        if not rapidapi_key:
            return jsonify({'error': 'RapidAPI key not configured'}), 500
            
        content_type = "main post" if is_main_post else "comment"
        logging.info(f"Generating reply for {content_type}: {comment_text[:100]}...")
        
        # Analyze sentiment and emotion
        sentiment_data = analyze_sentiment(comment_text)
        emotion_data = analyze_emotion(comment_text)
        
        # Generate reply using Gemini
        reply = generate_reply_with_gemini(comment_text, sentiment_data, emotion_data, brand_name, is_main_post)
        
        return jsonify({
            'success': True,
            'reply': reply,
            'sentiment': sentiment_data,
            'emotion': emotion_data,
            'brand_used': bool(brand_name)
        })
        
    except Exception as e:
        logging.error(f"Error generating reply: {str(e)}")
        return jsonify({'error': 'Failed to generate reply'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
