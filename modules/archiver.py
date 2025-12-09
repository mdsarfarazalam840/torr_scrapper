"""
Archiver module for creating RAR archives from downloaded files.
"""

import os
import subprocess
import shutil
from typing import Optional
from utils.logger import logger
from utils.helpers import format_bytes, validate_path
from tqdm import tqdm
import time

class Archiver:
    """Create RAR archives using WinRAR or 7-Zip."""
    
    def __init__(self, winrar_path: Optional[str] = None, 
                 sevenzip_path: Optional[str] = None,
                 compression_level: int = 3):
        """
        Initialize archiver.
        
        Args:
            winrar_path: Path to WinRAR.exe
            sevenzip_path: Path to 7z.exe
            compression_level: Compression level (0-5)
        """
        self.winrar_path = winrar_path
        self.sevenzip_path = sevenzip_path
        self.compression_level = compression_level
        self.archiver_type = None
        
        # Detect available archiver
        self._detect_archiver()
    
    def _detect_archiver(self):
        """Detect which archiver is available."""
        # Try WinRAR first
        if self.winrar_path and os.path.exists(self.winrar_path):
            self.archiver_type = 'winrar'
            logger.info(f"Using WinRAR: {self.winrar_path}")
            return
        
        # Try 7-Zip
        if self.sevenzip_path and os.path.exists(self.sevenzip_path):
            self.archiver_type = '7zip'
            logger.info(f"Using 7-Zip: {self.sevenzip_path}")
            return
        
        # Try common installation paths
        common_winrar = r"C:\Program Files\WinRAR\WinRAR.exe"
        common_7zip = r"C:\Program Files\7-Zip\7z.exe"
        
        if os.path.exists(common_winrar):
            self.winrar_path = common_winrar
            self.archiver_type = 'winrar'
            logger.info(f"Found WinRAR: {common_winrar}")
            return
        
        if os.path.exists(common_7zip):
            self.sevenzip_path = common_7zip
            self.archiver_type = '7zip'
            logger.info(f"Found 7-Zip: {common_7zip}")
            return
        
        logger.error("No archiver found. Please install WinRAR or 7-Zip")
    
    def create_rar(self, source_path: str, output_path: Optional[str] = None, 
                   archive_name: Optional[str] = None) -> Optional[str]:
        """
        Create RAR archive from source file or directory.
        
        Args:
            source_path: Path to file or directory to archive
            output_path: Directory where archive will be created
            archive_name: Name of the archive (without extension)
            
        Returns:
            str: Path to created archive, None if failed
        """
        if not self.archiver_type:
            logger.error("No archiver available")
            return None
        
        if not os.path.exists(source_path):
            logger.error(f"Source path does not exist: {source_path}")
            return None
        
        # Determine output path and archive name
        if not output_path:
            output_path = os.path.dirname(source_path)
        
        if not archive_name:
            archive_name = os.path.basename(source_path)
        
        # Ensure output directory exists
        validate_path(output_path, create_if_missing=True)
        
        # Create archive path
        if self.archiver_type == 'winrar':
            archive_path = os.path.join(output_path, f"{archive_name}.rar")
        else:  # 7zip
            archive_path = os.path.join(output_path, f"{archive_name}.7z")
        
        logger.info(f"Creating archive: {archive_path}")
        logger.info(f"Source: {source_path}")
        
        # Get source size for progress estimation
        source_size = self._get_size(source_path)
        logger.info(f"Source size: {format_bytes(source_size)}")
        
        # Create archive
        success = False
        if self.archiver_type == 'winrar':
            success = self._create_with_winrar(source_path, archive_path)
        else:
            success = self._create_with_7zip(source_path, archive_path)
        
        if success and os.path.exists(archive_path):
            archive_size = os.path.getsize(archive_path)
            logger.info(f"✓ Archive created: {archive_path}")
            logger.info(f"Archive size: {format_bytes(archive_size)}")
            logger.info(f"Compression ratio: {(1 - archive_size/source_size)*100:.1f}%")
            return archive_path
        else:
            logger.error("Failed to create archive")
            return None
    
    def _create_with_winrar(self, source: str, output: str) -> bool:
        """Create archive using WinRAR."""
        try:
            # WinRAR command line arguments
            # a = add to archive
            # -m{0-5} = compression level
            # -ep1 = exclude base folder from paths
            # -r = recurse subdirectories
            # -y = assume yes on all queries
            
            cmd = [
                self.winrar_path,
                'a',  # Add
                f'-m{self.compression_level}',  # Compression level
                '-r',  # Recursive
                '-y',  # Assume yes
                output,
                source
            ]
            
            logger.debug(f"Running: {' '.join(cmd)}")
            
            # Run with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor process with progress bar
            with tqdm(total=100, desc="Archiving", unit="%") as pbar:
                while process.poll() is None:
                    time.sleep(0.5)
                    if os.path.exists(output):
                        # Estimate progress based on file size (rough estimate)
                        current_size = os.path.getsize(output)
                        pbar.update(1)
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                logger.info("WinRAR archiving completed successfully")
                return True
            else:
                logger.error(f"WinRAR error: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"WinRAR failed: {e}")
            return False
    
    def _create_with_7zip(self, source: str, output: str) -> bool:
        """Create archive using 7-Zip."""
        try:
            # 7-Zip command line arguments
            # a = add
            # -t7z = 7z format
            # -mx{0-9} = compression level
            
            # Map our 0-5 scale to 7-zip's 0-9 scale
            mx_level = min(self.compression_level * 2, 9)
            
            cmd = [
                self.sevenzip_path,
                'a',  # Add
                f'-mx={mx_level}',  # Compression level
                '-y',  # Assume yes
                output,
                source
            ]
            
            logger.debug(f"Running: {' '.join(cmd)}")
            
            # Run with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor process
            with tqdm(total=100, desc="Archiving", unit="%") as pbar:
                while process.poll() is None:
                    time.sleep(0.5)
                    if os.path.exists(output):
                        pbar.update(1)
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                logger.info("7-Zip archiving completed successfully")
                return True
            else:
                logger.error(f"7-Zip error: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"7-Zip failed: {e}")
            return False
    
    def _get_size(self, path: str) -> int:
        """Get total size of file or directory."""
        if os.path.isfile(path):
            return os.path.getsize(path)
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass
        
        return total_size
    
    def verify_archive(self, archive_path: str) -> bool:
        """
        Verify archive integrity.
        
        Args:
            archive_path: Path to archive file
            
        Returns:
            bool: True if archive is valid
        """
        if not os.path.exists(archive_path):
            return False
        
        try:
            if self.archiver_type == 'winrar':
                cmd = [self.winrar_path, 't', archive_path]
            else:
                cmd = [self.sevenzip_path, 't', archive_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to verify archive: {e}")
            return False
