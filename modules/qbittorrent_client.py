"""
qBittorrent Web API client for managing torrent downloads.
"""

import qbittorrentapi
from typing import Optional, Dict
from utils.logger import logger
import time

class QBittorrentClient:
    """Client for qBittorrent Web API."""
    
    def __init__(self, host: str = 'localhost', port: int = 8080, 
                 username: str = 'admin', password: str = 'adminadmin'):
        """
        Initialize qBittorrent client.
        
        Args:
            host: qBittorrent host
            port: qBittorrent Web UI port
            username: Web UI username
            password: Web UI password
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
    
    def connect(self) -> bool:
        """
        Connect to qBittorrent Web API.
        
        Returns:
            bool: True if connection successful
        """
        try:
            logger.info(f"Connecting to qBittorrent at {self.host}:{self.port}")
            
            self.client = qbittorrentapi.Client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password
            )
            
            # Test connection
            self.client.auth_log_in()
            version = self.client.app.version
            logger.info(f"Connected to qBittorrent v{version}")
            
            return True
            
        except qbittorrentapi.LoginFailed:
            logger.error("qBittorrent login failed. Check credentials in config.yaml")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to qBittorrent: {e}")
            logger.error("Make sure qBittorrent is running and Web UI is enabled")
            return False
    
    def add_magnet(self, magnet_link: str, save_path: Optional[str] = None) -> Optional[str]:
        """
        Add torrent via magnet link.
        
        Args:
            magnet_link: Magnet URI
            save_path: Custom download path
            
        Returns:
            str: Torrent hash if successful, None otherwise
        """
        if not self.client:
            logger.error("Not connected to qBittorrent")
            return None
        
        try:
            logger.info("Adding magnet link to qBittorrent")
            
            # Add torrent
            self.client.torrents_add(
                urls=magnet_link,
                save_path=save_path
            )
            
            # Wait for torrent to be added and get hash
            time.sleep(2)
            
            # Find the torrent by matching magnet link hash
            import re
            hash_match = re.search(r'btih:([a-fA-F0-9]+)', magnet_link)
            if hash_match:
                torrent_hash = hash_match.group(1).lower()
                
                # Verify torrent was added
                torrents = self.client.torrents_info()
                for torrent in torrents:
                    if torrent.hash.lower() == torrent_hash:
                        logger.info(f"Torrent added successfully: {torrent.name}")
                        return torrent.hash
            
            # Fallback: return the most recently added torrent
            torrents = self.client.torrents_info()
            if torrents:
                latest = max(torrents, key=lambda t: t.added_on)
                logger.info(f"Torrent added: {latest.name}")
                return latest.hash
            
            logger.warning("Torrent added but couldn't retrieve hash")
            return None
            
        except Exception as e:
            logger.error(f"Failed to add magnet link: {e}")
            return None
    
    def get_torrent_info(self, torrent_hash: str) -> Optional[Dict]:
        """
        Get torrent information.
        
        Args:
            torrent_hash: Torrent hash
            
        Returns:
            dict: Torrent information
        """
        if not self.client:
            return None
        
        try:
            torrents = self.client.torrents_info(torrent_hashes=torrent_hash)
            if not torrents:
                return None
            
            torrent = torrents[0]
            
            return {
                'name': torrent.name,
                'hash': torrent.hash,
                'size': torrent.size,
                'progress': torrent.progress,
                'state': torrent.state,
                'download_speed': torrent.dlspeed,
                'upload_speed': torrent.upspeed,
                'eta': torrent.eta,
                'seeds': torrent.num_seeds,
                'peers': torrent.num_leechs,
                'downloaded': torrent.downloaded,
                'save_path': torrent.save_path,
                'completion_date': torrent.completion_on
            }
            
        except Exception as e:
            logger.error(f"Failed to get torrent info: {e}")
            return None
    
    def is_complete(self, torrent_hash: str) -> bool:
        """
        Check if torrent download is complete.
        
        Args:
            torrent_hash: Torrent hash
            
        Returns:
            bool: True if download is complete
        """
        info = self.get_torrent_info(torrent_hash)
        if not info:
            return False
        
        return info['progress'] >= 1.0 and info['state'] in ['pausedUP', 'stalledUP', 'uploading', 'queuedUP']
    
    def get_download_path(self, torrent_hash: str) -> Optional[str]:
        """
        Get the download path for a torrent.
        
        Args:
            torrent_hash: Torrent hash
            
        Returns:
            str: Full path to downloaded content
        """
        info = self.get_torrent_info(torrent_hash)
        if not info:
            return None
        
        import os
        import glob
        
        # First try the exact path from qBittorrent
        exact_path = os.path.join(info['save_path'], info['name'])
        
        if os.path.exists(exact_path):
            logger.debug(f"Found exact path: {exact_path}")
            return exact_path
        
        # If exact path doesn't exist, search for similar folders
        logger.warning(f"Exact path not found: {exact_path}")
        logger.info("Searching for actual download folder...")
        
        save_path = info['save_path']
        torrent_name = info['name']
        
        # List all items in the save directory
        if os.path.exists(save_path):
            items = os.listdir(save_path)
            logger.debug(f"Items in {save_path}: {items}")
            
            # Try to find a folder that matches the torrent name (case-insensitive, partial match)
            # Clean the torrent name by removing/normalizing special characters
            torrent_name_clean = torrent_name.replace('[', '').replace(']', '').lower()
            
            best_match = None
            best_match_score = 0
            
            for item in items:
                item_path = os.path.join(save_path, item)
                item_clean = item.replace('[', '').replace(']', '').lower()
                
                # Calculate match score (how many words match)
                torrent_words = set(torrent_name_clean.split())
                item_words = set(item_clean.split())
                
                if len(torrent_words) > 0:
                    match_score = len(torrent_words & item_words) / len(torrent_words)
                    
                    if match_score > best_match_score and match_score > 0.5:  # At least 50% word match
                        best_match_score = match_score
                        best_match = item_path
            
            if best_match:
                logger.info(f"Found likely match: {best_match} (match score: {best_match_score:.0%})")
                return best_match
            
            # If still not found, return the most recently modified item in the directory
            # This is likely the just-downloaded torrent
            if items:
                latest_item = max(
                    [os.path.join(save_path, item) for item in items],
                    key=os.path.getmtime
                )
                logger.warning(f"Using most recent item: {latest_item}")
                return latest_item
        
        # Fallback to the original path even if it doesn't exist
        logger.error(f"Could not find download path, returning reported path: {exact_path}")
        return exact_path
    
    def pause_torrent(self, torrent_hash: str) -> bool:
        """Pause a torrent."""
        try:
            self.client.torrents_pause(torrent_hashes=torrent_hash)
            logger.info("Torrent paused")
            return True
        except Exception as e:
            logger.error(f"Failed to pause torrent: {e}")
            return False
    
    def resume_torrent(self, torrent_hash: str) -> bool:
        """Resume a torrent."""
        try:
            self.client.torrents_resume(torrent_hashes=torrent_hash)
            logger.info("Torrent resumed")
            return True
        except Exception as e:
            logger.error(f"Failed to resume torrent: {e}")
            return False
    
    def remove_torrent(self, torrent_hash: str, delete_files: bool = False) -> bool:
        """Remove a torrent."""
        try:
            self.client.torrents_delete(
                delete_files=delete_files,
                torrent_hashes=torrent_hash
            )
            logger.info(f"Torrent removed (files deleted: {delete_files})")
            return True
        except Exception as e:
            logger.error(f"Failed to remove torrent: {e}")
            return False
