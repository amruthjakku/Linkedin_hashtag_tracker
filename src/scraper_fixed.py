import configparser
import logging
import random
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from textblob import TextBlob
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Read config
config = configparser.ConfigParser()
if not config.read('config/config.ini'):
    raise FileNotFoundError('config/config.ini not found')

username = config['Credentials']['username']
password = config['Credentials']['password']
hashtag = config['Settings']['hashtag']
max_scrolls = int(config['Settings']['max_scrolls'])
scroll_delay_min = float(config['Settings']['scroll_delay_min'])
scroll_delay_max = float(config['Settings']['scroll_delay_max'])
output_file = config['Settings']['output_file']

def setup_driver():
    """Set up Selenium WebDriver with anti-detection measures."""
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(options=chrome_options)
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
        
        username_field = driver.find_element("id", "username")
        password_field = driver.find_element("id", "password")
        
        for char in username:
            username_field.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
        
        time.sleep(random.uniform(1, 2))
        
        for char in password:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
            
        sign_in_button = driver.find_element("xpath", "//button[@type='submit']")
        sign_in_button.click()
        time.sleep(random.uniform(3, 5))
        
        if "feed" in driver.current_url or "mynetwork" in driver.current_url:
            logging.info("Successfully logged in to LinkedIn")
        else:
            logging.warning("Login may have failed - unexpected URL after login")
            
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        raise

def scrape_hashtag_posts(driver, hashtag, max_scrolls):
    """Scrape posts for the given hashtag."""
    posts = []
    try:
        url = f"https://www.linkedin.com/search/results/content/?keywords=%23{hashtag}&origin=GLOBAL_SEARCH_HEADER"
        driver.get(url)
        time.sleep(random.uniform(3, 5))
        
        for _ in range(max_scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(scroll_delay_min, scroll_delay_max))
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Try multiple selectors and log results
        selectors = [
            ("div", {"class": "feed-shared-update-v2"}),
            ("div", {"class": "update-components-text"}),
            ("div", {"class": "feed-shared-update-v2__content"}),
            ("div", {"class": "update-components-update"}),
            ("div", {"data-urn": True}),
            ("article", {"class": "relative ember-view"}),
        ]
        
        for tag, attrs in selectors:
            found = soup.find_all(tag, attrs)
            if found:
                logging.info(f"Found {len(found)} posts with selector {tag}, {attrs}")
                posts.extend(found)
        
        if not posts:
            # Save HTML for debugging
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            logging.info("Saved HTML to debug_page.html for inspection")
        
        logging.info(f"Found total of {len(posts)} posts")
        return posts
    except Exception as e:
        logging.error(f"Scraping failed: {str(e)}")
        return []

def parse_post(post):
    """Parse post data and analyze sentiment."""
    try:
        # Debug the post structure
        logging.debug(f"Processing post with classes: {post.get('class', [])}")
        
        # Try multiple selectors for author
        author_selectors = [
            ("span", {"class": "update-components-actor__name"}),
            ("span", {"class": "feed-shared-actor__name"}),
            ("span", {"class": "update-components-actor__title"}),
            ("a", {"class": "app-aware-link"}),
        ]
        
        # Try multiple selectors for content
        content_selectors = [
            ("div", {"class": "feed-shared-text"}),
            ("span", {"class": "break-words"}),
            ("div", {"class": "update-components-text"}),
            ("div", {"class": "feed-shared-update-v2__description-wrapper"}),
        ]
        
        author_elem = None
        for tag, attrs in author_selectors:
            author_elem = post.find(tag, attrs)
            if author_elem:
                logging.debug(f"Found author with selector {tag}, {attrs}")
                break
                
        content_elem = None
        for tag, attrs in content_selectors:
            content_elem = post.find(tag, attrs)
            if content_elem:
                logging.debug(f"Found content with selector {tag}, {attrs}")
                break
            
        if not author_elem or not content_elem:
            if not author_elem:
                logging.debug("Failed to find author element")
            if not content_elem:
                logging.debug("Failed to find content element")
            return None
            
        author = author_elem.text.strip()
        content = content_elem.text.strip()
        
        if not content:
            logging.debug("Empty content found")
            return None
            
        analysis = TextBlob(content)
        sentiment = "Positive" if analysis.sentiment.polarity > 0 else "Negative" if analysis.sentiment.polarity < 0 else "Neutral"
        
        post_data = {
            "Author": author,
            "Content": content,
            "Sentiment": sentiment
        }
        
        logging.debug(f"Successfully parsed post: {post_data}")
        return post_data
        
    except Exception as e:
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
