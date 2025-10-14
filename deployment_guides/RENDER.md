# Deploy to Render - Step by Step Guide

This guide provides detailed instructions for deploying DevKraft RAG to Render's free tier.

## Prerequisites

- GitHub repository with your code
- Render account (sign up at https://render.com/)
- API keys ready:
  - `GEMINI_API_KEY`
  - `QDRANT_API_KEY`
  - `HF_TOKEN`
  - `MONGO_URI` (optional)

## Deployment Method 1: Using render.yaml (Recommended)

### Step 1: Prepare Your Repository

The repository already includes `render.yaml` in the root directory. This file defines both services.

### Step 2: Create Render Account

1. Go to https://render.com/
2. Sign up using your GitHub account
3. Authorize Render to access your repositories

### Step 3: Create New Blueprint

1. In Render Dashboard, click **"New +"** → **"Blueprint"**
2. Connect your GitHub repository
3. Select the repository: `ankitT20/devkraft_rag`
4. Render will automatically detect `render.yaml`
5. Click **"Apply"**

### Step 4: Configure Environment Variables

For **devkraft-rag-api** service:
1. Click on the service name
2. Go to **Environment** tab
3. Add the following variables:
   ```
   GEMINI_API_KEY=your_actual_key_here
   QDRANT_API_KEY=your_actual_key_here
   HF_TOKEN=your_actual_token_here
   MONGO_URI=your_mongodb_uri_here (optional)
   ```
4. Click **"Save Changes"**

For **devkraft-rag-ui** service:
1. The `API_URL` is automatically set from the API service
2. No additional variables needed

### Step 5: Deploy

1. Render will automatically start building both services
2. Wait for the build to complete (5-10 minutes)
3. Once deployed, you'll get two URLs:
   - `https://devkraft-rag-api.onrender.com` (API)
   - `https://devkraft-rag-ui.onrender.com` (UI)

### Step 6: Test

1. Visit the API URL: `https://devkraft-rag-api.onrender.com/health`
2. You should see: `{"status":"ok","message":"All services are operational"}`
3. Visit the UI URL to use the chatbot interface

---

## Deployment Method 2: Manual Setup (Alternative)

If you prefer to configure services manually:

### Step 1: Deploy FastAPI Backend

1. Click **"New +"** → **"Web Service"**
2. Connect GitHub repository
3. Configure:
   - **Name:** `devkraft-rag-api`
   - **Environment:** Python 3
   - **Branch:** `main`
   - **Root Directory:** Leave empty
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Choose **Free** plan
5. Add environment variables (see Step 4 above)
6. Click **"Create Web Service"**

### Step 2: Deploy Streamlit UI

1. Click **"New +"** → **"Web Service"**
2. Connect same GitHub repository
3. Configure:
   - **Name:** `devkraft-rag-ui`
   - **Environment:** Python 3
   - **Branch:** `main`
   - **Root Directory:** Leave empty
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
4. Choose **Free** plan
5. Add environment variable:
   ```
   API_URL=https://devkraft-rag-api.onrender.com
   ```
   (Replace with your actual API URL from Step 1)
6. Click **"Create Web Service"**

---

## Important Notes

### Free Tier Limitations

- **750 hours/month** shared across all services
- Services **sleep after 15 minutes** of inactivity
- **Cold start** takes 30-60 seconds after sleep
- **Build time** is ~5-10 minutes per deployment

### Preventing Sleep

Use a free uptime monitoring service:

**Option 1: UptimeRobot**
1. Sign up at https://uptimerobot.com/
2. Add new monitor:
   - **Type:** HTTP(s)
   - **URL:** `https://devkraft-rag-api.onrender.com/health`
   - **Interval:** 5 minutes
3. This keeps your API awake by pinging every 5 minutes

**Option 2: Cron-job.org**
1. Sign up at https://cron-job.org/
2. Create new cron job:
   - **URL:** `https://devkraft-rag-api.onrender.com/health`
   - **Interval:** */5 * * * * (every 5 minutes)

### Auto-Deploy on Git Push

Render automatically deploys when you push to your repository:

1. Make code changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update feature X"
   git push origin main
   ```
3. Render detects the push and redeploys automatically
4. Watch the build logs in Render Dashboard

### Viewing Logs

1. Go to Render Dashboard
2. Click on service name
3. Click **"Logs"** tab
4. View real-time logs
5. Use search to filter logs

### Custom Domain (Optional)

1. Go to service → **Settings**
2. Scroll to **Custom Domain**
3. Add your domain
4. Configure DNS records as instructed
5. Render provides free SSL certificate

---

## Troubleshooting

### Issue: Build Fails with "Module not found"

**Solution:**
```bash
# Test locally first
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python app/main.py  # Should work without errors
```

### Issue: Service Returns 503 Error

**Cause:** Service is sleeping or starting up

**Solution:**
- Wait 30-60 seconds for cold start
- Use UptimeRobot to prevent sleep

### Issue: API URL Not Working in Streamlit

**Solution:**
1. Check API service is running
2. Verify `API_URL` environment variable in Streamlit service
3. Make sure URL includes `https://` protocol
4. Try accessing API health endpoint directly

### Issue: Environment Variables Not Loading

**Solution:**
1. Go to service → **Environment**
2. Click **"Add Environment Variable"**
3. Enter **exact** key name (case-sensitive)
4. Click **"Save Changes"**
5. **Manual Deploy** to apply changes

### Issue: Port Already in Use

**Cause:** Not using `$PORT` variable

**Solution:**
Ensure start command uses `$PORT`:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## Monitoring & Maintenance

### Check Service Health

```bash
# Check API health
curl https://devkraft-rag-api.onrender.com/health

# Expected response:
{"status":"ok","message":"All services are operational"}
```

### Monitor Usage

1. Go to Render Dashboard
2. Click on service name
3. View **Metrics** tab:
   - CPU usage
   - Memory usage
   - Request count
   - Response time

### Update Environment Variables

1. Go to service → **Environment**
2. Click on variable to edit
3. Update value
4. Click **"Save Changes"**
5. Service automatically restarts

---

## Cost Optimization

### Option 1: Single Service (API Only)

If you want to save hours:
- Deploy only the FastAPI backend
- Use the API with Postman or other clients
- Skip Streamlit UI deployment

### Option 2: Scheduled Deployment

For development/testing:
- Use Render's **Suspend** feature
- Manually resume when needed
- Saves free tier hours

### Option 3: Hybrid Approach

- **Backend:** Render (reliable, important)
- **Frontend:** Hugging Face Spaces (unlimited free tier)

---

## Next Steps

1. ✅ Deploy both services
2. ✅ Test endpoints
3. ✅ Set up UptimeRobot (optional)
4. ✅ Configure custom domain (optional)
5. ✅ Share your deployed app!

---

## Resources

- **Render Docs:** https://render.com/docs
- **Render Status:** https://status.render.com/
- **FastAPI on Render:** https://render.com/docs/deploy-fastapi
- **Streamlit on Render:** https://docs.streamlit.io/knowledge-base/tutorials/databases/render

---

**Happy Deploying! 🚀**
