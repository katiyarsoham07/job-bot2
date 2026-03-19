# Soham's Daily Job Bot v2.1 🎯
### Powered by Google Gemini AI (100% FREE)

Fetches 60+ Sales/BD/GM/AgriTech jobs daily.
Scores each job using Gemini 1.5 Flash against your IIM K MBA + Agri profile.
Displays results in a live web dashboard on GitHub Pages.

---

## 💰 Cost Breakdown

| Component       | Cost          |
|-----------------|---------------|
| GitHub Actions  | FREE (2000 min/month) |
| GitHub Pages    | FREE          |
| Gemini 1.5 Flash| **FREE** (1500 req/day free tier) |
| **Total**       | **₹0/month**  |

> Gemini free tier = 1500 requests/day. Bot uses ~13 requests/day (130 jobs ÷ 10 per batch). You have 1487 requests to spare.

---

## ⚡ Setup in 15 Minutes

### Step 1 — Get Gemini API Key (FREE, 2 minutes)
1. Go to **aistudio.google.com/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key — looks like `AIzaSy...`

### Step 2 — Create GitHub Repository
1. Go to **github.com** → New Repository
2. Name: `job-bot` (must be **public** for GitHub Pages)
3. Upload all these files

### Step 3 — Add Gemini Key as Secret
1. Your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Name: `GEMINI_API_KEY`
4. Value: paste your `AIzaSy...` key
5. Save

### Step 4 — Enable GitHub Pages (your dashboard URL)
1. Your repo → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** → **/ (root)**
4. Save
5. Dashboard live at: `https://YOUR-USERNAME.github.io/job-bot/`

### Step 5 — Run It Now
1. Your repo → **Actions** tab
2. Click **"Daily Job Fetch"**
3. Click **"Run workflow"** → **Run workflow**
4. Wait ~3 minutes
5. Visit your dashboard — 60 jobs, AI-ranked! ✅

**After that: auto-runs every morning at 7:30 AM IST. Just open the URL.**

---

## 🌾 AgriTech Startups Monitored Daily
DeHaat · Ninjacart · AgroStar · Bighaat · FarMart · BharatAgri · Gramophone
WayCool · CropIn · Samunnati · Arya.ag · Fyllo · Eruvaka · Captain Fresh
Stellapps · KhetiBadi · Country Delight · Bijak · Animall · Krishify

## 🚀 Growth Startups Monitored Daily
Razorpay · OfBusiness · Udaan · Meesho · Zetwerk · Infra.Market
Juspay · Licious · Milkbasket · Daalchini + more

## 📡 Sources
LinkedIn RSS · Indeed India · Instahyre · Cutshort · Wellfound (AngelList) · IIMJobs · YC Jobs · Shine

## 🤖 How AI Scoring Works
Gemini 1.5 Flash reads each job title + description and scores 1–10 against your profile:
- **9-10**: AgriTech startup + sales/BD role (your rarest, highest-value combo)
- **8-9**: Rural/FMCG/startup sales leadership
- **7-8**: General startup BD/sales at Series A-C
- **5-7**: Large corporate (possibly underleveled for IIM K MBA)
- **3-5**: Experience mismatch (5+ years required)
