# Pairly Deployment Guide

Complete guide for deploying Pairly to production.

## Pre-Deployment Checklist

### 1. Get Bot Token
```bash
# Talk to @BotFather on Telegram
/newbot
# Follow prompts to get your BOT_TOKEN
```

### 2. Get Your Admin ID
```bash
# Talk to @userinfobot on Telegram
# It will reply with your user ID
```

### 3. Enable Telegram Stars Payments
```bash
# Talk to @BotFather
/mybots
# Select your bot
# Bot Settings → Payments
# Enable "Use Telegram Stars"
```

## Local Development

### Setup
```bash
# Clone/create project
mkdir pairly && cd pairly

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials
```

### Run Locally
```bash
# Activate virtual environment
source venv/bin/activate

# Run bot
python main.py
```

### Test
```bash
# Start bot
# Open Telegram and search for your bot
# Click /start
# Test matchmaking with a second account
```

## Railway Deployment

### Method 1: Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Set environment variables
railway variables set BOT_TOKEN="your_token_here"
railway variables set ADMIN_ID="your_id_here"

# Deploy
railway up

# View logs
railway logs
```

### Method 2: GitHub Integration

```bash
# Push code to GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/pairly.git
git push -u origin main

# Go to railway.app
# Click "New Project"
# Select "Deploy from GitHub repo"
# Choose your repository
# Add environment variables:
#   BOT_TOKEN = your_token
#   ADMIN_ID = your_id
# Railway auto-detects Python and deploys
```

### Method 3: Railway Template

```bash
# Click "Deploy on Railway" button (if you create one)
# Or manually:
# 1. Go to railway.app
# 2. New Project → Empty Project
# 3. Add variables
# 4. Connect GitHub repo
# 5. Deploy
```

## Heroku Deployment

### Setup
```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create app
heroku create pairly-bot

# Set environment variables
heroku config:set BOT_TOKEN="your_token"
heroku config:set ADMIN_ID="your_id"
```

### Create Procfile
```bash
# Create Procfile in project root
echo "worker: python main.py" > Procfile
```

### Deploy
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# Scale worker
heroku ps:scale worker=1

# View logs
heroku logs --tail
```

## DigitalOcean / VPS Deployment

### Setup Server
```bash
# SSH into server
ssh root@your_server_ip

# Update system
apt update && apt upgrade -y

# Install Python 3.11
apt install python3.11 python3.11-venv python3-pip -y

# Create user
adduser pairly
usermod -aG sudo pairly
su - pairly
```

### Deploy Application
```bash
# Clone repository
git clone https://github.com/yourusername/pairly.git
cd pairly

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
nano .env
# Paste your credentials
# Save: Ctrl+X, Y, Enter
```

### Create Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/pairly.service
```

```ini
[Unit]
Description=Pairly Telegram Bot
After=network.target

[Service]
Type=simple
User=pairly
WorkingDirectory=/home/pairly/pairly
Environment="PATH=/home/pairly/pairly/venv/bin"
ExecStart=/home/pairly/pairly/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Start Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable pairly

# Start service
sudo systemctl start pairly

# Check status
sudo systemctl status pairly

# View logs
sudo journalctl -u pairly -f
```

## Docker Deployment

### Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### Create docker-compose.yml
```yaml
version: '3.8'

services:
  bot:
    build: .
    env_file: .env
    volumes:
      - ./pairly.db:/app/pairly.db
    restart: unless-stopped
```

### Deploy
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Database Management

### Backup
```bash
# Local backup
cp pairly.db pairly.db.backup

# Remote backup (VPS)
scp user@server:/path/to/pairly.db ./backup-$(date +%Y%m%d).db

# Automated daily backup (cron)
0 2 * * * cp /home/pairly/pairly/pairly.db /home/pairly/backups/pairly-$(date +\%Y\%m\%d).db
```

### Restore
```bash
# Stop bot
systemctl stop pairly

# Restore database
cp pairly.db.backup pairly.db

# Start bot
systemctl start pairly
```

### Migrate to PostgreSQL (Future)
```bash
# Install PostgreSQL adapter
pip install asyncpg

# Update database.py to use PostgreSQL
# Change connection string
# Deploy updated code
```

## Monitoring & Maintenance

### Check Bot Status
```bash
# Railway
railway logs

# Heroku
heroku logs --tail

# VPS
sudo systemctl status pairly
sudo journalctl -u pairly -f
```

### Performance Monitoring
```bash
# Check database size
ls -lh pairly.db

# Check memory usage (VPS)
free -h

# Check CPU usage
top -p $(pgrep -f "python main.py")
```

### Update Bot
```bash
# Pull latest code
git pull

# Restart service
sudo systemctl restart pairly

# Or on Railway
railway up
```

### Clean Up Old Data
```sql
-- Remove old monitored messages (keep 30 days)
DELETE FROM monitored_messages 
WHERE sent_at < datetime('now', '-30 days');

-- Remove expired bans
DELETE FROM bans 
WHERE banned_until < datetime('now');

-- Vacuum database
VACUUM;
```

## Troubleshooting

### Bot Not Responding
```bash
# Check if running
systemctl status pairly

# Check logs
journalctl -u pairly -n 50

# Restart
systemctl restart pairly
```

### Database Locked
```bash
# Check for stale connections
lsof pairly.db

# Kill process
kill -9 <PID>

# Restart bot
systemctl restart pairly
```

### High Memory Usage
```bash
# Check memory
free -h

# Restart bot
systemctl restart pairly

# If persistent, increase swap
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

### Permission Issues
```bash
# Fix ownership
sudo chown -R pairly:pairly /home/pairly/pairly

# Fix permissions
chmod 644 pairly.db
```

## Security Checklist

- [ ] Keep BOT_TOKEN secret
- [ ] Keep ADMIN_ID secret
- [ ] Enable firewall on VPS
- [ ] Use HTTPS for webhooks (if applicable)
- [ ] Regular database backups
- [ ] Monitor logs for abuse
- [ ] Update dependencies regularly
- [ ] Implement rate limiting (future)

## Scaling Checklist

- [ ] Monitor active users
- [ ] Track database size
- [ ] Monitor response times
- [ ] Plan PostgreSQL migration at 10k users
- [ ] Consider Redis for waiting pool at 50k users
- [ ] Plan multi-instance deployment at 100k users

## Support

For deployment issues:
- Check logs first
- Review this guide
- Check Railway/Heroku documentation
- Contact support@pairly.app

---

**Last Updated**: 2025-01-16  
**Deployment Status**: Production-ready
