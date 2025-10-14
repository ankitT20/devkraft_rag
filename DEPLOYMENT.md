# Free Deployment Options for DevKraft RAG

This document provides comprehensive guidance on deploying the DevKraft RAG application using **FREE** platforms only. The application consists of two components:
1. **FastAPI Backend** (port 8000) - REST API for RAG operations
2. **Streamlit Frontend** (port 8501) - Interactive UI

## Table of Contents
1. [Deployment Platforms Comparison](#deployment-platforms-comparison)
2. [Platform-Specific Guides](#platform-specific-guides)
3. [Understanding uvicorn.run() - Reddit Comment Explained](#understanding-uvicornrun---reddit-comment-explained)
4. [Recommended Approach](#recommended-approach)
5. [Environment Variables Setup](#environment-variables-setup)
6. [Fallback Configuration](#fallback-configuration)

---

## Deployment Platforms Comparison

| Platform | Free Tier | FastAPI Support | Streamlit Support | Multi-Service | Build Time | Sleep Policy | Recommended For |
|----------|-----------|----------------|------------------|--------------|------------|--------------|-----------------|
| **Render** | ✅ 750 hrs/mo | ✅ Excellent | ✅ Excellent | ✅ Yes (separate services) | ~5-10 min | Sleeps after 15 min inactivity | **Best Overall** |
| **Railway** | ✅ $5 credit/mo | ✅ Excellent | ✅ Good | ✅ Yes | ~3-5 min | No sleep on free tier | Fast deployment |
| **Fly.io** | ✅ 3 VMs free | ✅ Excellent | ⚠️ Requires config | ✅ Yes | ~5 min | No sleep | Advanced users |
| **Vercel** | ✅ Unlimited | ⚠️ Serverless only | ❌ Not suitable | ❌ No | ~2 min | Serverless (no sleep) | API only (not RAG) |
| **PythonAnywhere** | ✅ 1 web app | ✅ Good | ❌ Limited | ❌ No | Manual | Always on | Simple APIs only |
| **Hugging Face Spaces** | ✅ Unlimited | ⚠️ Limited | ✅ Excellent | ⚠️ Complex | ~3-5 min | Sleeps after 48h | Streamlit-first apps |
| **Replit** | ✅ Limited | ✅ Good | ✅ Good | ⚠️ Limited | ~2 min | Sleeps quickly | Development/Testing |
| **Glitch** | ✅ Unlimited | ⚠️ Basic | ❌ Not suitable | ❌ No | ~1 min | Sleeps after 5 min | Simple apps only |

**Note on Cyclic.sh:** As mentioned in the issue, Cyclic was a popular option but **shut down in August 2024**. It's no longer available for deployment.

---

## Platform-Specific Guides

### 1. Render (⭐ **RECOMMENDED**)

**Why Render?** 
- Most mature free tier for Python apps
- Excellent documentation and UI
- Supports both FastAPI and Streamlit natively
- Easy environment variable management
- Auto-deploys from GitHub
- You're already familiar with it!

#### Setup Steps:

**A. Deploy FastAPI Backend**

1. **Create `render.yaml`** (for Infrastructure as Code):
```yaml
services:
  # FastAPI Backend
  - type: web
    name: devkraft-rag-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: GEMINI_API_KEY
        sync: false
      - key: QDRANT_API_KEY
        sync: false
      - key: HF_TOKEN
        sync: false
      - key: MONGO_URI
        sync: false
    healthCheckPath: /health

  # Streamlit Frontend
  - type: web
    name: devkraft-rag-ui
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: API_URL
        value: https://devkraft-rag-api.onrender.com
```

2. **Via Render Dashboard** (Alternative to render.yaml):
   - Go to https://render.com/
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure service:
     - **Name:** `devkraft-rag-api`
     - **Environment:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - **Instance Type:** Free
   - Add environment variables in the dashboard

3. **Deploy Streamlit UI** (Separate Service):
   - Create another web service
   - **Name:** `devkraft-rag-ui`
   - **Start Command:** `streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0`
   - Set `API_URL` environment variable to your API URL

4. **Important Notes:**
   - Render uses `$PORT` environment variable (don't hardcode ports)
   - Services sleep after 15 minutes of inactivity
   - First request after sleep takes ~30-60 seconds
   - Free tier includes 750 hours/month (shared across services)

**Pros:**
- ✅ Best documentation and support
- ✅ Easy to use dashboard
- ✅ Auto-deploys on git push
- ✅ Free SSL certificates
- ✅ Good for both FastAPI and Streamlit

**Cons:**
- ❌ 15-minute sleep policy
- ❌ Slower cold starts (~30-60s)
- ❌ Limited to 750 hours/month combined

---

### 2. Railway

**Why Railway?**
- Fast deployments and cold starts
- No sleep policy on free tier
- Great developer experience
- Good for testing and staging

#### Setup Steps:

1. **Create `railway.json`**:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100
  }
}
```

2. **Create `Procfile`** (Alternative):
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

3. **Deploy:**
   - Go to https://railway.app/
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects Python and requirements.txt
   - Add environment variables in the dashboard

4. **For Streamlit** (Separate Service):
   - Create another service in the same project
   - Set start command: `streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0`

5. **Important Notes:**
   - Railway gives $5 credit/month on free tier
   - Estimated usage: ~$3-4/month for small apps
   - No sleep policy (stays running)
   - Fast cold starts (~5s)

**Pros:**
- ✅ Fast deployments and cold starts
- ✅ No sleep on free tier (within credit)
- ✅ Excellent developer experience
- ✅ Built-in metrics and logs

**Cons:**
- ❌ Limited $5/month credit
- ❌ May run out of credit for heavy usage
- ❌ Requires credit card for verification

---

### 3. Fly.io

**Why Fly.io?**
- True global deployment
- Multiple regions available
- Good for production-like environments
- 3 shared VMs free

#### Setup Steps:

1. **Install Fly CLI:**
```bash
curl -L https://fly.io/install.sh | sh
```

2. **Create `fly.toml`**:
```toml
app = "devkraft-rag-api"
primary_region = "iad"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

3. **Deploy:**
```bash
fly launch
fly secrets set GEMINI_API_KEY="your-key" QDRANT_API_KEY="your-key" HF_TOKEN="your-token" MONGO_URI="your-uri"
fly deploy
```

4. **For Streamlit** (Separate App):
```bash
fly launch --name devkraft-rag-ui
# Set different start command in fly.toml
fly deploy
```

**Pros:**
- ✅ 3 free VMs (1GB storage each)
- ✅ Global CDN and edge network
- ✅ No sleep (auto-start on request)
- ✅ Production-grade infrastructure

**Cons:**
- ❌ More complex setup
- ❌ CLI-focused (less GUI)
- ❌ Steeper learning curve
- ❌ Limited free resources

---

### 4. Hugging Face Spaces (For Streamlit-First Approach)

**Why Hugging Face Spaces?**
- Perfect for ML/AI applications
- Excellent for Streamlit apps
- Unlimited free tier
- Great community

#### Setup Steps:

1. **Create a Space:**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Select "Streamlit" as SDK

2. **Project Structure:**
   - All code in repository root
   - Rename `streamlit_app.py` to `app.py`
   - Add `requirements.txt`

3. **For FastAPI Backend:**
   - Create a second Space with "Docker" SDK
   - Use custom Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

4. **Connect Services:**
   - Update Streamlit app to use FastAPI Space URL
   - Example: `https://username-space-name.hf.space`

**Pros:**
- ✅ Unlimited free tier
- ✅ No sleep after inactivity (only after 48h)
- ✅ Perfect for AI/ML demos
- ✅ Great for showcasing projects

**Cons:**
- ❌ Requires separating FastAPI and Streamlit
- ❌ Less flexible than other platforms
- ❌ Public by default (private requires subscription)

---

### 5. PythonAnywhere (Simple Backend Only)

**Why PythonAnywhere?**
- Always on (no sleep)
- Simple setup
- Good for API-only deployments

#### Setup Steps:

1. **Sign up** at https://www.pythonanywhere.com/
2. **Upload code** via Git or web interface
3. **Create Web App:**
   - WSGI configuration
   - Point to FastAPI app
4. **Set environment variables** in web interface

**Important:** PythonAnywhere free tier does NOT support:
- Streamlit (requires always-running process)
- WebSockets (needed for some Streamlit features)
- External HTTPS requests (firewall restrictions)

**Pros:**
- ✅ Always on (no sleep)
- ✅ Simple setup
- ✅ Good for learning

**Cons:**
- ❌ Cannot run Streamlit
- ❌ Firewall restrictions
- ❌ Limited resources
- ❌ Not suitable for this project

---

### 6. Replit (Development/Testing)

**Why Replit?**
- Quick prototyping
- Online IDE included
- Easy sharing

#### Setup Steps:

1. **Import from GitHub:**
   - Go to https://replit.com/
   - Click "Import from GitHub"
   - Select repository

2. **Configure:**
   - Replit auto-detects Python
   - Add `.replit` file:
```
run = "uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

3. **Environment Variables:**
   - Use Secrets tab in Replit

**Pros:**
- ✅ Very quick setup
- ✅ Online IDE
- ✅ Good for demos

**Cons:**
- ❌ Sleeps very quickly (aggressive)
- ❌ Limited resources
- ❌ Not reliable for production
- ❌ Requires keeping browser open

---

## Understanding uvicorn.run() - Reddit Comment Explained

The Reddit comment you found mentions:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=3000)
```

### Do You Need This?

**Short Answer:** It depends on the platform.

**Current Code in `app/main.py`:**
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Platform-by-Platform Breakdown:

#### ✅ **Render - NO, Not Needed**
- **Why?** Render allows you to specify the startup command in the dashboard or `render.yaml`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Advantage:** Render sets the `$PORT` environment variable dynamically
- **Your code:** The `if __name__ == "__main__"` block is ignored because Render runs the uvicorn command directly

#### ⚠️ **Cyclic - WAS Required (Platform Shut Down)**
- Cyclic required the `if __name__ == "__main__"` block
- The Python file was executed directly: `python app/main.py`
- This approach is less flexible because the port is hardcoded
- **Important:** Cyclic shut down in August 2024, no longer available

#### ✅ **Railway - NO, Not Needed**
- Similar to Render, uses `Procfile` or `railway.json`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- The block is not executed

#### ✅ **Fly.io - NO, Not Needed**
- Uses `fly.toml` configuration
- Command specified in config file
- The block is not executed

#### ⚠️ **Replit - OPTIONAL**
- Can use `.replit` file OR run the Python file directly
- Having the block doesn't hurt, gives flexibility

#### ⚠️ **Hugging Face Spaces - DEPENDS**
- Docker-based: Use CMD in Dockerfile (not needed)
- Direct execution: Might need it (depends on SDK)

### Recommendations:

**Keep the Current Code:**
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**But make it more flexible for cloud deployments:**
```python
if __name__ == "__main__":
    import uvicorn
    import os
    
    # Use PORT environment variable if available (cloud platforms)
    # Otherwise default to 8000 (local development)
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(app, host="0.0.0.0", port=port)
```

**Why this approach?**
- ✅ Works for local development: `python app/main.py` or `python -m app.main`
- ✅ Works with cloud platforms: They'll use the command approach (this block is ignored)
- ✅ Flexible: Respects `PORT` environment variable if set
- ✅ No breaking changes needed

**When is it actually used?**
- Only when you run `python app/main.py` or `python -m app.main` directly
- Not used when running `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Most cloud platforms use the uvicorn command approach

---

## Recommended Approach

### Best Option: Render with Two Services

**Why?**
1. Free 750 hours/month
2. You're already familiar with it
3. Native support for both FastAPI and Streamlit
4. Easy environment variable management
5. Good documentation
6. Auto-deployment from GitHub

### Deployment Architecture:

```
GitHub Repository
    ↓ (Auto-deploy)
    ├─→ Render Service 1: devkraft-rag-api (FastAPI)
    │   ├─ URL: https://devkraft-rag-api.onrender.com
    │   ├─ Health Check: /health
    │   └─ Environment Variables: GEMINI_API_KEY, QDRANT_API_KEY, etc.
    │
    └─→ Render Service 2: devkraft-rag-ui (Streamlit)
        ├─ URL: https://devkraft-rag-ui.onrender.com
        └─ Environment Variable: API_URL=https://devkraft-rag-api.onrender.com
```

### Alternative: Railway (if you want no-sleep)

- Better for staging/testing environments
- $5/month credit should be enough for moderate usage
- Faster cold starts than Render

### For Maximum Free Tier:

**Hybrid Approach:**
- **FastAPI Backend:** Render (more reliable)
- **Streamlit UI:** Hugging Face Spaces (better for ML apps)

---

## Environment Variables Setup

All platforms require these environment variables:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here
QDRANT_API_KEY=your_qdrant_cloud_api_key_here
HF_TOKEN=your_huggingface_token_here

# Optional (for MongoDB chat history)
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true

# For Streamlit UI (when deployed separately)
API_URL=https://your-api-url.onrender.com
```

### Platform-Specific Variable Names:

**Render:**
- Add in Dashboard → Environment → Environment Variables
- Or use `render.yaml` (recommended)

**Railway:**
- Add in Dashboard → Variables tab
- Or use Railway CLI: `railway variables set KEY=value`

**Fly.io:**
- Use CLI: `fly secrets set KEY=value`
- Or edit `fly.toml`

**Hugging Face Spaces:**
- Settings → Repository Secrets
- Available at runtime

---

## Fallback Configuration

Your application already has excellent fallback mechanisms:

### ✅ Already Implemented:

1. **Qdrant Storage:**
   - Primary: Qdrant Cloud (always available)
   - Fallback: If Docker unavailable, uses cloud collections
   - See: `app/core/storage.py`

2. **Chat History:**
   - Primary: MongoDB Atlas
   - Fallback: JSON files in `user_chat/` folder
   - Automatic fallback, no configuration needed

3. **Embeddings:**
   - Primary: LM Studio (local)
   - Fallback: HuggingFace API
   - Works automatically in cloud deployment

4. **LLM Models:**
   - Primary: LM Studio (local)
   - Fallback: HuggingFace API
   - Automatic fallback in production

### For Cloud Deployment:

**What Works Out of the Box:**
- ✅ Gemini API (always available with API key)
- ✅ Qdrant Cloud (always available with API key)
- ✅ HuggingFace (fallback for embeddings/LLM)
- ✅ MongoDB Atlas (optional, with fallback to JSON)

**What Won't Work (Expected):**
- ❌ Qdrant Docker (no Docker in most free tiers)
- ❌ LM Studio (local service, not in cloud)
- ❌ Local embedding models (not in cloud)

**But:** Your fallback configuration handles all of this automatically! 🎉

---

## Monitoring & Maintenance

### Preventing Sleep (Render/Railway):

**Option 1: UptimeRobot (Free)**
- Sign up at https://uptimerobot.com/
- Add your service URL
- Pings every 5 minutes
- Keeps your service awake

**Option 2: Cron-job.org (Free)**
- Similar to UptimeRobot
- More configuration options
- Can ping multiple URLs

**Option 3: GitHub Actions (Free)**
```yaml
name: Keep Alive
on:
  schedule:
    - cron: '*/14 * * * *'  # Every 14 minutes
  workflow_dispatch:

jobs:
  keep-alive:
    runs-on: ubuntu-latest
    steps:
      - name: Ping API
        run: curl -f https://your-api-url.onrender.com/health || exit 0
```

### Logs and Debugging:

**Render:**
- View logs in Dashboard → Logs tab
- Real-time streaming logs
- Download logs for analysis

**Railway:**
- Excellent built-in logging
- Metrics and analytics
- Deployment history

**Fly.io:**
- `fly logs` command
- Real-time log streaming
- Integration with logging services

---

## Cost Comparison (Monthly)

| Platform | Free Tier | Estimated Usage | Cost |
|----------|-----------|-----------------|------|
| **Render** | 750 hrs/mo | 2 services × 720 hrs = 1440 hrs* | **$0** (with sleep) or **Exceeds** (no sleep) |
| **Railway** | $5 credit | ~$3-4/month for 2 services | **$0** (within credit) |
| **Fly.io** | 3 VMs free | 2 apps × 1 VM each | **$0** |
| **HF Spaces** | Unlimited | Unlimited | **$0** |
| **PythonAnywhere** | 1 web app | Limited | **$0** (API only) |

*Note: Render's 750 hours is shared across all services. For 2 services running 24/7, you'd need 1440 hours, which exceeds the free tier. Solution: Let services sleep (default behavior) or use UptimeRobot to keep only critical service awake.

---

## Troubleshooting Common Issues

### Issue 1: "Application failed to respond"
- **Cause:** Wrong port configuration
- **Solution:** Use `$PORT` environment variable (most platforms set this)
- **Fix:** Update uvicorn command to `--port $PORT`

### Issue 2: "Module not found"
- **Cause:** Missing dependencies in requirements.txt
- **Solution:** Ensure all imports are in requirements.txt
- **Fix:** Test locally with fresh venv: `pip install -r requirements.txt`

### Issue 3: "Service sleeping/not responding"
- **Cause:** Inactivity timeout
- **Solution:** Use UptimeRobot or similar service
- **Alternative:** Upgrade to paid tier for always-on

### Issue 4: "Environment variables not loaded"
- **Cause:** Not set correctly in platform dashboard
- **Solution:** Double-check variable names (case-sensitive)
- **Fix:** Use platform's environment variable UI, not .env file

### Issue 5: "Cold start too slow"
- **Cause:** Large dependencies (numpy, pandas, transformers)
- **Solution:** Optimize requirements.txt (remove unused packages)
- **Alternative:** Use Railway (faster cold starts) or Fly.io (VM-based)

---

## Next Steps

1. **Choose Your Platform:**
   - Recommended: Start with **Render** (you know it, it works)
   - Alternative: **Railway** (if you need no-sleep behavior)

2. **Prepare Configuration:**
   - Create `render.yaml` or `Procfile`
   - Update `streamlit_app.py` API_URL to use environment variable

3. **Set Environment Variables:**
   - Get all API keys ready
   - Add to platform dashboard

4. **Deploy:**
   - Connect GitHub repository
   - Let platform auto-deploy
   - Test endpoints

5. **Monitor:**
   - Set up UptimeRobot (optional)
   - Check logs regularly
   - Monitor usage

6. **Optimize:**
   - Add caching where possible
   - Optimize cold start time
   - Consider splitting services if needed

---

## Conclusion

**Best Choice for Your Project: Render**

✅ Pros:
- You're already familiar with it
- Excellent documentation
- Native support for both FastAPI and Streamlit
- Easy GitHub integration
- Free SSL
- Good enough for MVP/demo

⚠️ Keep in Mind:
- Services sleep after 15 min inactivity
- Cold start takes ~30-60 seconds
- Use UptimeRobot to prevent sleep
- 750 hours/month shared across services

**Alternative: Railway**
- If you need faster cold starts
- If no-sleep is critical
- $5/month credit is usually enough

**Regarding the Reddit Comment:**
The `if __name__ == "__main__"` block is NOT required for Render deployment. Render uses the command-line approach (`uvicorn app.main:app`), which is more flexible and follows best practices. The block is useful for local development but won't be executed in cloud deployments.

---

## Support & Resources

- **Render Docs:** https://render.com/docs/deploy-fastapi
- **Railway Docs:** https://docs.railway.app/
- **Fly.io Docs:** https://fly.io/docs/
- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/
- **Streamlit Deployment:** https://docs.streamlit.io/streamlit-community-cloud/get-started

---

**Made by Ankit Tayal**  
*DevKraft RAG - A free, open-source RAG system*
