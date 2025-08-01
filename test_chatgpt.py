#!/usr/bin/env python3

import requests
import json
import os

# Test the ChatGPT integration with sample Reddit data
def test_chatgpt_integration():
    # Sample Reddit posts data to test ChatGPT analysis
    sample_posts = [
        {
            "title": "Best CRM for small business in 2024",
            "subreddit": "entrepreneur",
            "author": "business_owner",
            "score": 145,
            "comments": [
                {
                    "author": "sales_expert",
                    "body": "I've been using HubSpot for 3 years and it's been amazing for tracking leads and automating follow-ups."
                },
                {
                    "author": "startup_founder", 
                    "body": "Pipedrive is great for small teams. Simple interface and affordable pricing."
                },
                {
                    "author": "tech_consultant",
                    "body": "Salesforce is the gold standard but might be overkill for small businesses."
                }
            ]
        },
        {
            "title": "CRM software recommendations for real estate",
            "subreddit": "realestate",
            "author": "realtor_mike",
            "score": 89,
            "comments": [
                {
                    "author": "property_agent",
                    "body": "I recommend Follow Up Boss specifically for real estate. Great lead management features."
                },
                {
                    "author": "broker_jane",
                    "body": "Chime is also excellent for real estate teams, especially the automated drip campaigns."
                }
            ]
        }
    ]
    
    # Test the ChatGPT analysis endpoint
    url = "http://localhost:5000/analyze-chatgpt"
    payload = {
        "search_query": "best crm software",
        "reddit_posts": sample_posts
    }
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            result = response.json()
            print("✅ ChatGPT Analysis Success!")
            print("Analysis:", result.get('analysis', 'No analysis')[:200] + "...")
            print("Sources Used:", result.get('sources_used', []))
            print("Posts Analyzed:", result.get('reddit_posts_analyzed', 0))
        else:
            print(f"❌ Error: {response.status_code}")
            print("Response:", response.text)
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")

if __name__ == "__main__":
    test_chatgpt_integration()