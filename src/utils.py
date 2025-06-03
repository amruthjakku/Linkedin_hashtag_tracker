import logging
from textblob import TextBlob

def parse_post(post):
    """Parse a single post and return author, content, and sentiment."""
    try:
        # Try different selector combinations for author
        author_element = (
            post.find("span", class_="feed-shared-actor__name") or
            post.find("span", class_="update-components-actor__name") or
            post.find("a", class_="app-aware-link")  # Latest LinkedIn structure
        )
        
        # Try different selector combinations for content
        content_element = (
            post.find("span", class_="feed-shared-text") or
            post.find("div", class_="feed-shared-text") or
            post.find("div", class_="update-components-text")
        )
        
        if not author_element or not content_element:
            return None
            
        author = author_element.text.strip()
        content = content_element.text.strip()
        
        if not content:
            return None
            
        analysis = TextBlob(content)
        sentiment = "Positive" if analysis.sentiment.polarity > 0 else "Negative" if analysis.sentiment.polarity < 0 else "Neutral"
        
        # Get timestamp if available
        timestamp_element = post.find("time") or post.find("span", class_="feed-shared-actor__sub-description")
        timestamp = timestamp_element.text.strip() if timestamp_element else "N/A"
        
        return {
            "Author": author,
            "Content": content,
            "Sentiment": sentiment,
            "Timestamp": timestamp
        }
        
    except Exception as e:
        logging.error(f"Error parsing post: {str(e)}")
        return None