#!/usr/bin/env python3
"""
Test the ChatGPT integration with sample Reddit data since the Reddit API is having authentication issues.
This shows how the ChatGPT analysis would work once Reddit API is fixed.
"""

import requests
import json

def test_chatgpt_with_sample_data():
    """Test ChatGPT integration with realistic Reddit-style data"""
    
    # Realistic sample data that looks like real Reddit posts
    sample_data = {
        "search_query": "best crm for real estate agents",
        "reddit_posts": [
            {
                "title": "What's the best CRM for real estate agents? I'm drowning in leads",
                "subreddit": "realestate",
                "author": "struggling_agent",
                "score": 287,
                "comments": [
                    {
                        "author": "top_producer_2024",
                        "body": "I've been using Follow Up Boss for 3 years and it's transformed my business. The automated drip campaigns are incredible - I close 40% more deals now. It's specifically built for real estate, so it understands our lead sources and conversion funnel. Worth every penny at $99/month."
                    },
                    {
                        "author": "luxury_homes_expert",
                        "body": "For high-end clients, I swear by LionDesk. The communication tools are sophisticated enough for luxury real estate. Video messaging, smart lists, and the mobile app is fantastic. Much better than generic CRMs that don't understand our industry."
                    },
                    {
                        "author": "team_leader_chicago",
                        "body": "We run a 15-agent team and use KvCORE. The MLS integration is seamless and the lead attribution reports show exactly which marketing channels are working. Analytics are incredibly detailed - shows cost per lead, conversion rates by source, etc."
                    }
                ]
            },
            {
                "title": "Follow Up Boss vs Chime vs KvCORE - honest comparison",
                "subreddit": "realtors",
                "author": "tech_savvy_realtor",
                "score": 156,
                "comments": [
                    {
                        "author": "data_driven_agent",
                        "body": "Used all three. Follow Up Boss is the most user-friendly, Chime has the best automation features, and KvCORE has the most advanced analytics. If you're just starting out, go with Follow Up Boss. If you're doing volume business, KvCORE is worth the complexity."
                    },
                    {
                        "author": "millennial_realtor",
                        "body": "Chime's text messaging automation saved me 20+ hours per week. The lead scoring is also really smart - it prioritizes hot leads automatically. Customer support is amazing too, they actually understand real estate."
                    }
                ]
            },
            {
                "title": "Anyone tried the new real estate CRM features in HubSpot?",
                "subreddit": "entrepreneur",
                "author": "business_optimizer",
                "score": 98,
                "comments": [
                    {
                        "author": "proptech_insider",
                        "body": "HubSpot added some real estate templates but it's still too generic. Missing key features like MLS integration, commission tracking, and closing date pipelines. Stick with industry-specific tools like Follow Up Boss or Wise Agent."
                    }
                ]
            }
        ]
    }
    
    # Test the ChatGPT analysis endpoint
    try:
        response = requests.post(
            "http://localhost:5000/analyze-chatgpt",
            json=sample_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("🎉 ChatGPT Analysis Success!")
            print("=" * 60)
            print(f"Query: {result.get('query')}")
            print(f"Posts Analyzed: {result.get('reddit_posts_analyzed')}")
            print(f"Sources: {result.get('sources_used')}")
            print("=" * 60)
            print("ANALYSIS:")
            print(result.get('analysis', 'No analysis available'))
            print("=" * 60)
            print("\n✅ This demonstrates how ChatGPT cites Reddit as a valuable source!")
            print("✅ This helps your clients rank in LLMs by marking Reddit as authoritative!")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")

if __name__ == "__main__":
    print("Testing ChatGPT Integration with Sample Reddit Data")
    print("=" * 60)
    test_chatgpt_with_sample_data()