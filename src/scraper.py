import configparser
import logging
import random
import time
import sys
print("Python version:", sys.version)
print("Python path:", sys.path)

try:
    from selenium import webdriver
    print("Selenium imported successfully")
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options
    print("Selenium components imported successfully")
    
    from bs4 import BeautifulSoup
    print("BeautifulSoup imported successfully")
    
    from textblob import TextBlob
    print("TextBlob imported successfully")
    
    import pandas as pd
    print("Pandas imported successfully")
except ImportError as e:
    print(f"Failed to import required module: {e}")
    sys.exit(1)

# Setup logging with console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper_errors.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

try:
    # Read config
    config = configparser.ConfigParser()
    if not config.read('config/config.ini'):
        raise FileNotFoundError('config/config.ini not found')
    print("Config file read successfully")
    
    username = config['Credentials']['username']
    password = config['Credentials']['password']
    hashtag = config['Settings']['hashtag']
    max_scrolls = int(config['Settings']['max_scrolls'])
    scroll_delay_min = float(config['Settings']['scroll_delay_min'])
    scroll_delay_max = float(config['Settings']['scroll_delay_max'])
    output_file = config['Settings']['output_file']
except Exception as e:
    logging.error(f"Error reading config: {str(e)}")
    sys.exit(1)

def setup_driver():
    """Set up Selenium WebDriver with anti-detection measures."""
    chrome_options = Options()
    
    # Anti-detection measures
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument(f"user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Add experimental options
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Execute CDP commands to prevent detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    return driver

def login_to_linkedin(driver):
    """Log in to LinkedIn."""
    try:
        driver.get("https://www.linkedin.com/login")
        time.sleep(random.uniform(2, 4))
        
        # Updated selectors for username and password fields
        username_field = driver.find_element("id", "username")
        password_field = driver.find_element("id", "password")
        
        # Type like a human
        for char in username:
            username_field.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
        
        time.sleep(random.uniform(1, 2))
        
        for char in password:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
            
        time.sleep(random.uniform(1, 2))
        
        # Click sign in button
        sign_in_button = driver.find_element("xpath", "//button[@type='submit']")
        sign_in_button.click()
        
        # Wait for login to complete
        time.sleep(random.uniform(3, 5))
        
        # Check if login was successful
        if "feed" in driver.current_url or "mynetwork" in driver.current_url:
            logging.info("Successfully logged in to LinkedIn")
        else:
            logging.error("Login may have failed - unexpected URL after login")
            
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        raise

def scrape_hashtag_posts(driver, hashtag, max_scrolls):
    """Scrape posts for the given hashtag."""
    posts = []
    try:
        # Navigate to hashtag search results
        driver.get(f"https://www.linkedin.com/search/results/content/?keywords=%23{hashtag}&origin=GLOBAL_SEARCH_HEADER")
        time.sleep(random.uniform(3, 5))
        
        # Scroll to load more posts
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        
        while scroll_count < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(scroll_delay_min, scroll_delay_max))
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_count += 1
        
        # Parse page source
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Try multiple selector patterns for posts
        posts = (
            soup.find_all("div", class_="feed-shared-update-v2__description-wrapper") or
            soup.find_all("div", {"class": ["feed-shared-update-v2", "occludable-update"]}) or
            soup.find_all("div", {"data-urn": True}) or
            soup.find_all("div", class_="relative feed-shared-update-v2--e2e artdeco-card")
            
        logging.info(f"Found {len(posts)} posts")
        return posts
        
    except Exception as e:
        logging.error(f"Scraping failed: {str(e)}")
        return []

def parse_post(post):
    """Parse individual post data."""
    try:
        # Find author - try multiple possible selectors
        author_elem = (
            post.find("span", {"class": ["feed-shared-actor__name", "update-components-actor__name"]}) or
            post.find("a", {"class": "app-aware-link"})
        )
        if not author_elem:
            return None
        author = author_elem.text.strip()

        # Find content - try multiple possible selectors
        content_elem = (
            post.find("div", {"class": ["feed-shared-update-v2__description-wrapper", "feed-shared-text"]}) or
            post.find("span", {"class": "break-words"})
        )
        if not content_elem:
            return None
        content = content_elem.text.strip()

        # Analyze sentiment
        analysis = TextBlob(content)
        sentiment = "Positive" if analysis.sentiment.polarity > 0 else "Negative" if analysis.sentiment.polarity < 0 else "Neutral"
        
        return {"Author": author, "Content": content, "Sentiment": sentiment}
    except AttributeError as e:
        logging.error(f"Error parsing post: {str(e)}")
        return None

def main():
    driver = setup_driver()
    posts_data = []
    
    try:
        login_to_linkedin(driver)
        logging.info(f"Starting to scrape posts with hashtag #{hashtag}")
        
        posts = scrape_hashtag_posts(driver, hashtag, max_scrolls)
        for post in posts:
            post_data = parse_post(post)
            if post_data:
                posts_data.append(post_data)
        
        # Save to CSV
        if posts_data:
            df = pd.DataFrame(posts_data)
            df.to_csv(output_file, index=False)
            logging.info(f"Successfully saved {len(posts_data)} posts to {output_file}")
        else:
            logging.warning("No posts were found or successfully parsed")
            
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()