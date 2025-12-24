# Google Drive API Setup Guide

This guide will help you set up Google Drive API access for automated file uploads.

## Overview

The automation uses **Google Drive API v3** for direct, headless uploads. You need to:
1. Create a Google Cloud project (free)
2. Enable Drive API
3. Create OAuth credentials
4. Download credentials file

**Time required**: ~5 minutes  
**Cost**: Free

---

## Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Enter project name: `Torrent Automation` (or any name)
4. Click **"Create"**

### 2. Enable Google Drive API

1. In the Cloud Console, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Drive API"**
3. Click on it and press **"Enable"**

### 3. Create OAuth Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. If prompted, configure the **OAuth consent screen**:
   - User Type: **External** (select this)
   - App name: `Torrent Automation`
   - User support email: your email
   - Developer contact: your email
   - Click **"Save and Continue"** through all steps
   
4. Back on Credentials page, click **"Create Credentials"** → **"OAuth client ID"** again:
   - Application type: **Desktop app**
   - Name: `Torrent Uploader`
   - Click **"Create"**

### 4. Download Credentials

1. After creating, a dialog shows your client ID and secret
2. Click **"Download JSON"**
3. Save the file as `credentials.json`
4. **Move it to**: `c:\Users\User\Downloads\Automation\config\credentials.json`

---

## First-Time Authentication

The **first time** you run an upload:

1. A browser window will open automatically
2. Sign in to your Google account
3. Click **"Allow"** to grant Drive access
4. You'll see: "The authentication flow has completed"
5. Close the browser

**After this**: All future uploads work completely headless (no browser needed)!

The authentication token is saved to `config/token.pickle` and reused.

---

## File Structure

After setup, your config folder should have:

```
config/
├── config.yaml           (already exists)
├── credentials.json      (you download this)
└── token.pickle         (auto-created after first auth)
```

---

## Verification

Test your setup:

```bash
python -c "from modules.drive_uploader import GoogleDriveUploader; u = GoogleDriveUploader(); u.authenticate()"
```

You should see:
- ✓ Successfully authenticated with Google Drive

---

## Troubleshooting

### "credentials.json not found"
- Make sure you placed `credentials.json` in `config/` folder
- Check the filename is exactly `credentials.json`

### "Access blocked" error
- Go back to OAuth consent screen
- Add your email to "Test users"
- Save and try again

### "Token expired" error
- Delete `config/token.pickle`
- Run authentication again

---

## Security Notes

- ✅ `credentials.json` is safe to keep (it's just OAuth client info)
- ⚠️ `token.pickle` contains your access token - keep it private
- 🔒 Both files are in `.gitignore` (won't be committed to git)

---

## What Happens During Upload

1. **Check authentication** → loads `token.pickle` if it exists
2. **Authenticate if needed** → opens browser once for first-time auth
3. **Find/create folder** → searches Drive for your target folder
4. **Upload file** → direct API upload with progress bar in terminal
5. **Display results** → shows file link and location

All progress is shown in the terminal! 📊
