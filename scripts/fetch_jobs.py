"""
Job Fetcher v3.0 — Soham Katiyar | IIM K MBA
Uses APIs that WORK from GitHub Actions (cloud IPs):
  - Google News RSS       — hiring posts, NO auth needed
  - Remotive API          — remote jobs, NO auth needed  
  - Arbeitnow API         — global jobs, NO auth needed
  - Jobicy API            — startup jobs, NO auth needed
  - Adzuna India API      — best India coverage (free key: developer.adzuna.com)
  - JSearch RapidAPI      — LinkedIn+Indeed jobs (free key: rapidapi.com/letscrape)

Scoring: Google Gemini 1.5 Flash (FREE — 1500 req/day)
"""

import json, os, re, time, hashlib
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

# ─── API KEYS ──────────────────────────────────────────────────────────────
GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY",   "")
ADZUNA_APP_ID    = os.environ.get("ADZUNA_APP_ID",    "")   # free: developer.adzuna.com
ADZUNA_APP_KEY   = os.environ.get("ADZUNA_APP_KEY",   "")   # free: developer.adzuna.com
JSEARCH_API_KEY  = os.environ.get("JSEARCH_API_KEY",  "")   # free: rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch

OUTPUT_FILE = "jobs.json"
MAX_TOTAL   = 120

# ─── CANDIDATE PROFILE ────────────────────────────────────────────────────
CANDIDATE_PROFILE = """
Name: Soham Katiyar
Education: MBA - IIM Kozhikode (2023-2025) | B.Sc. Agriculture Gold Medalist (90.41%)
Total Experience: 19 months
Last Role: General Manager - Sales & BD, RAAM Group (JSW MG Motors)
Background: Corporate Sales, AgriTech, Rural Markets, ICAR, Government Partnerships
Key Skills: B2B/B2C Sales, GTM Strategy, Key Account Management, Channel Management,
            P&L Ownership, Team Leadership (32 people), Market Penetration, CRM,
            Agri domain expertise, Dealer network building, Rural market development
Location: Kanpur, UP (Pan-India open, remote ok)
Target Roles: Sales Manager, BD Manager, GM Sales, Strategy Manager, KAM,
              GTM Manager, Regional Sales Manager, Agri Sales Manager, Startup Sales Lead
Target Industries: AgriTech Startups > Rural-tech > FMCG > Automotive > SaaS > Fintech
Salary: 12-20 LPA (IIM K MBA premium, 19 months exp)
"""

# ─── HELPERS ───────────────────────────────────────────────────────────────
def make_job(title, link, desc, source, tag="general", company="N/A", location="India"):
    return {
        "id":          hashlib.md5(link.encode()).hexdigest()[:10],
        "title":       title.strip()[:120],
        "link":        link.strip(),
        "description": desc.strip()[:400],
        "published":   datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000"),
        "source":      source,
        "tag":         tag,
        "score":       0,
        "reason":      "",
        "company":     company[:80],
        "location":    location[:60],
        "is_startup":  tag in ("startup", "agritech"),
        "is_agri":     tag == "agritech",
    }

def fetch_url(url, timeout=15):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; JobBot/3.0)"})
    with urlopen(req, timeout=timeout) as r:
        return r.read()

def fetch_json(url, headers=None, timeout=15):
    h = {"User-Agent": "Mozilla/5.0 JobBot/3.0", "Accept": "application/json"}
    if headers: h.update(headers)
    req = Request(url, headers=h)
    with urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def fetch_rss(url, source, tag="general", timeout=15):
    jobs = []
    try:
        content = fetch_url(url, timeout)
        root    = ET.fromstring(content)
        channel = root.find("channel") or root
        for item in channel.findall("item")[:12]:
            title = (item.findtext("title") or "").strip()
            link  = (item.findtext("link")  or "").strip()
            desc  = re.sub(r"<[^>]+>", " ", item.findtext("description") or "")
            desc  = re.sub(r"\s+", " ", desc).strip()[:400]
            if title and link:
                jobs.append(make_job(title, link, desc, source, tag,
                                     _co(title, desc), _loc(title, desc)))
    except Exception as e:
        print(f"    [skip] {source}: {type(e).__name__}: {str(e)[:60]}")
    return jobs

