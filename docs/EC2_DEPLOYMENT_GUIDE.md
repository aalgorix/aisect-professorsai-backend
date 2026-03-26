# 🚀 EC2 DEPLOYMENT GUIDE

**Your Instance:** prof-ai (i-0d995ce818dd8b8dc)  
**IP:** 51.20.109.241  
**Region:** eu-north-1 (Stockholm)  
**Type:** t3.large  
**Cost:** ~$60/month

---

## 📊 EC2 vs EKS COMPARISON

| Feature | EC2 (Current) | EKS (Prepared) |
|---------|---------------|----------------|
| **Cost** | $60/month | $440/month |
| **Setup Time** | 30 minutes | 4-5 hours |
| **Complexity** | Simple | Complex |
| **Scalability** | Manual | Auto-scaling |
| **Capacity** | 500-1K users | 6K+ users |
| **Best For** | Small-medium | Large scale |

**Recommendation:** Start with EC2, migrate to EKS when you need to scale!

---

## 🎯 DEPLOYMENT STEPS

### **STEP 1: Connect to Your Instance**

```bash
# From your Windows machine (PowerShell)
cd C:\path\to\your\keys

# Connect via SSH
ssh -i "my-ai-app-key.pem" ec2-user@51.20.109.241

# If connection refused, try ubuntu user
ssh -i "my-ai-app-key.pem" ubuntu@51.20.109.241
```

**Troubleshooting:**
```powershell
# If permission denied
icacls my-ai-app-key.pem /inheritance:r
icacls my-ai-app-key.pem /grant:r "%username%:R"
```

---

### **STEP 2: Check Current Setup**

```bash
# Once connected, check what's running
docker --version
docker ps
docker-compose ps

# Check app directory
ls -la /home/ec2-user/
ls -la /home/ubuntu/

# Check resources
free -h
df -h
```

---

### **STEP 3: Transfer Files to EC2**

#### **Option A: Using SCP (Recommended)**

From your local Windows machine:

```powershell
# Navigate to your project
cd C:\Users\Lenovo\OneDrive\Documents\profainew\ProfessorAI_0.2_AWS_Ready\Prof_AI

# Transfer entire project (first time)
scp -i "C:\path\to\my-ai-app-key.pem" -r . ec2-user@51.20.109.241:/home/ec2-user/profai/

# Or transfer specific files (updates)
scp -i "C:\path\to\my-ai-app-key.pem" docker-compose-production.yml ec2-user@51.20.109.241:/home/ec2-user/profai/
scp -i "C:\path\to\my-ai-app-key.pem" .env ec2-user@51.20.109.241:/home/ec2-user/profai/
scp -i "C:\path\to\my-ai-app-key.pem" Dockerfile ec2-user@51.20.109.241:/home/ec2-user/profai/
scp -i "C:\path\to\my-ai-app-key.pem" requirements.txt ec2-user@51.20.109.241:/home/ec2-user/profai/

# Transfer the deployment script
scp -i "C:\path\to\my-ai-app-key.pem" deploy-to-ec2.sh ec2-user@51.20.109.241:/home/ec2-user/profai/
```

#### **Option B: Using Git**

If your code is in a Git repository:

```bash
# On EC2 instance
cd /home/ec2-user
git clone https://github.com/yourusername/profai.git
cd profai

# Or update existing
cd /home/ec2-user/profai
git pull origin main
```

#### **Option C: Create Files Directly**

```bash
# SSH into EC2
ssh -i "my-ai-app-key.pem" ec2-user@51.20.109.241

# Create project directory
mkdir -p /home/ec2-user/profai
cd /home/ec2-user/profai

# Create .env file
nano .env
# Paste your environment variables
# Save with Ctrl+O, Enter, Ctrl+X
```

---

### **STEP 4: Set Up Environment Variables**

