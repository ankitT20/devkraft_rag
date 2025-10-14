# Deployment Quick Start Guide

Choose your platform and follow the quick start steps:

## 🚀 Render (Recommended)

**Best for:** First-time deployers, familiar interface, easy setup

```bash
# 1. Push code to GitHub (if not already)
git add .
git commit -m "Prepare for deployment"
git push origin main

# 2. Go to Render Dashboard
# Visit: https://render.com/

# 3. Create Blueprint
# Click "New +" → "Blueprint"
# Select repository → Apply

# 4. Add environment variables in dashboard:
GEMINI_API_KEY=xxx
QDRANT_API_KEY=xxx
HF_TOKEN=xxx
MONGO_URI=xxx

# 5. Wait for deployment (5-10 min)
# Done! Your app is live.
```

**URLs:**
- API: `https://devkraft-rag-api.onrender.com`
- UI: `https://devkraft-rag-ui.onrender.com`

---

## ⚡ Railway

**Best for:** No sleep required, faster cold starts, better performance

```bash
# 1. Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# 2. Login
railway login

# 3. Initialize project
cd /path/to/devkraft_rag
railway init

# 4. Set environment variables
railway variables set GEMINI_API_KEY="xxx"
railway variables set QDRANT_API_KEY="xxx"
railway variables set HF_TOKEN="xxx"
railway variables set MONGO_URI="xxx"

# 5. Deploy
railway up

# Done! Monitor with: railway logs
```

**URLs:**
- API: `https://devkraft-rag-api.up.railway.app`
- UI: `https://devkraft-rag-ui.up.railway.app`

---

## 🌍 Fly.io

**Best for:** Global deployment, production-like setup, advanced users

```bash
# 1. Install Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. Login
flyctl auth login

# 3. Launch API
flyctl launch --config fly.toml --name devkraft-rag-api

# 4. Set secrets
flyctl secrets set GEMINI_API_KEY="xxx" QDRANT_API_KEY="xxx" HF_TOKEN="xxx" MONGO_URI="xxx"

# 5. Deploy API
flyctl deploy

# 6. Launch UI
flyctl launch --config fly-streamlit.toml --name devkraft-rag-ui

# 7. Set UI environment
flyctl secrets set API_URL="https://devkraft-rag-api.fly.dev"

# 8. Deploy UI
flyctl deploy

# Done! Monitor with: flyctl logs
```

**URLs:**
- API: `https://devkraft-rag-api.fly.dev`
- UI: `https://devkraft-rag-ui.fly.dev`

---

## 🤗 Hugging Face Spaces (Streamlit Only)

**Best for:** ML/AI demos, unlimited free tier, Streamlit-focused

```bash
# 1. Create Space
# Visit: https://huggingface.co/spaces
# Click "Create new Space" → Select "Streamlit"

# 2. Upload files
# Clone your repo
git clone https://github.com/ankitT20/devkraft_rag.git
cd devkraft_rag

# 3. Add HF Space as remote
git remote add hf https://huggingface.co/spaces/USERNAME/SPACE_NAME

# 4. Push
git push hf main

# 5. Set secrets in Space settings
GEMINI_API_KEY=xxx
QDRANT_API_KEY=xxx
HF_TOKEN=xxx
MONGO_URI=xxx
API_URL=https://your-api-url.com

# Done! Space auto-deploys
```

---

## 📋 Comparison Table

| Platform | Setup Time | Cold Start | Sleep Policy | Free Tier | Difficulty |
|----------|-----------|------------|--------------|-----------|-----------|
| **Render** | 10 min | ~30-60s | 15 min inactivity | 750 hrs/mo | ⭐ Easy |
| **Railway** | 5 min | ~5s | No sleep | $5 credit/mo | ⭐⭐ Easy |
| **Fly.io** | 15 min | ~10s | Auto-start | 3 VMs free | ⭐⭐⭐ Medium |
| **HF Spaces** | 5 min | ~10s | 48h inactivity | Unlimited | ⭐⭐ Easy |

---

## 🛠️ Required Environment Variables

All platforms need these variables:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key
QDRANT_API_KEY=your_qdrant_cloud_api_key
HF_TOKEN=your_huggingface_token

# Optional (for MongoDB chat history)
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true

# For Streamlit UI (when deployed separately)
API_URL=https://your-api-url.com
```

---

## ✅ Post-Deployment Checklist

- [ ] Test API health endpoint: `/health`
- [ ] Test query endpoint: `/query`
- [ ] Test Streamlit UI
- [ ] Set up uptime monitoring (UptimeRobot)
- [ ] Configure custom domain (optional)
- [ ] Monitor logs and metrics
- [ ] Set up alerts (optional)

---

## 🚨 Troubleshooting Quick Fixes

### Service not responding?
```bash
# Check logs
render logs  # Render
railway logs  # Railway
flyctl logs  # Fly.io
```

### Environment variables not working?
```bash
# Verify they're set
railway variables  # Railway
flyctl secrets list  # Fly.io
# Render: Check dashboard
```

### Build failing?
```bash
# Test locally first
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

---

## 📚 Detailed Guides

For detailed step-by-step instructions, see:

- [Render Guide](./RENDER.md) - Comprehensive Render deployment guide
- [Railway Guide](./RAILWAY.md) - Complete Railway deployment guide
- [Main Deployment Guide](../DEPLOYMENT.md) - All platforms comparison

---

## 💡 Tips

1. **Start with Render** if you're new to deployment
2. **Use Railway** if you need 24/7 uptime
3. **Use Fly.io** for production-like environment
4. **Use HF Spaces** for ML demos and portfolios
5. **Always test locally** before deploying
6. **Monitor your usage** to stay within free tier
7. **Set up alerts** for downtime

---

## 🆘 Need Help?

- **Render:** https://render.com/docs
- **Railway:** https://docs.railway.app/
- **Fly.io:** https://fly.io/docs/
- **HF Spaces:** https://huggingface.co/docs/hub/spaces

---

**Happy Deploying! 🚀**
