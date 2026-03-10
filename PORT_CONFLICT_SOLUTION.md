# Permanent Fix for Port 8000 Conflict

## Problem
Two projects competing for port 8000:
- Liases Foras (this project)
- REGULUS (/regulus/backend)

## Solution Options

### Option 1: Use Different Ports (RECOMMENDED)
**Liases Foras:** Keep port 8000
**REGULUS:** Change to port 8001

In REGULUS project, update backend startup:
```bash
cd ~/Documents/Projects/regulus/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Option 2: Kill REGULUS Auto-Start
Find and disable the auto-start script:
```bash
# Check for tmux sessions
tmux ls

# Check for screen sessions
screen -ls

# Check for startup scripts
cat ~/.bashrc | grep uvicorn
cat ~/.zshrc | grep uvicorn
```

### Option 3: Use Process Manager (BEST for Production)
Install PM2:
```bash
npm install -g pm2

# Liases Foras
cd ~/Documents/Projects/liases-foras
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8000" --name liases-foras

# REGULUS
cd ~/Documents/Projects/regulus/backend
pm2 start "uvicorn app.main:app --host 0.0.0.0 --port 8001" --name regulus

# Save configuration
pm2 save
pm2 startup
```

## Quick Fix (When It Happens Again)
```bash
# Kill all uvicorn processes
pkill -f uvicorn

# Start Liases Foras backend
cd ~/Documents/Projects/liases-foras
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
```