```bash
# On EC2 instance
cd /home/ec2-user/profai

# Create .env file
cat > .env << 'EOF'
# API Keys
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_KEY_HERE
ELEVENLABS_API_KEY=YOUR_ELEVENLABS_KEY_HERE
DEEPGRAM_API_KEY=YOUR_DEEPGRAM_KEY_HERE
SARVAM_API_KEY=YOUR_SARVAM_KEY_HERE
GROQ_API_KEY=YOUR_GROQ_KEY_HERE

# ChromaDB Cloud
CHROMA_CLOUD_API_KEY=YOUR_CHROMA_CLOUD_KEY_HERE
CHROMA_CLOUD_TENANT=c4f6d066-6b8e-48d1-80d9-25db6a21839e
CHROMA_CLOUD_DATABASE=profai
USE_CHROMA_CLOUD=true

# Redis Labs Cloud
REDIS_URL=rediss://default:YOUR_REDIS_PASSWORD_HERE@redis-10925.crce206.ap-south-1-1.ec2.cloud.redislabs.com:10925
REDIS_PASSWORD=YOUR_REDIS_PASSWORD_HERE

# Neon PostgreSQL
USE_DATABASE=True
DATABASE_URL=postgresql://neondb_owner:YOUR_NEON_DB_PASSWORD_HERE@ep-still-cake-adz101ej-pooler.c-2.us-east-1.aws.neon.tech/prof_AI?sslmode=require&channel_binding=require

# Server
HOST=0.0.0.0
PORT=5001
DEBUG=False
EOF

# Verify
cat .env
```

---

### **STEP 5: Deploy with Script (Easiest)**

```bash
# Make script executable
chmod +x deploy-to-ec2.sh

# Run deployment
./deploy-to-ec2.sh

# Watch the magic happen! ✨
```

---

### **STEP 6: Manual Deployment (Alternative)**

```bash
# Stop old containers
docker-compose -f docker-compose-production.yml down

# Build image
docker-compose -f docker-compose-production.yml build

# Start services
docker-compose -f docker-compose-production.yml up -d

# Check status
docker-compose -f docker-compose-production.yml ps

# View logs
docker-compose -f docker-compose-production.yml logs -f
```

---

### **STEP 7: Configure Security Group**

1. Go to **AWS Console → EC2 → Instances**
2. Select your instance: **prof-ai**
3. Click **Security** tab
4. Click on the **Security Group** (e.g., launch-wizard-1)
5. Click **Edit inbound rules**
6. Add these rules:

| Type | Port | Source | Description |
|------|------|--------|-------------|
| SSH | 22 | My IP | SSH access |
| Custom TCP | 5001 | 0.0.0.0/0 | API server |
| Custom TCP | 8765 | 0.0.0.0/0 | WebSocket |
| HTTPS | 443 | 0.0.0.0/0 | SSL (optional) |

7. Click **Save rules**

---

### **STEP 8: Verify Deployment**

#### Test from EC2 Instance
```bash
# Health check
curl http://localhost:5001/health

# Should return: {"status":"healthy"}

# Test upload endpoint
curl http://localhost:5001/api/courses

# Check logs
docker-compose logs api | tail -50
docker-compose logs worker | tail -50
```

#### Test from Your Local Machine
```bash
# Test with public IP
curl http://51.20.109.241:5001/health

# Test with DNS
curl http://ec2-51-20-109-241.eu-north-1.compute.amazonaws.com:5001/health

# In browser
http://51.20.109.241:5001
```

---

## 🔧 CONFIGURATION FILES

### Your docker-compose-production.yml

Make sure it looks like this:

```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    image: profai:latest
    container_name: profai_api
    ports:
      - "5001:5001"
      - "8765:8765"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    command: python run_profai_websocket_celery.py

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    image: profai:latest
    container_name: profai_worker
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    command: python worker.py
    depends_on:
      - api
```

---

## 📊 MONITORING & MAINTENANCE

### Check Resource Usage
```bash
# CPU and Memory
docker stats

# Disk space
df -h

# Container logs size
docker system df
```

### View Logs
```bash
# Live logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
docker-compose restart worker

# Full redeploy
docker-compose down && docker-compose up -d
```