def _co(title, desc):
    m = re.search(r"(?:at|@|-|–|by)\s+([A-Z][A-Za-z0-9\s&.,]+?)(?:\s*[-|,\n]|$)", title)
    if m: return m.group(1).strip()[:60]
    return "N/A"

def _loc(title, desc):
    combined = (title+" "+desc).lower()
    for c in ["Mumbai","Delhi","Bangalore","Bengaluru","Hyderabad","Pune","Chennai",
               "Kolkata","Kanpur","Lucknow","Noida","Gurgaon","Gurugram","Ahmedabad",
               "Jaipur","Indore","Remote","Pan-India","Hybrid"]:
        if c.lower() in combined: return c
    return "India"

# ─── SOURCE 1: GOOGLE NEWS RSS ─────────────────────────────────────────────
# Works from any IP. Indexes LinkedIn posts, company blogs, news, hiring posts.
GOOGLE_QUERIES = [
    # Hiring posts (catches LinkedIn + Twitter posts Google indexed)
    "we are hiring sales manager india startup",
    "hiring business development manager india",
    "hiring agritech sales india",
    "hiring rural sales manager india",
    "hiring GTM manager india startup",
    "we are hiring sales india MBA",
    "job opening sales manager india startup",
    "hiring agri sales india startup",
    # Company specific
    "DeHaat hiring sales india",
    "Ninjacart hiring india",
    "BharatAgri hiring sales",
    "FarMart hiring india",
    "Gramophone agri hiring",
    "WayCool hiring sales",
    "OfBusiness hiring sales india",
    "Udaan hiring business development",
    "Meesho hiring sales india",
    "Zetwerk hiring india",
    "Country Delight hiring",
    "Bijak hiring agri",
    # Role-specific news
    "sales manager job india startup 2025",
    "business development job india agritech",
    "agritech startup job india sales",
    "IIM MBA sales job india startup",
]

def fetch_google_news():
    jobs = []
    base = "https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
    for q in GOOGLE_QUERIES:
        encoded = q.replace(" ", "+")
        raw = fetch_rss(base.format(q=encoded), "Google/LinkedIn Posts", "startup")
        # Keep only hiring-relevant results
        filtered = [j for j in raw if any(kw in (j["title"]+j["description"]).lower()
                    for kw in ["hiring","vacancy","opening","job","career","recruit","apply","sales","bd ","agri","startup"])]
        jobs += filtered
        time.sleep(0.3)
    print(f"  Google News: {len(jobs)} posts")
    return jobs

# ─── SOURCE 2: REMOTIVE API ────────────────────────────────────────────────
# Free, no auth, remote-friendly jobs. Many Indian startups post here.
REMOTIVE_CATS = ["sales","business-development","management"]

def fetch_remotive():
    jobs = []
    for cat in REMOTIVE_CATS:
        try:
            url  = f"https://remotive.com/api/remote-jobs?category={cat}&limit=20"
            data = fetch_json(url)
            for j in data.get("jobs", []):
                title   = j.get("title","")
                company = j.get("company_name","N/A")
                desc    = re.sub(r"<[^>]+>"," ", j.get("description",""))[:400]
                link    = j.get("url","")
                loc     = j.get("candidate_required_location","Remote")
                # Include if India/Remote/Worldwide
                if any(kw in loc.lower() for kw in ["india","remote","worldwide","anywhere"]):
                    jobs.append(make_job(title, link, desc, "Remotive", "startup", company, loc))
        except Exception as e:
            print(f"    [skip] Remotive/{cat}: {e}")
        time.sleep(0.3)
    print(f"  Remotive: {len(jobs)} jobs")
    return jobs

# ─── SOURCE 3: ARBEITNOW API ──────────────────────────────────────────────
# Free, no auth. Good startup job coverage.
def fetch_arbeitnow():
    jobs = []
    queries = ["sales","business-development","account-manager","sales-manager"]
    for q in queries:
        try:
            url  = f"https://www.arbeitnow.com/api/job-board-api?search={q}&location=india"
            data = fetch_json(url)
            for j in data.get("data", [])[:10]:
                title   = j.get("title","")
                company = j.get("company_name","N/A")
                desc    = re.sub(r"<[^>]+>"," ", j.get("description",""))[:400]
                link    = j.get("url","")
                loc     = j.get("location","India")
                jobs.append(make_job(title, link, desc, "Arbeitnow", "startup", company, loc))
        except Exception as e:
            print(f"    [skip] Arbeitnow/{q}: {e}")
        time.sleep(0.3)
    print(f"  Arbeitnow: {len(jobs)} jobs")
    return jobs

