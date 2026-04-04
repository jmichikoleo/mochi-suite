# Deploying Mochi's Assistant to Oracle Cloud (Free Forever)

## What You Get
- App running 24/7 at `http://YOUR_IP:5050`
- Daily 6am email digest sends automatically (even when laptop is off)
- Access from any device (phone, tablet, any computer)
- 1GB RAM free-tier VM (more than enough for this app)

## Step 1: Create Oracle Cloud Account

1. Go to [cloud.oracle.com](https://cloud.oracle.com) and sign up (free)
2. You'll need a credit card for verification but it won't be charged
3. Choose your home region (closest to Busan: **AP Tokyo** or **AP Seoul**)

## Step 2: Create a Free VM

1. Go to **Compute → Instances → Create Instance**
2. Settings:
   - Name: `mochi-assistant`
   - Image: **Ubuntu 22.04** (Canonical)
   - Shape: **VM.Standard.E2.1.Micro** (Always Free)
   - Add your SSH key (generate one if you don't have: `ssh-keygen -t rsa`)
3. Click **Create**
4. Note the **Public IP** once it's running

## Step 3: Open Port 5050

1. Go to **Networking → Virtual Cloud Networks** → click your VCN
2. Click **Security Lists** → **Default Security List**
3. **Add Ingress Rule**:
   - Source CIDR: `0.0.0.0/0`
   - Destination Port: `5050`
   - Protocol: TCP
4. Save

Also on the VM itself:
```bash
sudo iptables -I INPUT -p tcp --dport 5050 -j ACCEPT
sudo netfilter-persistent save
```

## Step 4: Upload Your App

From your Mac terminal:
```bash
# Upload the entire project to your server
scp -r ~/Desktop/claudecode/mochis-assistant ubuntu@YOUR_IP:~/mochis-assistant
```

## Step 5: Install and Run on Server

SSH into your server:
```bash
ssh ubuntu@YOUR_IP
```

Then:
```bash
# Install Python and pip
sudo apt update && sudo apt install -y python3-pip

# Go to app directory
cd ~/mochis-assistant

# Install dependencies
pip3 install -r requirements.txt gunicorn

# Test it works
python3 -c "from src.app import app; print('OK')"

# Run with gunicorn (production server)
gunicorn --bind 0.0.0.0:5050 --workers 2 --timeout 120 --daemon src.app:app

# Check it's running
curl http://localhost:5050/
```

Now open `http://YOUR_IP:5050` in your browser — Mochi should be running!

## Step 6: Keep it Running (auto-start on reboot)

```bash
# Create a systemd service
sudo tee /etc/systemd/system/mochi.service << 'EOF'
[Unit]
Description=Mochi's Assistant
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/mochis-assistant
ExecStart=/usr/bin/gunicorn --bind 0.0.0.0:5050 --workers 2 --timeout 120 src.app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable mochi
sudo systemctl start mochi
sudo systemctl status mochi
```

## Step 7: Set Up Daily Email Digest (6am KST cron)

```bash
# Add cron job
crontab -e

# Add this line (6am KST = 9pm UTC):
0 21 * * * cd /home/ubuntu/mochis-assistant && /usr/bin/python3 src/send_digest.py >> /var/log/mochi-digest.log 2>&1
```

## Step 8: (Optional) Add HTTPS with a Domain

If you want `https://mochi.yourdomain.com`:

```bash
# Install nginx and certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# Point your domain to YOUR_IP in DNS settings
# Then:
sudo certbot --nginx -d mochi.yourdomain.com
```

Nginx config (`/etc/nginx/sites-available/mochi`):
```nginx
server {
    listen 80;
    server_name mochi.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }
}
```

## Updating the App

When you make changes locally:
```bash
# From your Mac
scp -r ~/Desktop/claudecode/mochis-assistant ubuntu@YOUR_IP:~/mochis-assistant

# On the server
ssh ubuntu@YOUR_IP
sudo systemctl restart mochi
```

## Troubleshooting

```bash
# Check if app is running
sudo systemctl status mochi

# Check logs
sudo journalctl -u mochi -f

# Check email digest logs
cat /var/log/mochi-digest.log

# Restart
sudo systemctl restart mochi
```
