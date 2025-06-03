LinkedIn Hashtag Tracker
Tracks LinkedIn posts for a hashtag (#aii), extracts authors, performs sentiment analysis, and visualizes results.

Setup

Install Python 3.8+ and dependencies:

```bash
pip install -r requirements.txt
```

Install ChromeDriver:
1. Download from https://chromedriver.chromium.org/.
2. Ensure it matches your Chrome browser version (check in Chrome > About Chrome).
3. Add ChromeDriver to your system PATH (e.g., `/usr/local/bin`) or specify its path in `src/scraper.py` like this:
   ```python
   driver = webdriver.Chrome(executable_path="/path/to/chromedriver", options=chrome_options)
   ```

Configure Credentials:
1. Edit `config/config.ini` with your LinkedIn email and password:
   ```ini
   [Credentials]
   username = your_email@example.com
   password = your_password
   ```
2. **Do not share this file publicly.**

(Optional) Adjust settings like `max_scrolls` in `config/config.ini` if needed.

Run the Scraper:

```bash
python src/scraper.py
```

Outputs: `data/linkedin_aii_posts.csv` and console analytics (post count, unique users, sentiment).

Visualize Results:

```bash
python src/visualize.py
```

Outputs: `data/sentiment_distribution.png`.

Notes

- Update HTML class names in `src/scraper.py` and `src/utils.py` if LinkedIn’s structure changes.
- Use random delays and proxies to avoid detection.
- Check `logs/scraper_errors.log` for errors.

Requirements

- Python 3.8+
- Chrome browser and ChromeDriver
- Libraries: selenium, beautifulsoup4, textblob, pandas, matplotlib

Disclaimer
Scraping LinkedIn may violate its terms of service. Use ethically and at your own risk.
