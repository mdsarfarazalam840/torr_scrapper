"""
Google Drive uploader module using Selenium browser automation.
"""

import os
import time
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from utils.logger import logger
from tqdm import tqdm

class GoogleDriveUploader:
    """Upload files to Google Drive using browser automation."""
    
    def __init__(self, browser: str = 'edge', upload_timeout: int = 3600):
        """
        Initialize Google Drive uploader.
        
        Args:
            browser: Browser to use ('edge', 'chrome', or 'firefox')
            upload_timeout: Maximum seconds to wait for upload completion
        """
        self.browser = browser.lower()
        self.upload_timeout = upload_timeout
        self.driver = None
    
    def _init_driver(self):
        """Initialize Selenium WebDriver."""
        try:
            logger.info(f"Initializing {self.browser} browser")
            
            if self.browser == 'edge':
                service = EdgeService(EdgeChromiumDriverManager().install())
                options = webdriver.EdgeOptions()
                options.add_argument('--start-maximized')
                options.add_experimental_option('prefs', {
                    'profile.default_content_setting_values.automatic_downloads': 1
                })
                self.driver = webdriver.Edge(service=service, options=options)
                
            elif self.browser == 'chrome':
                service = ChromeService(ChromeDriverManager().install())
                options = webdriver.ChromeOptions()
                options.add_argument('--start-maximized')
                self.driver = webdriver.Chrome(service=service, options=options)
                
            elif self.browser == 'firefox':
                service = FirefoxService(GeckoDriverManager().install())
                options = webdriver.FirefoxOptions()
                self.driver = webdriver.Firefox(service=service, options=options)
                
            else:
                raise ValueError(f"Unsupported browser: {self.browser}")
            
            logger.info("Browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            return False
    
    def navigate_to_drive(self) -> bool:
        """Navigate to Google Drive."""
        try:
            logger.info("Navigating to Google Drive")
            self.driver.get("https://drive.google.com")
            
            # Wait for page to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(3)  # Additional wait for dynamic content
            
            # Check if logged in
            if "accounts.google.com" in self.driver.current_url:
                logger.warning("Not logged into Google Drive. Please log in manually.")
                logger.info("Waiting for manual login (you have 60 seconds)...")
                time.sleep(60)
            
            logger.info("Google Drive loaded")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to Google Drive: {e}")
            return False
    
    def list_folders(self) -> List[str]:
        """
        List available folders in Google Drive.
        
        Returns:
            list: List of folder names
        """
        # This is a simplified implementation
        # In practice, would need to navigate and scrape folder structure
        logger.info("Listing folders (simplified - showing root folders)")
        return ["My Drive", "Computers", "Shared with me"]
    
    def create_folder(self, folder_name: str) -> bool:
        """
        Create a new folder in Google Drive.
        
        Args:
            folder_name: Name of folder to create
            
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Creating folder: {folder_name}")
            
            # Click "New" button
            new_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='New']"))
            )
            new_button.click()
            time.sleep(1)
            
            # Click "New folder"
            folder_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'New folder')]"))
            )
            folder_option.click()
            time.sleep(1)
            
            # Enter folder name
            name_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='New folder']"))
            )
            name_input.clear()
            name_input.send_keys(folder_name)
            time.sleep(0.5)
            
            # Click Create button
            create_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Create')]")
            create_button.click()
            
            logger.info(f"✓ Folder created: {folder_name}")
            time.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            return False
    
    def navigate_to_folder(self, folder_name: str) -> bool:
        """
        Navigate to a specific folder.
        
        Args:
            folder_name: Name of folder to navigate to
            
        Returns:
            bool: True if successful
        """
        try:
            if folder_name == "My Drive":
                # Already at root
                return True
            
            logger.info(f"Navigating to folder: {folder_name}")
            
            # Search for folder
            folder_elem = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//div[@data-tooltip='{folder_name}']"))
            )
            folder_elem.double_click()
            
            time.sleep(2)
            logger.info(f"Navigated to: {folder_name}")
            return True
            
        except Exception as e:
            logger.warning(f"Could not navigate to folder: {e}")
            return False
    
    def upload_file(self, file_path: str, folder_name: Optional[str] = None) -> bool:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Path to file to upload
            folder_name: Target folder name (None for root)
            
        Returns:
            bool: True if upload successful
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        try:
            # Initialize browser if not already done
            if not self.driver:
                if not self._init_driver():
                    return False
                if not self.navigate_to_drive():
                    return False
            
            # Navigate to folder if specified
            if folder_name:
                # Try to navigate to existing folder
                if not self.navigate_to_folder(folder_name):
                    logger.info(f"Folder not found, creating: {folder_name}")
                    if not self.create_folder(folder_name):
                        logger.error("Failed to create folder")
                        return False
                    # Navigate to newly created folder
                    self.navigate_to_folder(folder_name)
            
            logger.info(f"Uploading file: {os.path.basename(file_path)}")
            logger.info(f"File path: {file_path}")
            
            # Find file input element (hidden)
            file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
            
            # Send file path to input
            file_input.send_keys(file_path)
            
            logger.info("Upload started, waiting for completion...")
            
            # Monitor upload progress
            file_size = os.path.getsize(file_path)
            logger.info(f"File size: {file_size / (1024*1024):.2f} MB")
            
            # Wait for upload to complete with progress bar
            uploaded = self._wait_for_upload_complete(os.path.basename(file_path))
            
            if uploaded:
                logger.info("✓ Upload completed successfully!")
                return True
            else:
                logger.error("Upload failed or timed out")
                return False
                
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False
    
    def _wait_for_upload_complete(self, filename: str) -> bool:
        """Wait for upload to complete."""
        try:
            start_time = time.time()
            
            with tqdm(total=100, desc="Uploading", unit="%") as pbar:
                while time.time() - start_time < self.upload_timeout:
                    try:
                        # Check if upload progress indicator is gone
                        # Google Drive shows progress in bottom right
                        progress_elements = self.driver.find_elements(
                            By.XPATH, 
                            "//*[contains(text(), 'Upload complete')]"
                        )
                        
                        if progress_elements:
                            pbar.n = 100
                            pbar.refresh()
                            return True
                        
                        # Check for upload progress text
                        uploading_elements = self.driver.find_elements(
                            By.XPATH,
                            "//*[contains(text(), 'Uploading')]"
                        )
                        
                        if uploading_elements:
                            # Still uploading
                            elapsed = time.time() - start_time
                            progress = min((elapsed / self.upload_timeout) * 100, 99)
                            pbar.n = progress
                            pbar.refresh()
                        else:
                            # No upload indicator - might be complete
                            # Verify file appears in drive
                            time.sleep(5)
                            file_elements = self.driver.find_elements(
                                By.XPATH,
                                f"//*[@data-tooltip='{filename}']"
                            )
                            if file_elements:
                                pbar.n = 100
                                pbar.refresh()
                                return True
                        
                    except Exception:
                        pass
                    
                    time.sleep(3)
            
            # Timeout
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for upload: {e}")
            return False
    
    def close(self):
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