# ─── SOURCE 4: JOBICY API ─────────────────────────────────────────────────
# Free, no auth. Startup/tech job board.
def fetch_jobicy():
    jobs = []
    try:
        url  = "https://jobicy.com/api/v0/remote-jobs?count=50&geo=india&tag=sales"
        data = fetch_json(url)
        for j in data.get("jobs", []):
            title   = j.get("jobTitle","")
            company = j.get("companyName","N/A")
            desc    = re.sub(r"<[^>]+>"," ", j.get("jobDescription",""))[:400]
            link    = j.get("url","")
            loc     = j.get("jobGeo","India")
            jobs.append(make_job(title, link, desc, "Jobicy", "startup", company, loc))
    except Exception as e:
        print(f"    [skip] Jobicy: {e}")
    print(f"  Jobicy: {len(jobs)} jobs")
    return jobs

# ─── SOURCE 5: ADZUNA INDIA API ───────────────────────────────────────────
# FREE — 1000 calls/month. Best India job coverage. Aggregates Naukri+Indeed.
# Get free key: developer.adzuna.com (2 min signup, instant key)
ADZUNA_QUERIES = [
    "Sales Manager", "Business Development Manager",
    "General Manager Sales", "Key Account Manager",
    "Regional Sales Manager", "GTM Manager",
    "AgriTech Sales", "Rural Sales Manager",
    "Sales Head Startup", "Corporate Sales Manager",
    "Agri Sales Manager", "Startup Sales Lead",
]

def fetch_adzuna():
    if not (ADZUNA_APP_ID and ADZUNA_APP_KEY):
        print("  Adzuna: no keys set (add ADZUNA_APP_ID + ADZUNA_APP_KEY for 1000 free India jobs/month)")
        return []
    jobs = []
    base = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    for q in ADZUNA_QUERIES:
        try:
            params = urlencode({
                "app_id":        ADZUNA_APP_ID,
                "app_key":       ADZUNA_APP_KEY,
                "results_per_page": 10,
                "what":          q,
                "content-type":  "application/json",
                "sort_by":       "date",
                "max_days_old":  1,
            })
            data = fetch_json(f"{base}?{params}")
            for j in data.get("results", []):
                title   = j.get("title","")
                company = j.get("company",{}).get("display_name","N/A")
                desc    = j.get("description","")[:400]
                link    = j.get("redirect_url","")
                loc     = j.get("location",{}).get("display_name","India")
                tag     = "agritech" if any(k in (title+desc).lower() for k in ["agri","farm","rural","crop"]) else "startup"
                jobs.append(make_job(title, link, desc, "Adzuna", tag, company, loc))
        except Exception as e:
            print(f"    [skip] Adzuna/{q}: {e}")
        time.sleep(0.4)
    print(f"  Adzuna: {len(jobs)} jobs")
    return jobs

# ─── SOURCE 6: JSEARCH (RapidAPI) ─────────────────────────────────────────
# Free tier: 200 calls/month. Searches LinkedIn + Indeed + Glassdoor + more.
# Get free key: rapidapi.com → search "JSearch" → Subscribe Free
JSEARCH_QUERIES = [
    "Sales Manager India", "Business Development Manager India",
    "AgriTech Sales India", "Startup Sales Lead India",
    "Key Account Manager India", "GTM Manager India startup",
    "Rural Sales Manager India", "General Manager Sales India",
]