### Update Code
```bash
# Pull latest code
git pull origin main

# Or upload new files via SCP

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

---

## 🚨 TROUBLESHOOTING

### Issue: Can't Connect via SSH
```bash
# Check instance is running
aws ec2 describe-instances --instance-ids i-0d995ce818dd8b8dc

# Check security group allows port 22 from your IP

# Verify key file permissions
icacls my-ai-app-key.pem
```

### Issue: Container Keeps Restarting
```bash
# Check logs
docker logs profai_api
docker logs profai_worker

# Check .env file
cat .env

# Check Redis connection
docker exec profai_api python -c "import redis; r=redis.from_url('YOUR_REDIS_URL'); print(r.ping())"
```

### Issue: Out of Memory
```bash
# Check memory
free -h

# If low, stop workers temporarily
docker stop profai_worker

# Or upgrade to t3.xlarge (16GB RAM)
```

### Issue: Port Already in Use
```bash
# Find what's using port 5001
sudo lsof -i :5001

# Kill the process
sudo kill -9 PID

# Or use different port in .env
PORT=5002
```

---

## 💰 COST OPTIMIZATION

### Current Cost: ~$60/month

```
t3.large instance:     $60/month
EBS storage (30GB):    $3/month
Data transfer:         $5/month
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total:                 ~$68/month
```

### Save Money:

1. **Stop instance when not in use**
   ```bash
   # Stop (keeps data)
   aws ec2 stop-instances --instance-ids i-0d995ce818dd8b8dc
   
   # Start
   aws ec2 start-instances --instance-ids i-0d995ce818dd8b8dc
   ```
   Saves: ~$40/month if stopped 16 hours/day

2. **Use smaller instance for testing**
   - t3.medium: $30/month (1 vCPU, 4GB)
   - t3.small: $15/month (0.5 vCPU, 2GB)

3. **Use Reserved Instance (1-year commit)**
   - Save 30-40%: ~$35/month instead of $60

---

## 📈 SCALING UP

### When to Upgrade:

**Current Capacity (t3.large):**
- 500-1,000 concurrent users
- 5-10 concurrent PDF processing
- Response time: <500ms

**Upgrade to t3.xlarge if:**
- More than 1,000 concurrent users
- Slow response times
- High CPU usage (>80%)

```bash
# In AWS Console:
1. Stop instance
2. Actions → Instance Settings → Change instance type
3. Select t3.xlarge
4. Start instance
```

### When to Move to EKS:

Consider EKS when:
- More than 5,000 concurrent users
- Need zero-downtime deployments
- Need auto-scaling
- Geographic distribution needed

You already have EKS configs ready! Just follow the EKS deployment guide.

---

## 🎯 QUICK COMMANDS CHEAT SHEET

```bash
# Deploy/Update
./deploy-to-ec2.sh

# Check status
docker-compose ps
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down

# Full rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Clean up
docker system prune -a

# Monitor resources
docker stats
htop

# Update .env
nano .env
docker-compose restart
```

---

## ✅ POST-DEPLOYMENT CHECKLIST

- [ ] API responding at http://51.20.109.241:5001/health
- [ ] WebSocket accessible at ws://51.20.109.241:8765
- [ ] Can upload PDF successfully
- [ ] Can generate quiz
- [ ] Can chat with documents
- [ ] Redis Labs connected (check logs)
- [ ] ChromaDB Cloud connected (check logs)
- [ ] Database connected (check logs)
- [ ] All API keys working (check logs for errors)
- [ ] Security group configured
- [ ] Domain pointed (if using custom domain)
- [ ] SSL configured (if using HTTPS)

---

## 🎉 SUCCESS!

Your application is now running on EC2!

**Access URLs:**
- API: http://51.20.109.241:5001
- Health: http://51.20.109.241:5001/health
- WebSocket: ws://51.20.109.241:8765

**Cost:** $60-70/month  
**Capacity:** 500-1,000 concurrent users  
**Uptime:** 99%+

**When you need more scale, your EKS setup is ready to go!**
