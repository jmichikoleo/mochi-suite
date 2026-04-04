# Deploy Mochi's Assistant to PythonAnywhere (Free, No Card)

## What You Get
- App running 24/7 at `https://YOURUSERNAME.pythonanywhere.com`
- Free tier: 512MB RAM, 100 seconds CPU/day (plenty for personal use)
- Daily scheduled tasks (for email digest)
- No credit card needed
- Your data persists on their servers

## Step 1: Create Account

1. Go to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Click **"Start running Python online in less than a minute!"**
3. Sign up with email (free tier, no card)
4. Note your username — your app will be at `https://USERNAME.pythonanywhere.com`

## Step 2: Upload Your App

### Option A: Via Git (recommended)
1. Push your app to a private GitHub repo first:
   ```bash
   cd ~/Desktop/claudecode/mochis-assistant
   git init
   git add -A
   git commit -m "Initial commit"
   gh repo create mochis-assistant --private --push
   ```

2. On PythonAnywhere, open a **Bash console** and run:
   ```bash
   git clone https://github.com/YOURUSERNAME/mochis-assistant.git
   ```

### Option B: Via File Upload
1. On PythonAnywhere, go to **Files** tab
2. Create folder: `mochis-assistant`
3. Zip your project locally:
   ```bash
   cd ~/Desktop/claudecode
   zip -r mochis-assistant.zip mochis-assistant/ -x "*.pyc" "*__pycache__*" "*.git*"
   ```
4. Upload the zip via the Files tab
5. Open a Bash console and unzip:
   ```bash
   cd ~
   unzip mochis-assistant.zip
   ```

## Step 3: Install Dependencies

In the PythonAnywhere **Bash console**:
```bash
cd ~/mochis-assistant
pip3 install --user -r requirements.txt
```

## Step 4: Set Up the Web App

1. Go to the **Web** tab
2. Click **"Add a new web app"**
3. Choose **Manual configuration** → **Python 3.10**
4. Set the **Source code** directory to: `/home/USERNAME/mochis-assistant`
5. Edit the **WSGI configuration file** — replace ALL contents with:

```python
import sys
import os

project_home = '/home/USERNAME/mochis-assistant'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.chdir(project_home)

from src.app import app as application
```

6. Click **Reload** (the green button)

## Step 5: Set Up Static Files (for PDF uploads etc.)

On the **Web** tab, under **Static files**, add:
- URL: `/files/uploads/`  → Directory: `/home/USERNAME/mochis-assistant/data/uploads`
- URL: `/files/lab/`  → Directory: `/home/USERNAME/mochis-assistant/data/lab/pdfs`
- URL: `/files/uni/`  → Directory: `/home/USERNAME/mochis-assistant/data/uni/files`

## Step 6: Set Up Daily Email Digest

1. Go to the **Tasks** tab
2. Add a **Scheduled task**:
   - Time: `21:00` UTC (= 6:00 AM KST)
   - Command: `cd /home/USERNAME/mochis-assistant && python3 src/send_digest.py`
3. Click **Create**

This runs every day at 6am KST and sends your email digest!

## Step 7: Visit Your App!

Open: `https://USERNAME.pythonanywhere.com`

It's live! Access from your phone, tablet, any device, 24/7.

## Updating Your App

When you make changes locally:

### If using Git:
```bash
# On your Mac
cd ~/Desktop/claudecode/mochis-assistant
git add -A && git commit -m "Updates" && git push

# On PythonAnywhere Bash console
cd ~/mochis-assistant && git pull
```
Then click **Reload** on the Web tab.

### If using file upload:
Re-upload changed files via the Files tab, then click **Reload**.

## Important Notes

- **Free tier limits**: 100 seconds CPU/day, but Mochi's Assistant is lightweight so this is fine
- **File storage**: Your data/ folder persists on PythonAnywhere's servers
- **HTTPS**: Included free at `https://USERNAME.pythonanywhere.com`
- **Custom domain**: Available on paid plans ($5/month) if you want `mochi.yourdomain.com`
- **Whitelist**: Free tier can only access a whitelist of external sites. ArXiv, OpenAI, and most RSS feeds are whitelisted. If something doesn't work, check the whitelist page.
