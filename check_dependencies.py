"""
Dependency checker - ensures all required packages are installed before running main script.
"""

import subprocess
import sys
import os

def check_and_install_requirements():
    """Check if requirements are satisfied, install if missing."""
    
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    
    if not os.path.exists(requirements_file):
        print("⚠️  requirements.txt not found, skipping dependency check")
        return True
    
    print("🔍 Checking dependencies...")
    
    try:
        # Try importing key packages to see if they're installed
        import qbittorrentapi
        import selenium
        import undetected_chromedriver
        import bs4
        import yaml
        import colorama
        import tqdm
        import google.auth
        import googleapiclient
        
        print("✓ All dependencies satisfied\n")
        return True
        
    except ImportError as e:
        print(f"⚠️  Missing dependency detected: {e.name if hasattr(e, 'name') else 'unknown'}")
        print("📦 Installing missing dependencies from requirements.txt...\n")
        
        try:
            # Install requirements
            subprocess.check_call([
                sys.executable, 
                '-m', 
                'pip', 
                'install', 
                '-r', 
                requirements_file,
                '--quiet'
            ])
            
            print("\n✓ Dependencies installed successfully!\n")
            return True
            
        except subprocess.CalledProcessError as install_error:
            print(f"\n❌ Failed to install dependencies: {install_error}")
            print("Please run manually: pip install -r requirements.txt")
            return False

if __name__ == "__main__":
    # This can be used to check dependencies standalone
    if check_and_install_requirements():
        print("✓ All dependencies are ready!")
        sys.exit(0)
    else:
        print("❌ Dependency check failed!")
        sys.exit(1)
