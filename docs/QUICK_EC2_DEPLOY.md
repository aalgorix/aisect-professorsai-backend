# ⚡ QUICK EC2 DEPLOYMENT

**Copy-paste these commands to deploy in 10 minutes!**

---

## 🚀 **OPTION 1: FAST DEPLOY (If you have SSH access)**

### On Your Local Machine (Windows PowerShell)

```powershell
# 1. Navigate to project
cd C:\Users\Lenovo\OneDrive\Documents\profainew\ProfessorAI_0.2_AWS_Ready\Prof_AI

# 2. Connect to EC2
ssh -i "C:\path\to\my-ai-app-key.pem" ec2-user@51.20.109.241
```

### On EC2 Instance

```bash
# 3. Create project directory
mkdir -p ~/profai && cd ~/profai

# 4. Create .env file
cat > .env << 'EOF'
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_KEY_HERE
ELEVENLABS_API_KEY=YOUR_ELEVENLABS_KEY_HERE
DEEPGRAM_API_KEY=YOUR_DEEPGRAM_KEY_HERE
SARVAM_API_KEY=YOUR_SARVAM_KEY_HERE
GROQ_API_KEY=YOUR_GROQ_KEY_HERE
CHROMA_CLOUD_API_KEY=YOUR_CHROMA_CLOUD_KEY_HERE
CHROMA_CLOUD_TENANT=c4f6d066-6b8e-48d1-80d9-25db6a21839e
CHROMA_CLOUD_DATABASE=profai
USE_CHROMA_CLOUD=true
REDIS_URL=rediss://default:YOUR_REDIS_PASSWORD_HERE@redis-10925.crce206.ap-south-1-1.ec2.cloud.redislabs.com:10925
REDIS_PASSWORD=YOUR_REDIS_PASSWORD_HERE
USE_DATABASE=True
DATABASE_URL=postgresql://neondb_owner:YOUR_NEON_DB_PASSWORD_HERE@ep-still-cake-adz101ej-pooler.c-2.us-east-1.aws.neon.tech/prof_AI?sslmode=require&channel_binding=require
HOST=0.0.0.0
PORT=5001
DEBUG=False
EOF

# 5. Exit and transfer files from local
exit
```

### Back on Local Machine

```powershell
# 6. Transfer all files
scp -i "C:\path\to\my-ai-app-key.pem" -r . ec2-user@51.20.109.241:~/profai/

# 7. Reconnect
ssh -i "C:\path\to\my-ai-app-key.pem" ec2-user@51.20.109.241
```

### On EC2 Instance Again

```bash
# 8. Deploy!
cd ~/profai
chmod +x deploy-to-ec2.sh
./deploy-to-ec2.sh

# Done! ✨
```

---

## 🔧 **OPTION 2: MANUAL STEPS**

```bash
# 1. SSH into EC2
ssh -i "my-ai-app-key.pem" ec2-user@51.20.109.241

# 2. Navigate to project
cd ~/profai

# 3. Stop old version
docker-compose -f docker-compose-production.yml down

# 4. Build new version
docker-compose -f docker-compose-production.yml build

# 5. Start
docker-compose -f docker-compose-production.yml up -d

# 6. Check logs
docker-compose -f docker-compose-production.yml logs -f
```

---

## ✅ **VERIFY IT WORKS**

```bash
# On EC2
curl http://localhost:5001/health

# On your local machine
curl http://51.20.109.241:5001/health

# In browser
http://51.20.109.241:5001
```

---

## 🔐 **CONFIGURE SECURITY GROUP**

**AWS Console → EC2 → Security Groups → launch-wizard-1**

Add inbound rules:
- Port 22 (SSH) from Your IP
- Port 5001 (API) from 0.0.0.0/0
- Port 8765 (WebSocket) from 0.0.0.0/0

---

## 📊 **USEFUL COMMANDS**

```bash
# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down

# Check resources
docker stats

# Update code and redeploy
git pull && ./deploy-to-ec2.sh
```

---

## 💰 **COST**

**EC2 (t3.large):** $60/month  
**EKS Alternative:** $440/month

**Recommendation:** Start with EC2, migrate to EKS when you reach 5K+ users.

---

## 🎯 **YOUR INSTANCE INFO**

```
Instance: prof-ai
ID: i-0d995ce818dd8b8dc
IP: 51.20.109.241
Region: eu-north-1
Type: t3.large
Key: my-ai-app-key.pem
```

**Access:** http://51.20.109.241:5001  
**WebSocket:** ws://51.20.109.241:8765

---

## 📚 **FULL GUIDES**

- `EC2_DEPLOYMENT_GUIDE.md` - Complete EC2 guide
- `AWS_DEPLOYMENT_STEP_BY_STEP.md` - EKS deployment (for later)
- `deploy-to-ec2.sh` - Automated deployment script

---

**Deploy in 10 minutes! 🚀**
