"""
Web scraper module for 1337x.to torrent site with Edge + VPN.
"""

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from utils.logger import logger
from utils.helpers import format_bytes
import time

class TorrentScraper:
    """Scraper for x1337x.cc torrent search and details with Cloudflare bypass."""
    
    def __init__(self, base_url: str, timeout: int = 30, max_retries: int = 3, user_agent: str = None):
        """
        Initialize scraper with undetected Chrome driver.
        
        Args:
            base_url: Base URL of the torrent site
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            user_agent: Custom user agent string (not used with undetected chromedriver)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.driver = None
        
    def _init_driver(self):
        """Initialize Edge WebDriver with VPN extension support."""
        if self.driver is None:
            logger.info("Initializing Microsoft Edge browser with VPN extension...")
            
            options = EdgeOptions()
            # Load default user profile to access VPN extension
            # This loads your Edge profile with all extensions including VPN
            options.add_argument("user-data-dir=C:\\Users\\kekeb\\AppData\\Local\\Microsoft\\Edge\\User Data")
            options.add_argument("profile-directory=Default")
            
            # Disable automation flags
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # Initialize Edge driver
            try:
                self.driver = webdriver.Edge(options=options)
                logger.info("Edge browser initialized successfully with VPN extension")
                logger.info("⚠ IMPORTANT: Please ensure VPN is connected before searching!")
            except Exception as e:
                logger.error(f"Failed to initialize Edge: {e}")
                raise
    
    def __del__(self):
        """Clean up driver on deletion."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def search_torrents(self, query: str, category: str = 'all', page: int = 1) -> List[Dict]:
        """
        Search for torrents.
        
        Args:
            query: Search query
            category: Category filter (all, movies, tv, games, etc.)
            page: Page number
            
        Returns:
            list: List of torrent dictionaries with metadata
        """
        logger.info(f"Searching for: {query}")
        
        # Construct search URL (regular search, will sort on page)
        search_url = f"{self.base_url}/search/{query.replace(' ', '+')}/{page}/"
        
        try:
            # Make request and get page
            page_source = self._make_request(search_url)
            if not page_source:
                return []
            
            # Try to click "Time" sort link if available
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
            
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Find torrent table
            torrents = []
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
                time.sleep(4)
                
                page_source = self.driver.page_source
                
                # Check for various error states
                if "403" in self.driver.title or "forbidden" in self.driver.title.lower():
                    raise Exception("Still blocked: 403 Forbidden")
                
                if "access denied" in page_source.lower():
                    raise Exception("Access denied by Cloudflare")
                
                # Verify we got actual content
                if page_source and len(page_source) > 1000:
                    logger.info(f"✓ Page retrieved successfully ({len(page_source)} bytes)")
                    
                    # Check for expected content
                    if "table-list" in page_source:
                        logger.debug("✓ Found torrent table in page")
                    else:
                        logger.warning("⚠ Torrent table not found - page structure may have changed") 
                    
                    return page_source
                else:
                    raise Exception("Page source too short, might be blocked")
                
            except Exception as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    # Reset driver on retry
                    if self.driver:
                        try:
                            self.driver.quit()
                        except:
                            pass
                        self.driver = None
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        logger.error(f"All request attempts failed for: {url}")
        return None
