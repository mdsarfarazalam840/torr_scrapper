# Torrent Automation System

A comprehensive Python automation tool that automates the entire workflow from searching torrents on x1337x.cc to uploading completed downloads to Google Drive.

## Features

- 🔍 **Search Torrents**: Search x1337x.cc with detailed results including seeds, leeches, size, and uploader
- ⬇️ **Automated Downloads**: Add torrents to qBittorrent via magnet links
- 📊 **Progress Monitoring**: Real-time download progress with speed, ETA, and peer information
- 📦 **Auto-Archiving**: Create RAR archives automatically after download completion
- ☁️ **Google Drive Upload**: Automated upload to Google Drive with folder selection
- 🎯 **End-to-End Automation**: Complete hands-free workflow from search to cloud storage

## Prerequisites

### Required Software

1. **Python 3.8+**
   - Download from [python.org](https://www.python.org/downloads/)

2. **qBittorrent with Web UI**
   - Download from [qbittorrent.org](https://www.qbittorrent.org/download.php)
   - Enable Web UI:
     - Open qBittorrent
     - Go to Tools → Options → Web UI
     - Check "Enable the Web User Interface"
     - Set port to 8080 (default)
     - Set username: `admin` and password: `adminadmin` (or update config.yaml)

3. **WinRAR or 7-Zip**
   - WinRAR: [rarlab.com](https://www.rarlab.com/download.htm)
   - 7-Zip: [7-zip.org](https://www.7-zip.org/)

4. **Microsoft Edge Browser**
   - Pre-installed on Windows 10/11
   - Must be logged into Google Drive

## Installation

1. **Clone or download this repository**

2. **Create virtual environment** (recommended):
   ```powershell
   cd c:\Users\kekeb\Downloads\Automation
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure settings**:
   - Edit `config/config.yaml` to match your setup
   - Update paths, qBittorrent credentials, and preferences

## Configuration

Edit `config/config.yaml`:

```yaml
qbittorrent:
  host: localhost
  port: 8080
  username: admin
  password: adminadmin

paths:
  download_dir: "D:/Volume E/Downloads"
  archive_dir: "D:/Volume E/Downloads/Archivers"

rar:
  winrar_path: "C:/Program Files/WinRAR/WinRAR.exe"
  sevenzip_path: "C:/Program Files/7-Zip/7z.exe"
  compression_level: 3

drive:
  default_folder: "Torrents"
  browser: "edge"
```

## Usage

1. **Start qBittorrent** and ensure Web UI is accessible at `http://localhost:8080`

2. **Run the automation tool**:
   ```powershell
   python main.py
   ```

3. **Follow the interactive prompts**:
   - Enter search query
   - Select torrent from results
   - Choose Google Drive folder (or create new)
   - Monitor progress automatically

## Workflow

1. **Search**: Enter keywords to search x1337x.cc
2. **Select**: Choose from results showing seeds, leeches, size
3. **Download**: Magnet link added to qBittorrent automatically
4. **Monitor**: Real-time progress tracking
5. **Archive**: Auto-create RAR file when download completes
6. **Upload**: Automated Google Drive upload
7. **Complete**: File available in your Google Drive

## Troubleshooting

### qBittorrent Connection Failed
- Verify qBittorrent is running
- Check Web UI is enabled (Tools → Options → Web UI)
- Verify credentials in config.yaml match qBittorrent settings
- Test access: http://localhost:8080

### RAR Creation Failed
- Check WinRAR or 7-Zip installation path in config.yaml
- Ensure sufficient disk space
- Verify write permissions for archive directory

### Google Drive Upload Issues
- Ensure Edge browser is logged into Google Drive
- Check internet connection
- Verify folder name exists or enable auto-create in config

### Web Scraping Errors
- x1337x.cc may be down or blocked
- Try using a VPN
- Website structure may have changed (update needed)

## Project Structure

```
Automation/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── config/
│   └── config.yaml        # Configuration file
├── modules/
│   ├── scraper.py         # x1337x.cc web scraper
│   ├── qbittorrent_client.py  # qBittorrent API client
│   ├── download_monitor.py    # Download progress monitor
│   ├── archiver.py        # RAR archive creator
│   └── drive_uploader.py  # Google Drive uploader
├── utils/
│   ├── logger.py          # Logging utility
│   └── helpers.py         # Helper functions
└── logs/                   # Application logs
```

## License

This is a personal automation tool. Use responsibly and respect copyright laws.

## Disclaimer

This tool is for educational purposes. Users are responsible for ensuring their use complies with applicable laws and regulations. The author is not responsible for any misuse of this software.
