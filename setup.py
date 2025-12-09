"""
Setup script to verify prerequisites and environment setup.
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ Python 3.8+ required")
        return False
    return True

def check_qbittorrent():
    """Check if qBittorrent is accessible."""
    import requests
    
    try:
        response = requests.get('http://localhost:8080', timeout=5)
        print("✓ qBittorrent Web UI is accessible")
        return True
    except:
        print("✗ qBittorrent Web UI not accessible")
        print("  Please ensure qBittorrent is running and Web UI is enabled")
        print("  (Tools → Options → Web UI)")
        return False

def check_archiver():
    """Check for WinRAR or 7-Zip."""
    winrar_path = r"C:\Program Files\WinRAR\WinRAR.exe"
    sevenzip_path = r"C:\Program Files\7-Zip\7z.exe"
    
    if os.path.exists(winrar_path):
        print(f"✓ WinRAR found: {winrar_path}")
        return True
    elif os.path.exists(sevenzip_path):
        print(f"✓ 7-Zip found: {sevenzip_path}")
        return True
    else:
        print("✗ No archiver found (WinRAR or 7-Zip)")
        print("  Please install WinRAR or 7-Zip")
        return False

def check_config():
    """Check if configuration file exists."""
    if os.path.exists('config/config.yaml'):
        print("✓ Configuration file found")
        return True
    else:
        print("✗ Configuration file not found")
        return False

def install_dependencies():
    """Install Python dependencies."""
    print("\nInstalling Python dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ Dependencies installed successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def main():
    """Run setup checks."""
    print("=" * 60)
    print(" TORRENT AUTOMATION SYSTEM - SETUP VERIFICATION")
    print("=" * 60)
    print()
    
    checks = []
    
    print("Checking prerequisites...")
    print()
    
    checks.append(check_python_version())
    checks.append(check_config())
    checks.append(check_qbittorrent())
    checks.append(check_archiver())
    
    print()
    
    if not all(checks):
        print("\n⚠ Some prerequisites are missing. Please fix the issues above.")
        print()
        
        install_deps = input("Do you want to install Python dependencies anyway? (y/n): ").strip().lower()
        if install_deps == 'y':
            install_dependencies()
    else:
        print("✓ All prerequisites verified!")
        print()
        
        install_deps = input("Install/update Python dependencies? (y/n): ").strip().lower()
        if install_deps == 'y':
            install_dependencies()
    
    print()
    print("=" * 60)
    print()
    print("Setup complete!")
    print()
    print("To run the automation:")
    print("  python main.py")
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()
