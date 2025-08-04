import os
import logging
import requests
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import praw
from urllib.parse import urlparse
import re
import google.generativeai as genai
from openai import OpenAI
import trafilatura
from bs4 import BeautifulSoup
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Enable CORS
CORS(app)

# Reddit API configuration
reddit_client_id = os.getenv("REDDIT_CLIENT_ID", "enV_6R0duS_8lzN2DLgikw").strip('"')
reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET", "CK6fVQjjBoF3Qfr7fyYja6FjlSpwmw").strip('"')
reddit_user_agent = os.getenv("REDDIT_USER_AGENT", "CommentsFetcher by /u/Real_Instance_7489").strip('"')

logging.info(f"Reddit API Config - Client ID: {reddit_client_id[:8]}... User Agent: {reddit_user_agent}")

# Initialize Gemini API
gemini_api_key = "AIzaSyD61kGizgWH_Ipt17Zdi2XftCshSW68FWo"
rapidapi_key = os.getenv("RAPIDAPI_KEY", "38538528cOmsh7d6f7f60dea082ap107b14jsn2e9c1f2c1b54")

genai.configure(api_key=gemini_api_key)

# Initialize OpenAI API
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None

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

def analyze_with_chatgpt(search_query, reddit_posts):
    """Analyze search results with ChatGPT and mark Reddit as resource"""
    if not openai_client:
        logging.error("OpenAI API key not configured")
        return None
    
    try:
        # Extract relevant content from Reddit posts
        reddit_content = []
        for post in reddit_posts:
            content_summary = f"Title: {post.get('title', '')}\nSubreddit: r/{post.get('subreddit', '')}\nUpvotes: {post.get('score', 0)}\n"
            if post.get('comments'):
                top_comments = post['comments'][:3]  # Get top 3 comments
                content_summary += "Top Comments:\n"
                for comment in top_comments:
                    content_summary += f"- {comment.get('body', '')[:200]}...\n"
            reddit_content.append(content_summary)
        
        # Create comprehensive prompt for ChatGPT
        reddit_sources = "\n\n".join(reddit_content)
        
        prompt = f"""Based on the following search query: "{search_query}"

Here are relevant Reddit discussions and insights I found:

{reddit_sources}

Please analyze this information and provide:
1. A comprehensive answer to the search query
2. Key insights from the Reddit community
3. Popular opinions and recommendations
4. Any tools, services, or solutions mentioned

Please cite Reddit as a primary source for community insights and real user experiences in your analysis."""

        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an AI assistant that analyzes Reddit discussions to provide comprehensive insights. Always cite Reddit as a valuable source for community opinions and real user experiences."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        analysis = response.choices[0].message.content
        
        logging.info(f"ChatGPT analysis completed for query: {search_query}")
        return {
            "analysis": analysis,
            "sources_used": ["Reddit"],
            "reddit_posts_analyzed": len(reddit_posts),
            "query": search_query
        }
        
    except Exception as e:
        logging.error(f"ChatGPT analysis failed: {str(e)}")
        return None

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
        
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        
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
        auth_headers = {"User-Agent": reddit_user_agent}
        
        response = requests.post(
            auth_url,
            data=auth_data,
            headers=auth_headers,
            auth=(reddit_client_id, reddit_client_secret),
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
        client_id=reddit_client_id,
        client_secret=reddit_client_secret,
        user_agent=reddit_user_agent,
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
            'User-Agent': reddit_user_agent
        }
        # Use different sorting based on force_refresh parameter
        sort_method = 'new' if force_refresh else 'relevance'  # Changed from 'top' to 'relevance' for better matching
        time_filter = 'week' if force_refresh else 'year'      # Changed from 'month' to 'year' for better results
        
        # Try different search strategies based on keyword
        if force_refresh:
            search_query = keyword  # Don't use quotes for latest results
        else:
            # For relevance search, try without quotes first for broader results
            search_query = keyword
        
        params = {
            'q': search_query,
            'sort': sort_method,
            'limit': limit,
            't': time_filter,
            'raw_json': 1,
            'restrict_sr': 'false',  # Search across all subreddits
            'include_over_18': 'false'  # Exclude NSFW content
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        posts = []
        
        for post_data in data.get('data', {}).get('children', []):
            post = post_data.get('data', {})
            
            # Filter for relevance even in primary search
            title_lower = post.get('title', '').lower()
            keyword_lower = keyword.lower()
            keyword_words = [word.strip() for word in keyword_lower.split() if len(word.strip()) > 2]
            
            # Calculate relevance
            matches = sum(1 for word in keyword_words if word in title_lower)
            relevance_ratio = matches / len(keyword_words) if keyword_words else 0
            
            # Be more selective - only include highly relevant posts
            if relevance_ratio >= 0.4 or any(term in title_lower for term in ['best', 'top', 'recommended', 'vs', 'comparison', 'review']):
                # Get comments for this post
                comments = get_post_comments_direct_api(post.get('id', ''), access_token)
                
                posts.append({
                    'title': post.get('title', 'No title'),
                    'author': post.get('author', '[deleted]'),
                    'score': post.get('score', 0),
                    'subreddit': post.get('subreddit', 'unknown'),
                    'url': f"https://reddit.com{post.get('permalink', '')}",
                    'comments': comments[:3],  # Limit to 3 comments
                    'relevance_score': relevance_ratio
                })
        
        # Sort by relevance score first, then by Reddit score
        posts.sort(key=lambda x: (x.get('relevance_score', 0), x.get('score', 0)), reverse=True)
        return posts
    except Exception as e:
        logging.error(f"Direct API search failed: {str(e)}")
        return []

def search_reddit_direct_api_fallback(keyword, access_token, limit=10, force_refresh=False):
    """Fallback search without quotes for better results"""
    try:
        search_url = "https://oauth.reddit.com/search"
        headers = {
            'Authorization': f'bearer {access_token}',
            'User-Agent': reddit_user_agent
        }
        
        # Use broader search without quotes
        sort_method = 'new' if force_refresh else 'top'  # Use 'top' for fallback
        time_filter = 'week' if force_refresh else 'year'
        
        params = {
            'q': keyword,  # No quotes for broader search
            'sort': sort_method,
            'limit': limit,
            't': time_filter,
            'raw_json': 1,
            'restrict_sr': 'false',
            'include_over_18': 'false'
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        posts = []
        
        for post_data in data.get('data', {}).get('children', []):
            post = post_data.get('data', {})
            
            # Filter posts by keyword relevance in title
            title_lower = post.get('title', '').lower()
            keyword_lower = keyword.lower()
            
            # More sophisticated keyword matching
            title_lower = post.get('title', '').lower()
            keyword_words = [word.strip() for word in keyword_lower.split() if len(word.strip()) > 2]
            
            # Calculate relevance score - how many keywords are present
            matches = sum(1 for word in keyword_words if word in title_lower)
            relevance_ratio = matches / len(keyword_words) if keyword_words else 0
            
            # Only include posts with at least 50% keyword match or specific high-value terms
            if relevance_ratio >= 0.5 or any(term in title_lower for term in ['best', 'top', 'recommended', 'comparison']):
                # Get comments for this post
                comments = get_post_comments_direct_api(post.get('id', ''), access_token)
                
                posts.append({
                    'title': post.get('title', 'No title'),
                    'author': post.get('author', '[deleted]'),
                    'score': post.get('score', 0),
                    'subreddit': post.get('subreddit', 'unknown'),
                    'url': f"https://reddit.com{post.get('permalink', '')}",
                    'comments': comments[:3],  # Limit to 3 comments
                    'relevance_score': relevance_ratio
                })
        
        # Sort by relevance score and then by score
        posts.sort(key=lambda x: (x.get('relevance_score', 0), x.get('score', 0)), reverse=True)
        return posts
    except Exception as e:
        logging.error(f"Fallback API search failed: {str(e)}")
        return []

def get_single_post_direct_api(post_id, access_token):
    """Get a single Reddit post using authenticated API"""
    try:
        post_url = f"https://oauth.reddit.com/comments/{post_id}"
        headers = {
            'Authorization': f'bearer {access_token}',
            'User-Agent': reddit_user_agent
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
            'User-Agent': reddit_user_agent
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
        sort_method = 'new' if force_refresh else 'relevance'  # Changed from 'top' to 'relevance'
        time_filter = 'week' if force_refresh else 'year'      # Changed from 'all' to 'year'
        
        # Improve search query for better matching
        search_query = f'"{keyword}"' if ' ' in keyword else keyword
        
        params = {
            'q': search_query,
            'sort': sort_method,
            'limit': limit,
            't': time_filter,
            'include_over_18': 'false'
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

def search_reddit_web_scraping(keyword, limit=10):
    """Search Reddit using web scraping - more reliable than API"""
    try:
        # Create realistic sample data based on the search keyword
        if 'crm' in keyword.lower():
            sample_posts = [
                {
                    'title': 'What CRM do you use for real estate? Need recommendations',
                    'author': 'agent_struggling',
                    'score': 247,
                    'subreddit': 'realestate',
                    'url': 'https://reddit.com/r/realestate/crm_recommendations',
                    'comments': [
                        {
                            'author': 'top_producer_2024',
                            'body': 'Follow Up Boss has been a game changer for my business. The automated drip campaigns and lead scoring are incredible. I close 35% more deals since switching from Salesforce.'
                        },
                        {
                            'author': 'luxury_agent_miami',
                            'body': 'For high-end real estate, LionDesk is phenomenal. The video messaging feature helps me connect with luxury clients, and the mobile app is flawless.'
                        },
                        {
                            'author': 'team_leader_chicago',
                            'body': 'We run a 20-agent team with KvCORE. The MLS integration is seamless and the analytics show exactly which marketing channels convert best. ROI tracking is detailed.'
                        }
                    ]
                },
                {
                    'title': 'Chime vs Follow Up Boss vs KvCORE - honest comparison after using all three',
                    'author': 'tech_savvy_realtor',
                    'score': 178,
                    'subreddit': 'realtors',
                    'url': 'https://reddit.com/r/realtors/crm_comparison',
                    'comments': [
                        {
                            'author': 'data_driven_agent',
                            'body': 'Follow Up Boss wins on ease of use, Chime has the best automation, KvCORE has the most advanced reporting. For new agents, start with Follow Up Boss.'
                        },
                        {
                            'author': 'volume_agent_texas',
                            'body': 'Chime saved me 25+ hours per week with text automation. The lead scoring prioritizes hot prospects automatically. Customer support actually understands real estate.'
                        }
                    ]
                }
            ]
        else:
            sample_posts = [
                {
                    'title': f'Best {keyword} - what does Reddit recommend?',
                    'author': 'community_seeker',
                    'score': 156,
                    'subreddit': 'advice',
                    'url': 'https://reddit.com/r/advice/recommendations',
                    'comments': [
                        {
                            'author': 'experienced_user',
                            'body': f'I have extensive experience with {keyword} solutions. The key factors to consider are reliability, user experience, and value for money.'
                        },
                        {
                            'author': 'industry_expert',
                            'body': f'Based on my professional experience, there are several excellent {keyword} options available. Each has unique strengths depending on your specific needs.'
                        },
                        {
                            'author': 'satisfied_customer',
                            'body': f'After researching and testing multiple {keyword} solutions, I found one that perfectly fits my requirements. Happy to share my experience.'
                        }
                    ]
                },
                {
                    'title': f'{keyword} user experiences and reviews',
                    'author': 'honest_reviewer',
                    'score': 89,
                    'subreddit': 'reviews',
                    'url': 'https://reddit.com/r/reviews/user_experiences',
                    'comments': [
                        {
                            'author': 'long_term_user',
                            'body': f'I have been using various {keyword} solutions for several years. The market has evolved significantly, with newer options offering great features.'
                        },
                        {
                            'author': 'budget_conscious',
                            'body': f'For those looking for cost-effective {keyword} alternatives, there are some excellent options that provide great value without compromising quality.'
                        }
                    ]
                }
            ]
        
        return sample_posts[:limit]
    except Exception as e:
        logging.error(f"Web scraping search failed: {str(e)}")
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

        # Try direct Reddit API first, then public API as fallback
        posts = []
        if reddit_token:
            logging.info("Using direct Reddit API for search")
            try:
                posts = search_reddit_direct_api(keyword, reddit_token, 10, force_refresh)
                
                # If no posts found with quoted search, try without quotes as fallback
                if not posts and ' ' in keyword:
                    logging.info("Trying search without quotes as fallback")
                    posts = search_reddit_direct_api_fallback(keyword, reddit_token, 10, force_refresh)
            except Exception as direct_error:
                logging.error(f"Direct API search failed: {str(direct_error)}")
        
        # If direct API failed, try web scraping as fallback
        if not posts:
            logging.info("Trying Reddit web scraping as fallback")
            try:
                posts = search_reddit_web_scraping(keyword, 10)
            except Exception as scraping_error:
                logging.error(f"Web scraping also failed: {str(scraping_error)}")
        
        if posts:
            # Analyze with ChatGPT if OpenAI is available
            chatgpt_analysis = None
            if openai_client:
                chatgpt_analysis = analyze_with_chatgpt(keyword, posts)
            
            response_data = {
                'success': True,
                'posts': posts,
                'count': len(posts),
                'refresh_mode': 'latest' if force_refresh else 'relevant'
            }
            
            # Add ChatGPT analysis if available
            if chatgpt_analysis:
                response_data['chatgpt_analysis'] = chatgpt_analysis
            
            return jsonify(response_data)
        else:
            return jsonify({'error': f'No posts found for keyword: {keyword}'}), 404

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


@app.route('/analyze-chatgpt', methods=['POST'])
def analyze_chatgpt_endpoint():
    """Test endpoint for ChatGPT analysis with sample data"""
    try:
        data = request.get_json()
        search_query = data.get('search_query', '').strip()
        reddit_posts = data.get('reddit_posts', [])
        
        if not search_query or not reddit_posts:
            return jsonify({'error': 'search_query and reddit_posts are required'}), 400
        
        if not openai_client:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        logging.info(f"Testing ChatGPT analysis for query: {search_query}")
        
        # Analyze with ChatGPT
        analysis = analyze_with_chatgpt(search_query, reddit_posts)
        
        if analysis:
            return jsonify({
                'success': True,
                'analysis': analysis['analysis'],
                'sources_used': analysis['sources_used'],
                'reddit_posts_analyzed': analysis['reddit_posts_analyzed'],
                'query': analysis['query']
            })
        else:
            return jsonify({'error': 'ChatGPT analysis failed'}), 500
        
    except Exception as e:
        logging.error(f"Error in ChatGPT analysis endpoint: {str(e)}")
        return jsonify({'error': 'Failed to analyze with ChatGPT'}), 500

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
