"""
Google Drive uploader module using official Google Drive API v3.
Provides direct, headless file uploads with terminal progress display.
"""

import os
import pickle
import io
import subprocess
import platform
from typing import Optional

# CRITICAL: Patch webbrowser BEFORE importing OAuth libraries
# This ensures Edge is used for authentication
import webbrowser

class EdgeController:
    """Custom browser controller for Edge."""
    def open(self, url, new=0, autoraise=True):
        """Open URL in Edge browser."""
        if platform.system() == 'Windows':
            # Try common Edge paths
            edge_paths = [
                r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                r'C:\Program Files\Microsoft\Edge\Application\msedge.exe'
            ]
            
            for edge_path in edge_paths:
                if os.path.exists(edge_path):
                    try:
                        subprocess.Popen([edge_path, url])
                        return True
                    except Exception:
                        continue
        
        # Fallback if specific Edge path fails or non-Windows
        # Try finding 'msedge' or 'edge' in path
        try:
            subprocess.Popen(['msedge', url])
            return True
        except:
            pass
            
        return False

def _edge_browser_getter(using=None):
    """Always return our Edge controller."""
    return EdgeController()

# Apply the patch globally to both open and get
# The library likely calls webbrowser.get().open()
webbrowser.get = _edge_browser_getter
webbrowser.open = EdgeController().open

# Now import OAuth libraries - they will use our patched webbrowser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from utils.logger import logger
from tqdm import tqdm

class GoogleDriveUploader:
    """Upload files to Google Drive using official API."""
    
    # If modifying these scopes, delete the token file
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, credentials_file: str = 'config/credentials.json', 
                 token_file: str = 'config/token.pickle',
                 upload_timeout: int = 3600):
        """
        Initialize Google Drive uploader.
        
        Args:
            credentials_file: Path to OAuth credentials JSON
            token_file: Path to save/load authentication token
            upload_timeout: Maximum seconds to wait for upload (unused, kept for compatibility)
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.upload_timeout = upload_timeout
        self.service = None
        self.creds = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive API using Edge browser.
        
        Returns:
            bool: True if authentication successful
        """
        try:
            # Check if we have saved credentials
            if os.path.exists(self.token_file):
                logger.info("Loading saved credentials...")
                with open(self.token_file, 'rb') as token:
                    self.creds = pickle.load(token)
            
            # If credentials are invalid or don't exist, get new ones
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    logger.info("Refreshing expired credentials...")
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Credentials file not found: {self.credentials_file}")
                        logger.error("Please follow the setup guide to create credentials.json")
                        return False
                    
                    logger.info("Starting OAuth authentication flow...")
                    logger.info("Opening Edge browser for authentication...")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    
                    # Run local server - webbrowser is already patched to use Edge
                    self.creds = flow.run_local_server(
                        port=0,
                        authorization_prompt_message='Please visit this URL to authorize:',
                        success_message='Authentication successful! You can close this window.',
                        open_browser=True
                    )
                
                # Save credentials for next run
                logger.info(f"Saving credentials to {self.token_file}")
                with open(self.token_file, 'wb') as token:
                    pickle.dump(self.creds, token)
            
            # Build the Drive service
            logger.info("Building Google Drive service...")
            self.service = build('drive', 'v3', credentials=self.creds)
            logger.info("✓ Successfully authenticated with Google Drive")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def find_folder(self, folder_name: str, parent_id: str = None) -> Optional[str]:
        """
        Find a folder by name in Google Drive.
        
        Args:
            folder_name: Name of folder to find
            parent_id: Parent folder ID (None for root)
            
        Returns:
            str: Folder ID if found, None otherwise
        """
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            logger.debug(f"Searching for folder: {folder_name}")
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()
            
            items = results.get('files', [])
            if items:
                logger.debug(f"Found folder: {items[0]['name']} (ID: {items[0]['id']})")
                return items[0]['id']
            
            return None
            
        except HttpError as e:
            logger.error(f"Error searching for folder: {e}")
            return None
    
    def create_folder(self, folder_name: str, parent_id: str = None) -> Optional[str]:
        """
        Create a folder in Google Drive.
        
        Args:
            folder_name: Name of folder to create
            parent_id: Parent folder ID (None for root)
            
        Returns:
            str: Created folder ID, None if failed
        """
        try:
            logger.info(f"Creating folder: {folder_name}")
            
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name'
            ).execute()
            
            logger.info(f"✓ Folder created: {folder.get('name')} (ID: {folder.get('id')})")
            return folder.get('id')
            
        except HttpError as e:
            logger.error(f"Error creating folder: {e}")
            return None
    
    def get_or_create_folder(self, folder_name: str) -> Optional[str]:
        """
        Get folder ID, creating it if it doesn't exist.
        
        Args:
            folder_name: Name of folder
            
        Returns:
            str: Folder ID
        """
        # First try to find existing folder
        folder_id = self.find_folder(folder_name)
        
        if folder_id:
            logger.info(f"Found existing folder: {folder_name}")
            return folder_id
        
        # If not found, create it
        logger.info(f"Folder '{folder_name}' not found, creating...")
        return self.create_folder(folder_name)
    
    def upload_file(self, file_path: str, folder_name: Optional[str] = None) -> bool:
        """
        Upload a file to Google Drive with terminal progress display.
        
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
            # Authenticate if not already done
            if not self.service:
                print("\n" + "="*60)
                print("  GOOGLE DRIVE AUTHENTICATION")
                print("="*60 + "\n")
                if not self.authenticate():
                    return False
            
            # Get or create target folder
            folder_id = None
            if folder_name:
                print(f"\n📁 Target folder: {folder_name}")
                folder_id = self.get_or_create_folder(folder_name)
                if not folder_id:
                    logger.error("Failed to access/create target folder")
                    return False
            
            # Prepare file metadata
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            print(f"\n📤 Uploading: {file_name}")
            print(f"📊 Size: {file_size / (1024*1024):.2f} MB")
            
            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Create media upload with resumable support
            media = MediaFileUpload(
                file_path,
                resumable=True,
                chunksize=1024*1024  # 1MB chunks
            )
            
            # Start upload
            logger.info("Starting upload to Google Drive...")
            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            )
            
            # Upload with progress bar
            response = None
            with tqdm(total=100, desc="Uploading to Drive", unit="%", 
                     bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}% [{elapsed}<{remaining}]') as pbar:
                
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        pbar.n = progress
                        pbar.refresh()
            
            # Upload complete
            print("\n" + "="*60)
            print("  ✓ UPLOAD SUCCESSFUL!")
            print("="*60)
            print(f"\n📁 File: {response.get('name')}")
            print(f"🔗 Link: {response.get('webViewLink', 'N/A')}")
            print(f"📍 Location: Google Drive/{folder_name if folder_name else 'My Drive'}")
            print()
            
            logger.info(f"✓ Upload completed: {response.get('name')}")
            logger.info(f"File ID: {response.get('id')}")
            
            return True
            
        except HttpError as e:
            logger.error(f"Google Drive API error: {e}")
            print(f"\n❌ Upload failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            print(f"\n❌ Upload failed: {e}")
            return False
    
    def close(self):
        """Close the uploader (no-op for API, kept for compatibility)."""
        logger.debug("Drive uploader closed")
        # No cleanup needed for API-based implementation
