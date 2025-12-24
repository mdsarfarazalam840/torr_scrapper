"""
Torrent Automation System - Main Application

A comprehensive automation tool that:
1. Searches for torrents on x1337x.cc
2. Downloads via qBittorrent
3. Creates RAR archives
4. Uploads to Google Drive

Author: Automation System
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check and install dependencies before importing modules
from check_dependencies import check_and_install_requirements
if not check_and_install_requirements():
    print("\n❌ Failed to install required dependencies.")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

from colorama import Fore, Style, init

from modules.scraper import TorrentScraper
from modules.qbittorrent_client import QBittorrentClient
from modules.download_monitor import DownloadMonitor
from modules.archiver import Archiver
from modules.drive_uploader import GoogleDriveUploader
from utils.logger import logger
from utils.helpers import load_config, format_bytes, validate_path

# Initialize colorama
init(autoreset=True)

class TorrentAutomation:
    """Main automation orchestrator."""
    
    def __init__(self, config_path: str = 'config/config.yaml', website_url: str = None, browser: str = None, auto_mode: bool = False):
        """Initialize automation with configuration."""
        try:
            self.config = load_config(config_path)
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)
        
        # Store website URL, browser choice, and auto mode
        self.website_url = website_url
        self.browser = browser
        self.auto_mode = auto_mode
        
        # Initialize components
        self.scraper = None
        self.qb_client = None
        self.monitor = None
        self.archiver = None
        self.uploader = None
        
        self._init_components()
    
    def _init_components(self):
        """Initialize all automation components."""
        # Scraper
        scraper_config = self.config.get('scraper', {})
        # Use website_url if provided, otherwise use config
        base_url = self.website_url if self.website_url else scraper_config.get('base_url', 'https://x1337x.cc')
        # Use browser choice if provided, otherwise use config
        browser = self.browser if self.browser else scraper_config.get('browser', 'chrome')
        
        self.scraper = TorrentScraper(
            base_url=base_url,
            timeout=scraper_config.get('timeout', 30),
            max_retries=scraper_config.get('max_retries', 3),
            user_agent=scraper_config.get('user_agent'),
            browser=browser,
            headless=scraper_config.get('headless', True)  # Run browser invisibly
        )
        
        # qBittorrent client
        qb_config = self.config.get('qbittorrent', {})
        self.qb_client = QBittorrentClient(
            host=qb_config.get('host', 'localhost'),
            port=qb_config.get('port', 8080),
            username=qb_config.get('username', 'admin'),
            password=qb_config.get('password', 'adminadmin')
        )
        
        # Download monitor
        monitor_config = self.config.get('monitoring', {})
        self.monitor = DownloadMonitor(
            self.qb_client,
            poll_interval=monitor_config.get('poll_interval', 5)
        )
        
        # Archiver
        rar_config = self.config.get('rar', {})
        self.archiver = Archiver(
            winrar_path=rar_config.get('winrar_path'),
            sevenzip_path=rar_config.get('sevenzip_path'),
            compression_level=rar_config.get('compression_level', 3)
        )
        
        # Google Drive uploader
        drive_config = self.config.get('drive', {})
        
        self.uploader = GoogleDriveUploader(
            credentials_file=drive_config.get('credentials_file', 'config/credentials.json'),
            token_file=drive_config.get('token_file', 'config/token.pickle'),
            upload_timeout=drive_config.get('upload_timeout', 3600)
        )
    
    def print_banner(self):
        """Print application banner."""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         {Fore.YELLOW}TORRENT AUTOMATION SYSTEM{Fore.CYAN}                        ║
║                                                              ║
║  {Fore.GREEN}Search → Download → Archive → Upload to Drive{Fore.CYAN}           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(banner)
    
    def search_torrents(self):
        """Interactive torrent discovery: Search or Browse Trending."""
        print(f"\n{Fore.YELLOW}═══ TORRENT DISCOVERY ═══{Style.RESET_ALL}\n")
        
        # 1. Fetch and show categories (Dynamic)
        try:
            print(f"{Fore.CYAN}Fetching categories...{Style.RESET_ALL}")
            categories = self.scraper.get_categories()
            if not categories:
                categories = ["Movies", "TV", "Games", "Music", "Apps", "Documentaries", "Other"]
            
            print(f"\n{Fore.CYAN}Step 1: Select Category{Style.RESET_ALL}")
            print(f"  {Fore.GREEN}0. All Categories{Style.RESET_ALL}")
            for i, cat in enumerate(categories, 1):
                print(f"  {i}. {cat}")
            
            cat_choice = input(f"\n{Fore.GREEN}Select Category (0-{len(categories)}) [0]: {Style.RESET_ALL}").strip()
            
            selected_category = 'all'
            category_name = "All Categories"
            
            if cat_choice and cat_choice.isdigit():
                idx = int(cat_choice)
                if 0 < idx <= len(categories):
                    selected_category = categories[idx-1]
                    category_name = selected_category
            
            print(f"\n{Fore.GREEN}✓ Category: {category_name}{Style.RESET_ALL}\n")
            
        except Exception as e:
            logger.debug(f"Category selection error: {e}")
            selected_category = 'all'
            category_name = "All Categories"
        
        # 2. Choose Mode: Search or Trending
        print(f"{Fore.CYAN}Step 2: Choose Action{Style.RESET_ALL}")
        print("  1. Search")
        print(f"  2. Browse Trending/Top in {category_name}")
        
        action = input(f"\n{Fore.GREEN}Enter choice (1-2) [1]: {Style.RESET_ALL}").strip()
        
        torrents = []
        
        if action == '2':
            # Browse Trending
            print(f"\n{Fore.CYAN}Fetching trending torrents for {category_name}...{Style.RESET_ALL}\n")
            torrents = self.scraper.get_trending(category=selected_category)
        else:
            # Search
            query = input(f"\n{Fore.GREEN}Enter search query: {Style.RESET_ALL}").strip()
            if not query:
                logger.error("Search query cannot be empty")
                return None
            
            print(f"\n{Fore.CYAN}Searching for: {query} (in {category_name}){Style.RESET_ALL}\n")
            torrents = self.scraper.search_torrents(query, category=selected_category)
        
        if not torrents:
            logger.error("No torrents found")
            return None
            
        # 3. Filter Results (Client-side)
        return self._filter_results(torrents)
        
    def _filter_results(self, torrents: list) -> list:
        """Apply filters to search results."""
        while True:
            # Show summary
            print(f"\n{Fore.CYAN}Found {len(torrents)} results.{Style.RESET_ALL}")
            
            print(f"{Fore.YELLOW}Step 3: Filter/Sort Results (Optional){Style.RESET_ALL}")
            print("  0. Done (Show Results)")
            print("  1. Sort by Seeds (High to Low)")
            print("  2. Sort by Leechers (High to Low)")
            print("  3. Sort by Size (High to Low)")
            print("  4. Filter by Uploader")
            
            choice = input(f"\n{Fore.GREEN}Enter choice [0]: {Style.RESET_ALL}").strip()
            
            if not choice or choice == '0':
                return torrents
            
            if choice == '1':
                torrents.sort(key=lambda x: x.get('seeds', 0), reverse=True)
                print(f"{Fore.GREEN}✓ Sorted by Seeds{Style.RESET_ALL}")
            
            elif choice == '2':
                torrents.sort(key=lambda x: x.get('leeches', 0), reverse=True)
                print(f"{Fore.GREEN}✓ Sorted by Leechers{Style.RESET_ALL}")
                
            elif choice == '3':
                # Parse size string to bytes for sorting (rough approximation)
                def parse_size(t):
                    s = t.get('size', '0 B').upper()
                    if 'GB' in s: return float(s.replace('GB', '').strip()) * 1024 * 1024 * 1024
                    if 'MB' in s: return float(s.replace('MB', '').strip()) * 1024 * 1024
                    if 'KB' in s: return float(s.replace('KB', '').strip()) * 1024
                    return 0
                torrents.sort(key=parse_size, reverse=True)
                print(f"{Fore.GREEN}✓ Sorted by Size{Style.RESET_ALL}")
                
            elif choice == '4':
                uploader = input(f"{Fore.GREEN}Enter uploader name to match: {Style.RESET_ALL}").lower().strip()
                if uploader:
                    filtered = [t for t in torrents if uploader in t.get('uploader', '').lower()]
                    if filtered:
                        torrents = filtered
                        print(f"{Fore.GREEN}✓ Filtered to {len(torrents)} torrents by '{uploader}'{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}No matches found for uploader '{uploader}'{Style.RESET_ALL}")

            # Display updated results immediately so user can see effect
            if choice in ('1', '2', '3', '4'):
                 self.display_results(torrents)
        
        return torrents
    
    def display_results(self, torrents: list):
        """Display search results in a formatted table."""
        print(f"\n{Fore.YELLOW}═══ SEARCH RESULTS ═══{Style.RESET_ALL}\n")
        
        header = f"{Fore.CYAN}{'#':<4} {'Name':<50} {'Seeds':<8} {'Leech':<8} {'Size':<12}{Style.RESET_ALL}"
        print(header)
        print("─" * 90)
        
        for idx, torrent in enumerate(torrents, 1):
            name = torrent['name'][:47] + "..." if len(torrent['name']) > 50 else torrent['name']
            seeds = torrent['seeds']
            leeches = torrent['leeches']
            size = torrent['size']
            
            # Color code seeds
            if seeds > 100:
                seed_color = Fore.GREEN
            elif seeds > 10:
                seed_color = Fore.YELLOW
            else:
                seed_color = Fore.RED
            
            print(f"{idx:<4} {name:<50} {seed_color}{seeds:<8}{Style.RESET_ALL} {leeches:<8} {size:<12}")
        
        print()
    
    def select_torrent(self, torrents: list):
        """Let user select a torrent."""
        while True:
            try:
                choice = input(f"{Fore.GREEN}Select torrent number (or 'q' to quit): {Style.RESET_ALL}").strip()
                
                if choice.lower() == 'q':
                    return None
                
                idx = int(choice) - 1
                
                if 0 <= idx < len(torrents):
                    return torrents[idx]
                else:
                    print(f"{Fore.RED}Invalid selection. Please try again.{Style.RESET_ALL}")
            
            except ValueError:
                print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")
    
    def show_torrent_details(self, torrent: dict):
        """Display detailed torrent information."""
        print(f"\n{Fore.YELLOW}═══ TORRENT DETAILS ═══{Style.RESET_ALL}\n")
        
        details = self.scraper.get_torrent_details(torrent['url'])
        
        if not details:
            logger.error("Failed to retrieve torrent details")
            return None
        
        print(f"{Fore.CYAN}Name:{Style.RESET_ALL} {torrent['name']}")
        print(f"{Fore.CYAN}Size:{Style.RESET_ALL} {torrent['size']}")
        print(f"{Fore.CYAN}Seeds:{Style.RESET_ALL} {Fore.GREEN}{torrent['seeds']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Leeches:{Style.RESET_ALL} {torrent['leeches']}")
        print(f"{Fore.CYAN}Uploader:{Style.RESET_ALL} {torrent['uploader']}")
        print(f"{Fore.CYAN}Date:{Style.RESET_ALL} {torrent['date']}")
        print(f"{Fore.CYAN}Magnet Link:{Style.RESET_ALL} {details['magnet_link'][:80]}...")
        print()
        
        return details
    
    def download_torrent(self, magnet_link: str):
        """Download torrent via qBittorrent."""
        print(f"\n{Fore.YELLOW}═══ DOWNLOADING TORRENT ═══{Style.RESET_ALL}\n")
        
        # Connect to qBittorrent
        if not self.qb_client.connect():
            logger.error("Failed to connect to qBittorrent. Make sure it's running.")
            return None
        
        # Add torrent
        download_path = self.config['paths']['download_dir']
        validate_path(download_path, create_if_missing=True)
        
        torrent_hash = self.qb_client.add_magnet(magnet_link, save_path=download_path)
        
        if not torrent_hash:
            logger.error("Failed to add torrent")
            return None
        
        logger.info(f"Torrent added with hash: {torrent_hash}")
        
        # Monitor download
        print(f"\n{Fore.CYAN}Monitoring download progress...{Style.RESET_ALL}\n")
        success = self.monitor.monitor_download(torrent_hash)
        
        if not success:
            logger.error("Download failed")
            return None
        
        # Get download path
        download_path = self.qb_client.get_download_path(torrent_hash)
        logger.info(f"Downloaded to: {download_path}")
        
        return download_path
    
    def create_archive(self, source_path: str):
        """Create RAR archive from downloaded files."""
        print(f"\n{Fore.YELLOW}═══ CREATING ARCHIVE ═══{Style.RESET_ALL}\n")
        
        archive_dir = self.config['paths']['archive_dir']
        validate_path(archive_dir, create_if_missing=True)
        
        archive_path = self.archiver.create_rar(source_path, archive_dir)
        
        if not archive_path:
            logger.error("Failed to create archive")
            return None
        
        # Verify archive
        if self.archiver.verify_archive(archive_path):
            logger.info("✓ Archive verified successfully")
        else:
            logger.warning("Archive verification failed")
        
        return archive_path
    
    def upload_to_drive(self, file_path: str):
        """Upload file to Google Drive."""
        print(f"\n{Fore.YELLOW}═══ UPLOADING TO GOOGLE DRIVE ═══{Style.RESET_ALL}\n")
        
        # Get folder selection
        default_folder = self.config['drive'].get('default_folder', 'Torrents')
        
        print(f"{Fore.CYAN}Default folder: {default_folder}{Style.RESET_ALL}")
        folder = input(f"{Fore.GREEN}Enter folder name (or press Enter for default): {Style.RESET_ALL}").strip()
        
        if not folder:
            folder = default_folder
        
        # Upload file
        success = self.uploader.upload_file(file_path, folder)
        
        if success:
            logger.info(f"✓ File uploaded to Google Drive: {folder}/{os.path.basename(file_path)}")
        else:
            logger.error("Upload failed")
        
        # Close browser
        self.uploader.close()
        
        return success
    
    def auto_download_first(self):
        """Automatically download the first torrent from search results."""
        self.print_banner()
        
        try:
            # Step 1: Search torrents
            torrents = self.search_torrents()
            if not torrents:
                return
            
            # Step 2: Display results
            self.display_results(torrents)
            
            # Step 3: Automatically select the first torrent
            selected = torrents[0]
            print(f"\n{Fore.YELLOW}► Auto-selecting first result (newest):{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  {selected['name']}{Style.RESET_ALL}\n")
            
            # Step 4: Show details and get magnet link
            details = self.show_torrent_details(selected)
            if not details:
                return
            
            # Step 5: Download torrent automatically
            downloaded_path = self.download_torrent(details['magnet_link'])
            if not downloaded_path:
                return
            
            # Success message
            print(f"\n{Fore.GREEN}{'='*60}")
            print(f"  ✓ AUTOMATIC DOWNLOAD COMPLETED SUCCESSFULLY!")
            print(f"{'='*60}{Style.RESET_ALL}\n")
            
            print(f"{Fore.CYAN}Downloaded:{Style.RESET_ALL} {downloaded_path}\n")
            
            # Ask if user wants to archive and upload
            archive_upload = input(f"{Fore.YELLOW}Would you like to archive and upload to Google Drive? (y/n): {Style.RESET_ALL}").strip().lower()
            
            if archive_upload == 'y':
                # Step 6: Create archive
                archive_path = self.create_archive(downloaded_path)
                if not archive_path:
                    return
                
                # Step 7: Upload to Google Drive
                upload_success = self.upload_to_drive(archive_path)
                
                if upload_success:
                    print(f"\n{Fore.GREEN}{'='*60}")
                    print(f"  ✓ FULL AUTOMATION COMPLETED SUCCESSFULLY!")
                    print(f"{'='*60}{Style.RESET_ALL}\n")
                    
                    print(f"{Fore.CYAN}Downloaded:{Style.RESET_ALL} {downloaded_path}")
                    print(f"{Fore.CYAN}Archived:{Style.RESET_ALL} {archive_path}")
                    print(f"{Fore.CYAN}Uploaded:{Style.RESET_ALL} Google Drive\n")
        
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}Operation cancelled by user{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            if self.uploader:
                try:
                    self.uploader.close()
                except:
                    pass
            
            if self.scraper:
                try:
                    self.scraper.close()
                except OSError:
                    # Suppress "The handle is invalid" error from undetected-chromedriver
                    pass
                except Exception as e:
                    logger.debug(f"Scraper cleanup error (ignored): {e}")
    
    def run(self):
        """Run the complete automation workflow."""
        self.print_banner()
        
        try:
            # Step 1: Search torrents
            torrents = self.search_torrents()
            if not torrents:
                return
            
            # Step 2: Display results
            self.display_results(torrents)
            
            # Step 3: Select torrent
            selected = self.select_torrent(torrents)
            if not selected:
                logger.info("User cancelled")
                return
            
            # Step 4: Show details and get magnet link
            details = self.show_torrent_details(selected)
            if not details:
                return
            
            # Confirm download
            confirm = input(f"{Fore.YELLOW}Proceed with download? (y/n): {Style.RESET_ALL}").strip().lower()
            if confirm != 'y':
                logger.info("Download cancelled")
                return
            
            # Step 5: Download torrent
            downloaded_path = self.download_torrent(details['magnet_link'])
            if not downloaded_path:
                return
            
            # Step 6: Create archive
            archive_path = self.create_archive(downloaded_path)
            if not archive_path:
                return
            
            # Step 7: Upload to Google Drive
            upload_success = self.upload_to_drive(archive_path)
            
            if upload_success:
                print(f"\n{Fore.GREEN}{'='*60}")
                print(f"  ✓ AUTOMATION COMPLETED SUCCESSFULLY!")
                print(f"{'='*60}{Style.RESET_ALL}\n")
                
                print(f"{Fore.CYAN}Downloaded:{Style.RESET_ALL} {downloaded_path}")
                print(f"{Fore.CYAN}Archived:{Style.RESET_ALL} {archive_path}")
                print(f"{Fore.CYAN}Uploaded:{Style.RESET_ALL} Google Drive\n")
            else:
                logger.error("Automation completed with errors")
        
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}Operation cancelled by user{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            if self.uploader:
                try:
                    self.uploader.close()
                except:
                    pass
            
            if self.scraper:
                try:
                    self.scraper.close()
                except OSError:
                    # Suppress "The handle is invalid" error from undetected-chromedriver
                    pass
                except Exception as e:
                    logger.debug(f"Scraper cleanup error (ignored): {e}")

def main():
    """Main entry point."""
    # Initialize colorama
    init(autoreset=True)
    
    # Print welcome message
    print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗")
    print(f"║                                                              ║")
    print(f"║         {Fore.YELLOW}TORRENT AUTOMATION SYSTEM{Fore.CYAN}                        ║")
    print(f"║                                                              ║")
    print(f"╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
    
    # Prompt for website URL
    print(f"{Fore.YELLOW}Enter the torrent website URL to scrape from:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Examples:{Style.RESET_ALL}")
    print(f"  - https://x1337x.cc")
    print(f"  - https://1337x.to")
    print(f"  - https://1337x.st\n")
    
    website_url = input(f"{Fore.GREEN}Website URL: {Style.RESET_ALL}").strip()
    
    # Validate URL
    if not website_url:
        print(f"{Fore.RED}Error: Website URL cannot be empty{Style.RESET_ALL}")
        sys.exit(1)
    
    # Ensure URL has proper scheme
    if not website_url.startswith(('http://', 'https://')):
        website_url = 'https://' + website_url
    
    print(f"\n{Fore.GREEN}✓ Using website: {website_url}{Style.RESET_ALL}\n")
    
    # Browser selection
    print(f"{Fore.YELLOW}Select browser for automation:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Available browsers:{Style.RESET_ALL}")
    print(f"  1. Chrome (recommended)")
    print(f"  2. Edge")
    print(f"  3. Firefox\n")
    
    browser_choice = input(f"{Fore.GREEN}Enter choice (1-3, or press Enter for Chrome): {Style.RESET_ALL}").strip()
    
    # Map choice to browser name
    browser_map = {
        '1': 'chrome',
        '2': 'edge',
        '3': 'firefox',
        '': 'chrome'  # Default
    }
    
    selected_browser = browser_map.get(browser_choice, 'chrome')
    print(f"\n{Fore.GREEN}✓ Using browser: {selected_browser.title()}{Style.RESET_ALL}\n")
    
    # Mode selection
    print(f"{Fore.YELLOW}Select operation mode:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Available modes:{Style.RESET_ALL}")
    print(f"  1. Automatic (download first/newest result)")
    print(f"  2. Manual (choose from list)\n")
    
    mode_choice = input(f"{Fore.GREEN}Enter choice (1-2, or press Enter for Automatic): {Style.RESET_ALL}").strip()
    
    auto_mode = mode_choice != '2'  # Default to automatic unless user chooses 2
    
    if auto_mode:
        print(f"\n{Fore.GREEN}✓ Mode: Automatic (will download first/newest result){Style.RESET_ALL}\n")
    else:
        print(f"\n{Fore.GREEN}✓ Mode: Manual (you will select from list){Style.RESET_ALL}\n")
    
    # Initialize automation with the provided website URL and browser
    automation = TorrentAutomation(website_url=website_url, browser=selected_browser, auto_mode=auto_mode)
    
    # Run the appropriate workflow
    if auto_mode:
        automation.auto_download_first()
    else:
        automation.run()

if __name__ == "__main__":
    main()

