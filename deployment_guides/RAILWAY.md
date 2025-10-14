# Deploy to Railway - Step by Step Guide

This guide provides detailed instructions for deploying DevKraft RAG to Railway's free tier.

## Why Railway?

- ✅ **$5 free credit** per month
- ✅ **No sleep policy** (stays running 24/7)
- ✅ **Fast cold starts** (~5 seconds)
- ✅ **Excellent developer experience**
- ✅ **Built-in metrics and logs**

## Prerequisites

- GitHub repository with your code
- Railway account (sign up at https://railway.app/)
- Credit card for verification (won't be charged on free tier)
- API keys ready:
  - `GEMINI_API_KEY`
  - `QDRANT_API_KEY`
  - `HF_TOKEN`
  - `MONGO_URI` (optional)

## Deployment Steps

### Step 1: Create Railway Account

1. Go to https://railway.app/
2. Sign up using your GitHub account
3. Complete verification (credit card required but not charged)

### Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose repository: `ankitT20/devkraft_rag`
4. Railway will start deploying automatically

### Step 3: Configure FastAPI Backend

1. Railway creates a service automatically
2. Click on the service card
3. Go to **Settings** tab
4. Configure:
   - **Service Name:** `devkraft-rag-api`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/health`

### Step 4: Add Environment Variables (Backend)

1. Click on the service card
2. Go to **Variables** tab
3. Click **"New Variable"**
4. Add each variable:
   ```
   GEMINI_API_KEY=your_actual_key_here
   QDRANT_API_KEY=your_actual_key_here
   HF_TOKEN=your_actual_token_here
   MONGO_URI=your_mongodb_uri_here
   ```
5. Variables are automatically encrypted

### Step 5: Generate Domain for API

1. In service settings, go to **Networking**
2. Click **"Generate Domain"**
3. You'll get a URL like: `https://devkraft-rag-api.up.railway.app`
4. Copy this URL for the next step

### Step 6: Add Streamlit UI Service

1. Click **"New"** → **"GitHub Repo"**
2. Select same repository
3. Railway creates another service
4. Configure:
   - **Service Name:** `devkraft-rag-ui`
   - **Start Command:** `streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`

### Step 7: Add Environment Variables (UI)

1. Go to Streamlit service → **Variables**
2. Add:
   ```
   API_URL=https://devkraft-rag-api.up.railway.app
   ```
   (Use the API URL from Step 5)

### Step 8: Generate Domain for UI

1. In Streamlit service settings, go to **Networking**
2. Click **"Generate Domain"**
3. You'll get a URL like: `https://devkraft-rag-ui.up.railway.app`

### Step 9: Test Deployment

1. Visit API health endpoint:
   ```
   https://devkraft-rag-api.up.railway.app/health
   ```
2. Expected response:
   ```json
   {"status":"ok","message":"All services are operational"}
   ```
3. Visit UI URL to use the chatbot

---

## Alternative: Using Railway CLI

### Step 1: Install Railway CLI

**macOS/Linux:**
```bash
curl -fsSL https://railway.app/install.sh | sh
```

**Windows (PowerShell):**
```powershell
iwr https://railway.app/install.ps1 | iex
```

### Step 2: Login

```bash
railway login
```

### Step 3: Initialize Project

```bash
cd /path/to/devkraft_rag
railway init
```

### Step 4: Set Environment Variables

```bash
railway variables set GEMINI_API_KEY="your_key_here"
railway variables set QDRANT_API_KEY="your_key_here"
railway variables set HF_TOKEN="your_token_here"
railway variables set MONGO_URI="your_uri_here"
```

### Step 5: Deploy

```bash
railway up
```

### Step 6: View Logs

```bash
railway logs
```

---

## Configuration Files

The repository includes `railway.json` for Railway-specific configuration:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Note:** Railway auto-detects Python and requirements.txt, so this file is optional but provides better control.

---

## Important Notes

### Free Tier Details

- **$5 credit/month** (resets monthly)
- Estimated usage: **$3-4/month** for 2 services
- **No sleep policy** (stays running)
- **Fast cold starts** (~5 seconds)
- **500 GB egress/month**

### Credit Monitoring

1. Go to Railway Dashboard
2. Click on your profile (top right)
3. View **Usage** tab
4. Monitor credit consumption

### Auto-Deploy on Git Push

Railway automatically redeploys when you push to GitHub:

```bash
git add .
git commit -m "Update feature X"
git push origin main
# Railway automatically detects and redeploys
```

### Viewing Logs

**Dashboard:**
1. Click on service card
2. Go to **Deployments** tab
3. Click on latest deployment
4. View real-time logs

**CLI:**
```bash
railway logs
railway logs --follow  # Real-time streaming
```

### Custom Domain

1. Go to service → **Settings** → **Networking**
2. Click **"Custom Domain"**
3. Enter your domain (e.g., `api.yourdomain.com`)
4. Configure DNS records as instructed:
   - Type: `CNAME`
   - Name: `api`
   - Value: Your Railway domain
5. Railway provides free SSL certificate

---

## Troubleshooting

### Issue: Deployment Fails

**Check logs:**
```bash
railway logs
```

**Common causes:**
- Missing dependencies in `requirements.txt`
- Python version mismatch
- Environment variables not set

**Solution:**
```bash
# Test locally first
pip install -r requirements.txt
python app/main.py
```

### Issue: Service Not Responding

**Check service status:**
1. Dashboard → Service card → **Deployments**
2. Look for error messages
3. Check health check status

**Solution:**
- Verify start command is correct
- Check health check endpoint exists
- Ensure `$PORT` is used in start command

### Issue: Out of Credit

**Symptom:** Services stop working mid-month

**Solution:**
1. Check usage dashboard
2. Optimize services:
   - Reduce number of services
   - Use external free services (e.g., Qdrant Cloud)
   - Deploy UI on Hugging Face Spaces
3. Upgrade to paid plan ($5/month for additional credit)

### Issue: Environment Variables Not Loading

**Solution:**
```bash
# Via CLI
railway variables set KEY=value

# Verify
railway variables
```

Or in Dashboard:
1. Service → **Variables**
2. Add/edit variable
3. Service automatically restarts

### Issue: Build Takes Too Long

**Cause:** Large dependencies

**Solution:**
1. Optimize `requirements.txt`:
   ```bash
   pip freeze > requirements.txt
   # Review and remove unused packages
   ```
2. Use Railway's build cache:
   - Subsequent builds are faster
   - Cache is shared across deployments

---

## Monitoring & Maintenance

### Check Service Health

```bash
# Via curl
curl https://devkraft-rag-api.up.railway.app/health

# Via Railway CLI
railway run curl http://localhost:$PORT/health
```

### Monitor Metrics

Dashboard provides:
- **CPU usage**
- **Memory usage**
- **Network traffic**
- **Request count**
- **Response time**

### Update Environment Variables

**CLI:**
```bash
railway variables set GEMINI_API_KEY="new_key_here"
```

**Dashboard:**
1. Service → **Variables**
2. Click variable to edit
3. Update value
4. Service auto-restarts

---

## Cost Optimization

### Estimated Usage

| Service | Estimated Cost/Month |
|---------|---------------------|
| FastAPI Backend | ~$2-3 |
| Streamlit UI | ~$1-2 |
| **Total** | **~$3-4** |

### Tips to Reduce Cost

1. **Use external services:**
   - Qdrant Cloud (free tier)
   - MongoDB Atlas (free tier)
   - Gemini API (free tier)

2. **Optimize resources:**
   - Reduce memory usage
   - Optimize API calls
   - Cache responses

3. **Hybrid deployment:**
   - **Backend:** Railway (reliable, fast)
   - **Frontend:** Hugging Face Spaces (unlimited free)

---

## Advantages Over Render

| Feature | Railway | Render |
|---------|---------|--------|
| **Cold Starts** | ~5 seconds | ~30-60 seconds |
| **Sleep Policy** | No sleep | 15 min inactivity |
| **Free Tier** | $5 credit/mo | 750 hrs/mo |
| **Metrics** | Excellent | Good |
| **Developer UX** | Excellent | Good |
| **Speed** | Very Fast | Moderate |

---

## Next Steps

1. ✅ Deploy both services
2. ✅ Test endpoints
3. ✅ Monitor credit usage
4. ✅ Configure custom domain (optional)
5. ✅ Set up monitoring alerts

---

## Resources

- **Railway Docs:** https://docs.railway.app/
- **Railway Status:** https://railway.statuspage.io/
- **Railway CLI:** https://docs.railway.app/develop/cli
- **Community:** https://discord.gg/railway

---

**Happy Deploying! 🚀**