def fetch_jsearch():
    if not JSEARCH_API_KEY:
        print("  JSearch: no key set (add JSEARCH_API_KEY for free LinkedIn+Indeed jobs)")
        return []
    jobs = []
    for q in JSEARCH_QUERIES[:6]:  # stay within free tier
        try:
            params = urlencode({"query": q, "page": "1", "num_pages": "1", "date_posted": "today"})
            url    = f"https://jsearch.p.rapidapi.com/search?{params}"
            data   = fetch_json(url, headers={
                "X-RapidAPI-Key":  JSEARCH_API_KEY,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            })
            for j in data.get("data", []):
                title   = j.get("job_title","")
                company = j.get("employer_name","N/A")
                desc    = j.get("job_description","")[:400]
                link    = j.get("job_apply_link","") or j.get("job_google_link","")
                loc     = j.get("job_city","") or j.get("job_country","India")
                tag     = "agritech" if any(k in (title+desc).lower() for k in ["agri","farm","rural"]) else "startup"
                jobs.append(make_job(title, link, desc, "JSearch(LinkedIn)", tag, company, loc))
        except Exception as e:
            print(f"    [skip] JSearch/{q}: {e}")
        time.sleep(0.5)
    print(f"  JSearch(LinkedIn+Indeed): {len(jobs)} jobs")
    return jobs

# ─── SOURCE 7: TWITTER/X VIA NITTER RSS ───────────────────────────────────
NITTER_INSTANCES = ["nitter.net", "nitter.privacydev.net", "nitter.poast.org"]
TWITTER_QUERIES  = [
    "hiring sales manager india startup",
    "hiring agritech india sales",
    "we are hiring business development india",
    "hiring rural sales india",
    "job opening sales india startup",
    "hiring GTM india",
]

def fetch_twitter():
    # Find working Nitter instance
    instance = None
    for ni in NITTER_INSTANCES:
        try:
            fetch_url(f"https://{ni}/search/rss?q=test", timeout=6)
            instance = ni
            break
        except:
            continue

    if not instance:
        print("  Twitter/X: Nitter unavailable — skipping")
        return []

    jobs = []
    for q in TWITTER_QUERIES:
        encoded = q.replace(" ","+")
        raw = fetch_rss(
            f"https://{instance}/search/rss?q={encoded}&f=tweets",
            "Twitter/X Hiring", "startup"
        )
        filtered = []
        for j in raw:
            text = (j["title"]+" "+j["description"]).lower()
            if (any(kw in text for kw in ["hiring","we're hiring","looking for","join","apply"]) and
                any(kw in text for kw in ["sales","bd","agri","startup","gtm","revenue"]) and
                not text.startswith("rt @")):
                filtered.append(j)
        jobs += filtered
        time.sleep(0.5)
    print(f"  Twitter/X: {len(jobs)} hiring posts")
    return jobs

# ─── MAIN FETCH ────────────────────────────────────────────────────────────
def fetch_all():
    pool, seen = [], set()

    def add(jobs):
        for j in jobs:
            if j["id"] not in seen:
                seen.add(j["id"])
                pool.append(j)

    print("🔍 Google News (hiring posts + LinkedIn indexed)...")
    add(fetch_google_news())

    print("🌐 Remotive (remote startup jobs)...")
    add(fetch_remotive())

    print("🌐 Arbeitnow (global startup jobs)...")
    add(fetch_arbeitnow())

    print("🌐 Jobicy (startup jobs)...")
    add(fetch_jobicy())

    print("🇮🇳 Adzuna India (best India coverage)...")
    add(fetch_adzuna())

    print("🔗 JSearch — LinkedIn + Indeed aggregator...")
    add(fetch_jsearch())

    print("🐦 Twitter/X hiring posts...")
    add(fetch_twitter())

    print(f"\n✅ Total unique jobs fetched: {len(pool)}")
    return pool[:MAX_TOTAL]

