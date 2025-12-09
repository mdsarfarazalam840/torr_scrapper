"""
Download monitor module for tracking torrent download progress.
"""

from typing import Optional, Callable
import time
from tqdm import tqdm
from utils.logger import logger
from utils.helpers import format_bytes, format_speed, format_time

class DownloadMonitor:
    """Monitor torrent download progress."""
    
    def __init__(self, qb_client, poll_interval: int = 5):
        """
        Initialize download monitor.
        
        Args:
            qb_client: QBittorrentClient instance
            poll_interval: Seconds between status checks
        """
        self.qb_client = qb_client
        self.poll_interval = poll_interval
    
    def monitor_download(self, torrent_hash: str, on_complete: Optional[Callable] = None) -> bool:
        """
        Monitor torrent download until completion.
        
        Args:
            torrent_hash: Torrent hash to monitor
            on_complete: Optional callback when download completes
            
        Returns:
            bool: True if download completed successfully
        """
        logger.info("Starting download monitor")
        
        # Get initial info
        info = self.qb_client.get_torrent_info(torrent_hash)
        if not info:
            logger.error("Failed to get torrent info")
            return False
        
        torrent_name = info['name']
        total_size = info['size']
        
        logger.info(f"Monitoring: {torrent_name}")
        logger.info(f"Size: {format_bytes(total_size)}")
        
        # Initialize progress bar
        with tqdm(total=100, desc="Downloading", unit="%", 
                  bar_format='{l_bar}{bar}| {n:.1f}% [{elapsed}<{remaining}]') as pbar:
            
            last_progress = 0
            
            while True:
                # Get current info
                info = self.qb_client.get_torrent_info(torrent_hash)
                if not info:
                    logger.error("Lost connection to torrent")
                    return False
                
                progress = info['progress'] * 100
                state = info['state']
                dl_speed = info['download_speed']
                up_speed = info['upload_speed']
                eta = info['eta']
                seeds = info['seeds']
                peers = info['peers']
                downloaded = info['downloaded']
                
                # Update progress bar
                progress_delta = progress - last_progress
                if progress_delta > 0:
                    pbar.update(progress_delta)
                    last_progress = progress
                
                # Update description with stats
                speed_str = format_speed(dl_speed) if dl_speed > 0 else "0 B/s"
                eta_str = format_time(eta) if eta > 0 else "Unknown"
                
                pbar.set_postfix_str(
                    f"⬇ {speed_str} | ⬆ {format_speed(up_speed)} | "
                    f"Seeds: {seeds} | Peers: {peers} | ETA: {eta_str}"
                )
                
                # Check if complete
                if self.qb_client.is_complete(torrent_hash):
                    pbar.n = 100
                    pbar.refresh()
                    logger.info(f"✓ Download complete: {torrent_name}")
                    
                    if on_complete:
                        on_complete(info)
                    
                    return True
                
                # Check for errors
                if state == 'error':
                    logger.error(f"Download error for: {torrent_name}")
                    return False
                
                if state == 'missingFiles':
                    logger.error(f"Missing files for: {torrent_name}")
                    return False
                
                # Wait before next poll
                time.sleep(self.poll_interval)
        
        return False
    
    def get_status_summary(self, torrent_hash: str) -> Optional[str]:
        """
        Get a formatted status summary.
        
        Args:
            torrent_hash: Torrent hash
            
        Returns:
            str: Formatted status string
        """
        info = self.qb_client.get_torrent_info(torrent_hash)
        if not info:
            return None
        
        summary = f"""
╔══════════════════════════════════════════════════════════════
║ Torrent: {info['name']}
╠══════════════════════════════════════════════════════════════
║ Progress: {info['progress']*100:.1f}%
║ State: {info['state']}
║ Size: {format_bytes(info['size'])}
║ Downloaded: {format_bytes(info['downloaded'])}
║ Download Speed: {format_speed(info['download_speed'])}
║ Upload Speed: {format_speed(info['upload_speed'])}
║ ETA: {format_time(info['eta'])}
║ Seeds: {info['seeds']} | Peers: {info['peers']}
║ Save Path: {info['save_path']}
╚══════════════════════════════════════════════════════════════
"""
        return summary
