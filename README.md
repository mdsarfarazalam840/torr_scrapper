# Torrent Automation System

A production-ready, full-cycle automation tool designed to streamline the process of finding, downloading, archiving, and cloud-hosting torrent files. This system handles the entire pipeline—from scraping torrent sites to uploading the final archive to Google Drive—without user intervention in Automatic Mode.

## 🚀 Key Features

*   **Multi-Site Intelligence**: Automatically detects and adapts to different torrent site structures (Primary support: `1337x`, `RARBG` variants).
*   **Stealth Scraping**:
    *   **Cloudflare Bypass**: Utilizes `undetected-chromedriver` to navigate anti-bot protections.
    *   **Headless Operation**: Runs invisibly in the background (no popping windows).
    *   **Ad-Blocker**: Injects aggressive CSS/JS to strip ads and trackers for faster performance.
*   **Flexible Search & Sort**:
    *   **Server-Side Sorting**: Enforces strict sorting (e.g., by Seeders) via URL parameters to get the best results.
    *   **Client-Side Filtering**: Local sorting options for Size, Upload Time, and Uploader name.
*   **Robust Workflow**:
    *   **Auto-Resume**: Handles network interruptions and page load failures with smart retries.
    *   **Dynamic Categories**: Fetches current categories directly from the site (no hardcoded lists).
*   **End-to-End Pipeline**:
    *   **qBittorrent Integration**: Seamlessly adds magnets and monitors download progress.
    *   **Auto-Archiving**: Compresses downloads into `.rar` archives using WinRAR or 7-Zip.
    *   **Cloud Upload**: Automates Google Drive uploads to specific folders.

---

## 📂 Project Structure

Organized for production and maintainability:

```text
Automation/
├── main.py                     # 🚀 Entry Point: Orchestrates the entire workflow
├── config/                     # ⚙️ Configuration
│   └── config.yaml             #    - Credentials, paths, and preferences
├── modules/                    # 🧠 Core Logic Modules
│   ├── scraper.py              #    - Intelligent web scraper (Cloudflare/Site logic)
│   ├── qbittorrent_client.py   #    - API client for qBittorrent Web UI
│   ├── download_monitor.py     #    - Real-time download tracking and speed monitoring
│   ├── archiver.py             #    - Wrapper for WinRAR/7-Zip CLI
│   └── drive_uploader.py       #    - Selenium-based Google Drive uploader
├── tests/                      # 🧪 Unit & Integration Tests
│   └── test_*.py               #    - Tests for browser, connectivity, and logic
├── utils/                      # 🛠️ Utilities
│   ├── logger.py               #    - Centralized colored logging
│   └── helpers.py              #    - Path validation, formatting tools
├── logs/                       # 📝 Runtime Logs
├── debug_artifacts/            # 🐞 Debug Dumps (HTML snapshots of failed pages)
└── requirements.txt            # 📦 Dependencies
```

---

## 🔄 Workflow & Architecture

The system operates in a sequential pipeline. Here is how data flows through the files:

### 1. Initialization Phase (`main.py`)
*   **Trigger**: User runs `python main.py`.
*   **Process**:
    *   Validates environment (Python version, dependencies).
    *   Prompts user for:
        *   **Target Website** (e.g., `https://x1337x.cc`).
        *   **Browser Engine** (Chrome/Edge/Firefox).
        *   **Mode** (Automatic "I'm Feeling Lucky" vs. Manual Selection).
    *   Initializes the `TorrentAutomation` class.

### 2. Discovery Phase (`modules/scraper.py`)
*   **Trigger**: `automation.search_torrents()`
*   **Process**:
    *   **Site Detection**: Analyzes URL to choose parsing strategy (`_detect_site_type`).
    *   **Browser Spin-up**: Launches headless browser with special flags to evade detection.
    *   **Category Fetch**: Scrapes the sidebar/navbar for live categories.
    *   **Search/Browse**:
        *   Constructs optimized URLs (e.g., adding `?order=seeders&by=DESC` for RARBG).
        *   Executes search or fetches "Trending".
        *   Parses HTML tables using `BeautifulSoup`.
    *   **Fail-Safe**: If a table isn't found, dumps the HTML to `debug_artifacts/` for analysis.

### 3. Selection Phase
*   **Manual**: Presents a CLI table of results. User selects ID.
*   **Automatic**: System picks the result with highest seed count/newest date.
*   **Detail Extraction**: Scraper visits the specific torrent page to extract the **Magnet Link**.

### 4. Download Phase (`modules/qbittorrent_client.py`)
*   **Trigger**: `automation.download_torrent()`
*   **Process**:
    *   Connects to `http://localhost:8080` (qBittorrent Web UI).
    *   Pushes Magnet Link.
    *   **Monitor** (`modules/download_monitor.py`): Polls API every few seconds to show a progress bar, speed, and ETA until "Completed".

### 5. Archival Phase (`modules/archiver.py`)
*   **Trigger**: `automation.create_archive()`
*   **Process**:
    *   Locates downloaded files.
    *   Constructs a CLI command for WinRAR or 7-Zip.
    *   Compresses content into a `.rar` file in the `Archive` directory.

### 6. Cloud Upload Phase (`modules/drive_uploader.py`)
*   **Trigger**: `automation.upload_to_drive()`
*   **Process**:
    *   Uses browser automation to log into Google Drive (uses saved session `user-data`).
    *   Navigates to specified folder (e.g., "Torrents").
    *   Uploads the created archive.

---

## 🛠️ Troubleshooting & Fixes

We have extensively battle-tested this script. Here is a history of resolved issues:

| Issue | Root Cause | Fix Implementation |
|-------|------------|--------------------|
| **"No Torrents Found"** | 1337x and RARBG change HTML classes frequently (e.g., `lista2` vs `lista2t`). | **Dynamic Selectors**: Added multiple fallback CSS selectors in `scraper.py` to try different table classes. Added HTML dumping to `debug_artifacts` to analyze failures. |
| **Cloudflare Loops** | Standard Selenium `webdriver` is easily detected. | **Undetected-Chromedriver**: Switched core engine to `uc` which patches the driver binary to look like a human user. |
| **Sorting Not Working** | Some sites ignore URL params or require clicking link headers. | **Hybrid Sorting**: For RARBG, we inject params (`order=seeders`). For 1337x, we try clicking "Time" element or fallback to client-side Python sorting. |
| **"Handle Invalid" Error** | Windows process cleanup timing. | **Graceful Cleanup**: Added `try/except` blocks in `__del__` methods to suppress harmless Windows OS errors during browser shutdown. |
| **Headless Detection** | Sites behave differently when `headless=True`. | **New Headless Mode**: Updated to `--headless=new` and added user-agent spoofing to perfectly mimic a visible browser. |

---

## ⚙️ Installation & Usage

### Prerequisites
*   Python 3.8+
*   qBittorrent (Web UI enabled at port 8080)
*   WinRAR or 7-Zip installed
*   Chrome / Edge browser (for scraping mechanism)

### Quick Start

1.  **Clone & Setup**:
    ```powershell
    git clone https://github.com/your/repo.git
    cd Automation
    pip install -r requirements.txt
    ```

2.  **Configure**:
    Edit `config/config.yaml` with your paths:
    ```yaml
    paths:
      download_dir: "D:/Downloads"
      archive_dir: "D:/Archive"
    ```

3.  **Run**:
    ```powershell
    python main.py
    ```
    Follow the prompts to select your site and mode!

---

*Verified for Production Use - Dec 2025*