# ─── AI SCORING (Gemini 1.5 Flash — FREE) ─────────────────────────────────
def score(jobs):
    if not GEMINI_API_KEY:
        print("[WARN] No GEMINI_API_KEY — keyword scoring")
        return kw_score_all(jobs)

    import urllib.request, json as _j
    GEMINI_URL = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                  f"gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}")
    scored  = []
    batches = [jobs[i:i+10] for i in range(0, len(jobs), 10)]

    for i, batch in enumerate(batches):
        print(f"  Gemini scoring batch {i+1}/{len(batches)}...")
        jtext = "\n".join([
            f"JOB_{n+1}: {j['title']} | {j['company']} | {j['location']} | agri={j['is_agri']}\nDESC: {j['description'][:200]}"
            for n, j in enumerate(batch)
        ])
        prompt = f"""Senior Indian recruiter. Score jobs for this MBA candidate (1-10).

CANDIDATE:
{CANDIDATE_PROFILE}

RULES:
- AgriTech startup sales/BD = 9-10 (rare IIM MBA + deep agri combo)
- Rural/Farm/FPO startup sales = 8.5-9.5
- FMCG sales UP/Bihar = 7.5-9
- Startup sales lead Series A-C = 7-8.5
- Large corporate junior role = 5-7
- Needs 5+ years exp = 3-5

JOBS:
{jtext}

Reply ONLY with JSON array:
[{{"job":"JOB_1","score":8.5,"reason":"specific 1-line reason"}}]"""

        try:
            payload = _j.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1200,
                                     "responseMimeType": "application/json"}
            }).encode()
            req = urllib.request.Request(GEMINI_URL, data=payload,
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=40) as r:
                result = _j.loads(r.read())
                text   = result["candidates"][0]["content"]["parts"][0]["text"]
                text   = re.sub(r"```json|```", "", text).strip()
                m      = re.search(r'\[.*\]', text, re.DOTALL)
                if m:
                    for s in _j.loads(m.group()):
                        num = re.search(r'\d+', s.get("job","0"))
                        if num:
                            idx = int(num.group()) - 1
                            if 0 <= idx < len(batch):
                                batch[idx]["score"]  = float(s.get("score", 5))
                                batch[idx]["reason"] = s.get("reason", "")
        except Exception as e:
            print(f"    [WARN] Gemini: {e}")
            for j in batch:
                j["score"]  = kw_score(j)
                j["reason"] = "Keyword scoring"
        scored += batch
        time.sleep(1.0)
    return scored

def kw_score(j):
    text = (j["title"]+" "+j["description"]+" "+j.get("tag","")).lower()
    s    = 3.0
    for kw in ["agritech","agri","rural","farm","agricultural","startup","series a","series b",
               "sales manager","business development","key account","general manager","gtm","iim"]:
        if kw in text: s += 0.9
    for kw in ["sales","bd","revenue","b2b","b2c","fmcg","growth","account"]:
        if kw in text: s += 0.3
    if j.get("is_agri"):    s += 1.8
    if j.get("is_startup"): s += 0.6
    return min(round(s,1), 10.0)

def kw_score_all(jobs):
    for j in jobs:
        j["score"]  = kw_score(j)
        j["reason"] = "Keyword scoring"
    return jobs

# ─── SAVE ──────────────────────────────────────────────────────────────────
def save(jobs):
    jobs.sort(key=lambda j: j["score"], reverse=True)
    top    = jobs[:60]
    agri   = sum(1 for j in top if j.get("is_agri"))
    startup= sum(1 for j in top if j.get("is_startup"))
    sources= {}
    for j in top: sources[j["source"]] = sources.get(j["source"],0)+1

    with open(OUTPUT_FILE,"w") as f:
        json.dump({
            "generated_at":     datetime.now(timezone.utc).isoformat(),
            "total_fetched":    len(jobs),
            "total_shown":      len(top),
            "agri_jobs":        agri,
            "startup_jobs":     startup,
            "source_breakdown": sources,
            "jobs":             top,
        }, f, indent=2)

    print(f"\n{'='*55}")
    print(f"✅ {len(top)} jobs saved | 🌾 Agri:{agri} 🚀 Startup:{startup}")
    print(f"📊 Sources: {sources}")
    print("🏆 Top 5:")
    for j in top[:5]:
        icon = "🌾" if j.get("is_agri") else ("🚀" if j.get("is_startup") else "🏢")
        print(f"  {icon} [{j['score']}] {j['title']} @ {j['company']}")
    print('='*55)

# ─── RUN ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{'='*55}")
    print(f"  Job Bot v3.0 — Soham Katiyar | IIM K MBA")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*55}\n")
    jobs = fetch_all()
    print(f"\n🤖 Scoring {len(jobs)} jobs with Gemini...")
    jobs = score(jobs)
    save(jobs)
