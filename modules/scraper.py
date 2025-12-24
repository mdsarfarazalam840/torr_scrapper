"""
Web scraper module for 1337x.to torrent site with Cloudflare bypass.
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from utils.logger import logger
from utils.helpers import format_bytes
import time
import os
import tempfile

class TorrentScraper:
    """Scraper for multiple torrent sites with Cloudflare bypass."""
    
    def __init__(self, base_url: str, timeout: int = 30, max_retries: int = 3, user_agent: str = None, browser: str = 'chrome', headless: bool = True):
        """
        Initialize scraper with selected browser.
        
        Args:
            base_url: Base URL of the torrent site
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            user_agent: Custom user agent string
            browser: Browser to use ('chrome', 'edge', or 'firefox')
            headless: Run browser invisibly in background (default: True)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.browser = browser.lower()
        self.headless = headless
        self.driver = None
        
        # Detect site type
        self.site_type = self._detect_site_type()
        logger.info(f"Detected site type: {self.site_type}")
    
    def _detect_site_type(self) -> str:
        """Detect which torrent site is being used based on URL."""
        url_lower = self.base_url.lower()
        if 'rarbg' in url_lower:
            return 'rarbg'
        elif '1337x' in url_lower:
            return '1337x'
        else:
            logger.warning(f"Unknown site, defaulting to 1337x format")
            return '1337x'
        
    def _init_driver(self):
        """Initialize WebDriver for the selected browser with Cloudflare bypass."""
        if self.driver is None:
            logger.info(f"Initializing {self.browser.title()} browser with Cloudflare bypass...")
            
            try:
                if self.browser == 'chrome':
                    # Use undetected Chrome for best Cloudflare bypass
                    options = uc.ChromeOptions()
                    
                    # Headless mode - run invisibly in background
                    if self.headless:
                        options.add_argument('--headless=new')  # Modern headless mode
                        options.add_argument('--disable-gpu')
                        # Use a unique temporary user data directory to avoid conflicts/locks
                        user_data_dir = os.path.join(tempfile.gettempdir(), f"chrome_automation_{int(time.time())}")
                        options.add_argument(f"--user-data-dir={user_data_dir}")
                        logger.info("Running in headless mode (invisible browser)")
                    else:
                        options.add_argument('--start-maximized')
                    
                    options.add_argument('--disable-blink-features=AutomationControlled')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-dev-shm-usage')
                    
                    # Add aggressive ad blocking arguments
                    options.add_argument('--disable-popup-blocking')
                    options.add_argument('--disable-notifications')
                    options.add_argument('--disable-infobars')
                    options.add_experimental_option('prefs', {
                        'profile.default_content_setting_values': {
                            'notifications': 2,  # Block notifications
                            'media_stream_mic': 2,  # Block microphone
                            'media_stream_camera': 2,  # Block camera
                        }
                    })
                    
                    # Explicitly use subprocess to avoid "session not created" on some systems
                    self.driver = uc.Chrome(options=options, version_main=None, use_subprocess=True)
                    
                    # Inject ad blocking script
                    self._inject_ad_blocker()
                    
                elif self.browser == 'edge':
                    # Use undetected Chrome in Edge mode
                    options = uc.ChromeOptions()
                    
                    # Headless mode - run invisibly in background
                    if self.headless:
                        options.add_argument('--headless=new')  # Modern headless mode
                        options.add_argument('--disable-gpu')
                        options.add_argument('--window-size=1920,1080')
                        logger.info("Running in headless mode (invisible browser)")
                    else:
                        options.add_argument('--start-maximized')
                    
                    options.add_argument('--disable-blink-features=AutomationControlled')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-dev-shm-usage')
                    
                    # Add ad blocking arguments
                    options.add_argument('--disable-popup-blocking')
                    options.add_experimental_option('prefs', {
                        'profile.default_content_setting_values': {
                            'notifications': 2,
                        }
                    })
                    
                    # Use Edge binary
                    self.driver = uc.Chrome(options=options, version_main=None, driver_executable_path=None, browser_executable_path=None)
                    
                    # Inject ad blocking script
                    self._inject_ad_blocker()
                    
                elif self.browser == 'firefox':
                    # Use standard Firefox with stealth settings
                    from selenium import webdriver
                    from selenium.webdriver.firefox.options import Options as FirefoxOptions
                    
                    options = FirefoxOptions()
                    
                    # Headless mode - run invisibly in background
                    if self.headless:
                        options.add_argument('--headless')
                        logger.info("Running in headless mode (invisible browser)")
                    
                    options.set_preference("dom.webdriver.enabled", False)
                    options.set_preference("useAutomationExtension", False)
                    options.add_argument('--width=1920')
                    options.add_argument('--height=1080')
                    
                    self.driver = webdriver.Firefox(options=options)
                    
                else:
                    raise ValueError(f"Unsupported browser: {self.browser}. Choose 'chrome', 'edge', or 'firefox'.")
                
                logger.info(f"✓ {self.browser.title()} browser initialized successfully")
                logger.info("✓ Ad blocking enabled")
                logger.info("✓ Ready to access websites directly (no VPN required)")
                
            except Exception as e:
                logger.error(f"Failed to initialize {self.browser}: {e}")
                if self.driver:
                    try:
                        self.driver.quit()
                    except: pass
                self.driver = None
                raise
    
    def _inject_ad_blocker(self):
        """Inject JavaScript and CSS to aggressively block ads and clean up the page."""
        try:
            ad_block_script = """
            // Inject aggressive CSS to hide ads
            const style = document.createElement('style');
            style.textContent = `
                /* Hide all ad-related elements */
                iframe[src*="ad"],
                iframe[src*="banner"],
                iframe[id*="ad"],
                div[id*="ad"]:not([id*="add"]):not([id*="address"]),
                div[class*="ad"]:not([class*="add"]):not([class*="thead"]):not([class*="head"]),
                div[class*="banner"],
                div[id*="banner"],
                div[class*="popup"],
                div[id*="popup"],
                ins.adsbygoogle,
                [class*="advertisement"],
                [id*="advertisement"],
                .ad-container,
                .ad-placement,
                #ad-top,
                #ad-bottom,
                [id^="google_ads"],
                [class^="google-ad"],
                .sponsored-content,
                .ad-wrapper {
                    display: none !important;
                    visibility: hidden !important;
                    opacity: 0 !important;
                    height: 0 !important;
                    width: 0 !important;
                    position: absolute !important;
                    left: -9999px !important;
                }
            `;
            document.head.appendChild(style);
            
            // Remove ad elements
            const adSelectors = [
                'iframe[src*="ads"]',
                'iframe[src*="ad"]',
                'iframe[src*="banner"]',
                'div[id*="googlead"]',
                'div[class*="adsense"]',
                'ins.adsbygoogle',
                '[id^="google_ads"]',
                '[class^="google-ad"]',
                '.sponsored-content',
                '.ad-wrapper',
                'div[id*="ad-"]:not([id*="add"])',
                'div[class*="ad-"]:not([class*="add"]):not([class*="thead"])'
            ];
            
            function removeAds() {
                let removed = 0;
                adSelectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        if (el && el.parentNode) {
                            el.parentNode.removeChild(el);
                            removed++;
                        }
                    });
                });
                return removed;
            }
            
            // Initial cleanup
            const initialRemoved = removeAds();
            
            // Continuous monitoring for new ads
            const observer = new MutationObserver(() => {
                removeAds();
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            return `Ad blocker active, removed ${initialRemoved} ad elements`;
            """
            
            # Execute the ad blocking script and get result
            result = self.driver.execute_script(ad_block_script)
            if result:
                logger.info(f"✓ {result}")
            else:
                logger.debug("✓ Ad blocking script injected")
        except Exception as e:
            logger.debug(f"Could not inject ad blocker: {e}")
    
    def __del__(self):
        """Clean up driver on deletion."""
        if self.driver:
            try:
                self.driver.quit()
            except (OSError, Exception):
                # Suppress cleanup errors (known issue with undetected_chromedriver on Windows)
                # The OSError "handle is invalid" is harmless and occurs during normal cleanup
                pass
    
    def get_categories(self) -> List[str]:
        """
        Fetch available categories dynamically from the website.
        
        Returns:
            list: List of category names
        """
        # Default fallback
        defaults = ["Movies", "TV", "Games", "Music", "Apps", "Documentaries", "Anime", "Other", "XXX"]
        
        try:
            # Check if we're already on a page, if not load base URL
            if not self.driver:
                self._make_request(self.base_url)
            else:
                try:
                    if self.base_url not in self.driver.current_url:
                         self._make_request(self.base_url)
                except:
                    self._make_request(self.base_url)

            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            categories = []
            
            # Check based on site type
            if self.site_type == 'rarbg':
                # RARBG Sidebar scraping
                # Look for the sidebar links (usually in a div/table on the left)
                # Structure: table with class 'lista2t' or similar, links are "Movies", "TV Shows", etc.
                
                # Based on user image, simple links on left sidebar
                # Try to find links that match common RARBG categories
                common_cats = ["Movies", "TV Shows", "Games", "Music", "Software", "Non XXX", "XXX"]
                
                # Find all links and filter
                links = soup.find_all('a')
                for link in links:
                    text = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    if text in common_cats or "torrents.php?category=" in href:
                        # Map XXX to NSFW
                        display_name = "NSFW" if text == "XXX" else text
                        if display_name == "Non XXX": continue # Skip this aggregate
                        
                        # Store as tuple (Display Name, URL suffix)
                        # Avoid duplicates
                        if display_name not in [c['name'] for c in categories]:
                            categories.append({
                                'name': display_name,
                                'url': href, 
                                'original': text # Keep original for matching
                            })
                
                # Manual fallback if scraping fails (matches the image)
                if not categories:
                    return ["Movies", "TV Shows", "Games", "Music", "Apps", "Anime", "Documentaries", "Other", "NSFW"]
                    
                return [c['name'] for c in categories]

            else:
                # 1337x specifically has a navbar or sidebar with categories
                # Look for links containing '/cat/' or '/sub/'
                links = soup.find_all('a', href=True)
                seen = set()
                
                for link in links:
                    href = link['href']
                    text = link.get_text(strip=True)
                    
                    if '/cat/' in href and text and text not in seen:
                        # e.g. /cat/Movies/ -> Movies
                        clean_text = text.replace('Library', '').strip()
                        if len(clean_text) > 1 and len(clean_text) < 20: 
                            categories.append(clean_text)
                            seen.add(clean_text)
            
            if categories:
                logger.info(f"✓ Fetched {len(categories)} categories from website")
                # Return just strings for the interface
                return sorted(list(seen)) if self.site_type != 'rarbg' else [c['name'] for c in categories]
            
            logger.warning("Could not scrape categories, using defaults")
            return defaults
            
        except Exception as e:
            logger.debug(f"Error fetching categories: {e}")
            return defaults

    def get_trending(self, category: str = None) -> List[Dict]:
        """
        Get trending/top torrents, optionally filtered by category.
        """
        logger.info(f"Fetching trending torrents (Category: {category or 'All'})...")
        
        url = ""
        
        if self.site_type == 'rarbg':
            # RARBG: Category browsing effectively shows recent/trending
            if category and category.lower() != 'all':
                # Map category back to URL if possible, otherwise use search
                # We need to click the link or construct URL
                # Standard RARBG map based on text
                cat_map = {
                    'movies': 'torrents.php?category=movies',
                    'tv shows': 'torrents.php?category=tv',
                    'games': 'torrents.php?category=games',
                    'music': 'torrents.php?category=music',
                    'software': 'torrents.php?category=software',
                    'apps': 'torrents.php?category=software',
                    'anime': 'torrents.php?category=anime',
                    'documentaries': 'torrents.php?category=documentaries',
                    'nsfw': 'torrents.php?category=xxx',
                    'xxx': 'torrents.php?category=xxx'
                }
                
                # Check known map first
                suffix = cat_map.get(category.lower())
                
                # If not found, try to find in scraped categories if we have the driver open
                if not suffix and self.driver:
                    try:
                        links = self.driver.find_elements(By.TAG_NAME, 'a')
                        for link in links:
                            if link.text.strip() == category:
                                suffix = link.get_attribute('href')
                                break
                    except: pass
                
                if suffix:
                    # Ensure suffix has sorting params
                    if 'order=seeders' not in suffix:
                        char = '&' if '?' in suffix else '?'
                        suffix += f"{char}order=seeders&by=DESC"
                    
                    if suffix.startswith('http'):
                        url = suffix
                    else:
                        url = f"{self.base_url}/{suffix}" if not suffix.startswith('/') else f"{self.base_url}{suffix}"
                else:
                     # Fallback to general torrents page with sorting
                     url = f"{self.base_url}/torrents.php?order=seeders&by=DESC"
            else:
                 # Home/All with sorting
                 url = f"{self.base_url}/torrents.php?order=seeders&by=DESC"
                 
            logger.info(f"Using RARBG URL with sorting: {url}")
            
        else:
            # 1337x URLs: 
            # /trending -> All
            # /top-100-movies -> Top 100 filtered
            url = f"{self.base_url}/trending"
            
            if category and category.lower() != 'all':
                cat_slug = category.lower().replace(' ', '-')
                url = f"{self.base_url}/top-100-{cat_slug}"
        
        try:
            page_source = self._make_request(url)
            if not page_source:
                # Fallback
                if category:
                    logger.warning(f"Category page failed, falling back to global")
                    url = f"{self.base_url}/trending" if self.site_type == '1337x' else f"{self.base_url}/torrents.php"
                    page_source = self._make_request(url)
            
            if not page_source:
                return []
            
            soup = BeautifulSoup(page_source, 'lxml')
            torrents = []
            
            # Parse logic depending on site
            if self.site_type == 'rarbg':
                # Use _parse_rarbg_row logic
                # Find table
                table = soup.find('table', class_='lista2t')
                if not table: table = soup.find('table', class_='lista')
                if not table: table = soup.find('table', class_='tablelist2_rarbgproxy')
                
                if table:
                   rows = table.find_all('tr')[1:]
                   for row in rows:
                       t = self._parse_rarbg_row(row)
                       if t: torrents.append(t)
            else:
                table = soup.find('table', class_='table-list')
                if table:
                    rows = table.find_all('tr')[1:]
                    for row in rows:
                        t = self._parse_torrent_row(row)
                        if t: torrents.append(t)
            
            return torrents
            
        except Exception as e:
            logger.error(f"Failed to get trending: {e}")
            return []

    def search_torrents(self, query: str, category: str = 'item', page: int = 1) -> List[Dict]:
        """
        Search for torrents.
        
        Args:
            query: Search query
            category: Category filter
            page: Page number
            
        Returns:
            list: List of torrent dictionaries with metadata
        """
        logger.info(f"Searching for: {query} (Category: {category})")
        
        # Construct search URL based on site type
        if self.site_type == 'rarbg':
            # RARBG format: /search/?search=query&order=data&by=DESC
            # Add category filtering if specified
            cat_param = ""
            if category and category.lower() != 'all':
                # Map categories to RARBG ids
                # Movies: 14,48,17,44,45,47,50,51,52,42,46
                # TV: 18,41,49
                # Games: 23,24,25,26,27,28,29,30,31,32,40,53
                # Music: 23,24,25
                # Software: 33
                # XXX: 4
                
                cat_ids = {
                    'movies': 'category[]=14&category[]=48&category[]=17&category[]=44&category[]=45&category[]=47&category[]=50&category[]=51&category[]=52&category[]=42&category[]=46',
                    'tv': 'category[]=18&category[]=41&category[]=49',
                    'tv shows': 'category[]=18&category[]=41&category[]=49',
                    'games': 'category[]=23&category[]=24&category[]=25&category[]=26&category[]=27&category[]=28&category[]=29&category[]=30&category[]=31&category[]=32&category[]=40&category[]=53',
                    'music': 'category[]=23&category[]=24&category[]=25',
                    'apps': 'category[]=33',
                    'software': 'category[]=33',
                    'nsfw': 'category[]=4',
                    'xxx': 'category[]=4'
                }
                
                params = cat_ids.get(category.lower())
                if params:
                    cat_param = f"&{params}"
            
            search_url = f"{self.base_url}/search/?search={query.replace(' ', '%20')}&order=data&by=DESC{cat_param}"
            logger.info(f"RARBG search URL: {search_url}")
        else:
            # 1337x format
            if category and category.lower() not in ('all', 'item', 'none'):
                # Category search: /category-search/query/Category/page/
                # Ensure category is correctly capitalized as 1337x expects
                formatted_cat = category
                known_cats = self.get_categories()
                for cat in known_cats:
                    if cat.lower() == category.lower():
                        formatted_cat = cat
                        break
                
                search_url = f"{self.base_url}/category-search/{query.replace(' ', '+')}/{formatted_cat}/{page}/"
                logger.info(f"Using category search URL: {search_url}")
            else:
                # Standard search: /search/query/page/
                search_url = f"{self.base_url}/search/{query.replace(' ', '+')}/{page}/"
        
        try:
            # Make request and get page
            page_source = self._make_request(search_url)
            if not page_source:
                return []
            
            # Try to click "Time" sort link if available (only for 1337x)
            # RARBG uses URL parameters for sorting (already included in search_url)
            if self.site_type == '1337x':
                try:
                    logger.info("Attempting to sort by time...")
                    
                    # Find and click the Time sort link
                    time_links = self.driver.find_elements(By.LINK_TEXT, "Time")
                    if time_links:
                        logger.info("Found 'Time' sort link, clicking...")
                        time_links[0].click()
                        
                        # Wait for page to reload with sorted results
                        import time
                        time.sleep(4)
                        
                        # Get the new page source after sorting
                        page_source = self.driver.page_source
                        logger.info("✓ Results sorted by time")
                    else:
                        logger.warning("'Time' sort link not found - using default sort")
                except Exception as e:
                    logger.warning(f"Could not sort by time: {e} - using default sort")
            else:
                # For RARBG, sorting is already in URL
                logger.info("✓ RARBG sorting applied via URL parameters (order=data&by=DESC)")
            
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Find torrent table based on site type
            torrents = []
            
            if self.site_type == 'rarbg':
                # RARBG uses different table structure - try multiple selectors
                table = soup.find('table', class_='lista2t')
                if not table:
                    # Try alternative RARBG table classes
                    table = soup.find('table', class_='lista')
                if not table:
                    # Try RARBG proxy table classes (e.g., rarbgproxy.to)
                    table = soup.find('table', class_='tablelist2_rarbgproxy')
                if not table:
                    # Try finding any table with torrent data
                    tables = soup.find_all('table')
                    for t in tables:
                        if t.find('tr', class_='lista2') or t.find('tr', class_='table2ta_rarbgproxy'):
                            table = t
                            break
                
                if not table:
                    logger.warning("No torrents found or page structure changed")
                    logger.debug(f"Page size: {len(page_source)} bytes")
                    # Save HTML for debugging
                    try:
                        import os
                        debug_file = os.path.join(os.path.dirname(__file__), '..', 'debug_rarbg.html')
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(page_source)
                        logger.info(f"Saved page HTML to {debug_file} for debugging")
                    except Exception as save_error:
                        logger.debug(f"Could not save debug HTML: {save_error}")
                    return []
                
                rows = table.find_all('tr', class_='lista2')
                if not rows:
                    # Try RARBG proxy row class
                    rows = table.find_all('tr', class_='table2ta_rarbgproxy')
                if not rows:
                    # Try without class filter
                    rows = table.find_all('tr')[1:]  # Skip header
                
                for row in rows:
                    try:
                        torrent = self._parse_rarbg_row(row)
                        if torrent:
                            torrents.append(torrent)
                    except Exception as e:
                        logger.debug(f"Error parsing torrent row: {e}")
                        continue
            else:
                # 1337x format
                table = soup.find('table', class_='table-list')
                if not table:
                    logger.warning("No torrents found or page structure changed")
                    return []
                
                rows = table.find_all('tr')[1:]  # Skip header row
                for row in rows:
                    try:
                        torrent = self._parse_torrent_row(row)
                        if torrent:
                            torrents.append(torrent)
                    except Exception as e:
                        logger.debug(f"Error parsing torrent row: {e}")
                        continue
            
            logger.info(f"Found {len(torrents)} torrents")
            return torrents
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _parse_torrent_row(self, row) -> Optional[Dict]:
        """Parse a single torrent table row."""
        cols = row.find_all('td')
        
        if len(cols) < 5:
            return None
        
        # Extract name and link
        name_col = cols[0]
        name_links = name_col.find_all('a')
        
        if len(name_links) < 2:
            return None
        
        name = name_links[1].text.strip()
        detail_url = self.base_url + name_links[1].get('href', '')
        
        # Extract seeds, leeches, size
        seeds = cols[1].text.strip()
        leeches = cols[2].text.strip()
        date = cols[3].text.strip()
        size = cols[4].text.strip()
        
        # Extract uploader if available
        uploader = "Unknown"
        uploader_link = name_col.find('a', class_='uploader')
        if uploader_link:
            uploader = uploader_link.text.strip()
        
        return {
            'name': name,
            'url': detail_url,
            'seeds': int(seeds) if seeds.isdigit() else 0,
            'leeches': int(leeches) if leeches.isdigit() else 0,
            'size': size,
            'date': date,
            'uploader': uploader
        }
    
    def _parse_rarbg_row(self, row) -> Optional[Dict]:
        """Parse a single RARBG torrent table row."""
        cols = row.find_all('td')
        
        if len(cols) < 7:
            return None
        
        try:
            # RARBG proxy structure (e.g., rarbgproxy.to):
            # Col 0: Category icon
            # Col 1: File name (with link)
            # Col 2: Category text
            # Col 3: Added date
            # Col 4: Size
            # Col 5: Seeders
            # Col 6: Leechers
            # Col 7: Uploader (if available)
            
            name_col = cols[1]
            name_link = name_col.find('a')
            
            if not name_link:
                return None
            
            name = name_link.text.strip()
            detail_url = name_link.get('href', '')
            if not detail_url.startswith('http'):
                detail_url = self.base_url + detail_url
            
            # Date in column 3
            date = cols[3].text.strip()
            # Size in column 4
            size = cols[4].text.strip()
            # Seeds in column 5
            seeds = cols[5].text.strip()
            # Leeches in column 6
            leeches = cols[6].text.strip()
            
            # Uploader in column 7 if it exists
            uploader = "Unknown"
            if len(cols) > 7:
                uploader_text = cols[7].text.strip()
                if uploader_text:
                    uploader = uploader_text
            
            return {
                'name': name,
                'url': detail_url,
                'seeds': int(seeds) if seeds.isdigit() else 0,
                'leeches': int(leeches) if leeches.isdigit() else 0,
                'size': size,
                'date': date,
                'uploader': uploader
            }
        except Exception as e:
            logger.debug(f"Error parsing RARBG row: {e}")
            return None
    
    def get_torrent_details(self, url: str) -> Optional[Dict]:
        """
        Get detailed torrent information including magnet link.
        
        Args:
            url: Torrent detail page URL
            
        Returns:
            dict: Torrent details including magnet link
        """
        logger.info(f"Fetching torrent details from: {url}")
        
        try:
            page_source = self._make_request(url)
            if not page_source:
                return None
            
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Find magnet link
            magnet_link = None
            magnet_elem = soup.find('a', href=lambda x: x and x.startswith('magnet:'))
            if magnet_elem:
                magnet_link = magnet_elem.get('href')
            
            if not magnet_link:
                logger.error("Magnet link not found")
                return None
            
            # Extract additional details
            details = {
                'magnet_link': magnet_link,
                'url': url
            }
            
            # Try to extract more info from the page
            info_box = soup.find('div', class_='torrent-detail-page')
            if info_box:
                # Extract category, language, etc.
                info_items = info_box.find_all('li')
                for item in info_items:
                    text = item.get_text(strip=True)
                    if ':' in text:
                        key, value = text.split(':', 1)
                        details[key.strip().lower()] = value.strip()
            
            logger.info("Successfully retrieved torrent details")
            return details
            
        except Exception as e:
            logger.error(f"Failed to get torrent details: {e}")
            return None
    
    def _make_request(self, url: str) -> Optional[str]:
        """Make HTTP request using undetected Chrome to bypass Cloudflare."""
        self._init_driver()
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Request attempt {attempt + 1}/{self.max_retries}: {url}")
                
                self.driver.get(url)
                logger.info("Page loaded, checking for Cloudflare challenge...")
                
                # Inject ad blocker on page load
                try:
                    self._inject_ad_blocker()
                except:
                    pass
                
                # Extended wait for Cloudflare challenge to auto-complete
                max_wait = 30  # Extended to 30 seconds
                waited = 0
                challenge_detected = False
                
                while waited < max_wait:
                    time.sleep(2)
                    waited += 2
                    
                    try:
                        page_source = self.driver.page_source
                        page_title = self.driver.title.lower()
                        
                        # Check if Cloudflare challenge is present
                        if ("just a moment" in page_source.lower() or 
                            "checking your browser" in page_source.lower() or 
                            "please wait" in page_source.lower() or
                            "verify you are human" in page_source.lower() or
                            "challenge" in page_title):
                            
                            if not challenge_detected:
                                logger.info("⏳ Cloudflare challenge detected - waiting for auto-completion...")
                                challenge_detected = True
                            else:
                                logger.info(f"   Still waiting... ({waited}s elapsed)")
                        else:
                            # Challenge appears to be completed
                            if challenge_detected:
                                logger.info("✓ Cloudflare challenge completed!")
                            break
                            
                    except Exception as e:
                        logger.debug(f"Error checking page state: {e}")
                        continue
                
                # Final wait for content to fully render
                logger.info("Waiting for page content to render...")
                # Longer wait for RARBG sites as they load slowly
                wait_time = 8 if self.site_type == 'rarbg' else 4
                time.sleep(wait_time)
                
                # Re-inject ad blocker after wait
                try:
                    self._inject_ad_blocker()
                except:
                    pass
                
                page_source = self.driver.page_source
                
                # Check for various error states
                if "403" in self.driver.title or "forbidden" in self.driver.title.lower():
                    raise Exception("Still blocked: 403 Forbidden")
                
                if "access denied" in page_source.lower():
                    raise Exception("Access denied by Cloudflare")
                
                # Verify we got actual content
                if page_source and len(page_source) > 1000:
                    logger.info(f"✓ Page retrieved successfully ({len(page_source)} bytes)")
                    
                    # Check for expected content based on site type
                    if "table-list" in page_source or "lista2t" in page_source or "tablelist2_rarbgproxy" in page_source:
                        logger.debug("✓ Found torrent table in page")
                        return page_source
                    else:
                        logger.warning("⚠ Torrent table not found - trying refresh...") 
                        # Try refreshing the page once
                        try:
                            logger.info("Refreshing page to reload content...")
                            self.driver.refresh()
                            time.sleep(5)  # Wait for refresh
                            page_source = self.driver.page_source
                            
                            if "table-list" in page_source or "lista2t" in page_source or "tablelist2_rarbgproxy" in page_source:
                                logger.info("✓ Content found after refresh")
                                return page_source
                            else:
                                logger.warning("Content still not found after refresh")
                                return page_source  # Return anyway, let parser handle it
                        except Exception as refresh_error:
                            logger.warning(f"Refresh failed: {refresh_error}")
                            return page_source  # Return original page source
                else:
                    raise Exception("Page source too short, might be blocked")
                
            except Exception as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    # Refresh page before retry
                    logger.info("Attempting page refresh before retry...")
                    try:
                        self.driver.refresh()
                        time.sleep(3)
                    except:
                        # If refresh fails, reset driver on retry
                        if self.driver:
                            try:
                                self.driver.quit()
                            except (OSError, Exception):
                                # Suppress all cleanup errors
                                pass
                            self.driver = None
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        logger.error(f"All request attempts failed for: {url}")
        return None
