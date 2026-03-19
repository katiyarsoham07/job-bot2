"""
Job Fetcher + AI Scorer — Soham Katiyar v2.1 (Gemini Edition)
Sources: LinkedIn, Indeed, Instahyre, Cutshort, Wellfound, IIMJobs, YC, Shine
AgriTech startups: 20 named companies searched individually
Growth startups: 15 named companies searched individually
AI Scoring: Google Gemini 1.5 Flash (FREE — 1500 req/day)
Profile: IIM Kozhikode MBA | 19 months experience | Agri + Sales background
"""

import json, os, re, time, hashlib
from datetime import datetime, timezone
from urllib.request import urlopen, Request
import xml.etree.ElementTree as ET

# ─── PROFILE ───────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

CANDIDATE_PROFILE = """
Name: Soham Katiyar
Education: MBA - IIM Kozhikode (2023-2025) | B.Sc. Agriculture Gold Medalist (90.41%)
Total Experience: 19 months
Current/Last Role: General Manager - Sales & Business Development, RAAM Group (JSW MG Motors)

Work History:
- General Manager, RAAM Group JSW MG Motors (Apr-Dec 2025): Led 32-member team, 20% revenue
  growth, 600 home test drives, 130 bookings/month, 50% complaint reduction, B2B partnerships
- UPMIP Consultant, VK Packwell (Dec 2025-Present): Agri micro-irrigation, 27 districts UP,
  50-acre farm development, KVK + Panchayat Sahayak network, commission-based dealer model
- Project Manager, ICAR-ATARI (Nov 2022-Jun 2023): INR 6.5 Mn project, 52 KVKs,
  5000+ farmers trained, 27 districts Uttar Pradesh, natural farming
- Project Manager, ICAR-IIPR (Apr-Aug 2022): Crop trials, 30% facility revenue growth,
  2000+ farmers, anti-wilt product launch, Black Gram adoption Madhya Pradesh
- Growth Consultant, FarmerFace (Oct-Dec 2024): 10% UP sales growth, 15 new dealerships,
  GTM strategy UP & Bihar, IAS & Govt partnerships, organic product launches
- Sales Intern, Bajaj Capital (Apr-Jun 2024): INR 1 Mn MF SIP sales in 2 months, 90% repeat

Key Skills: Corporate Sales, B2B/B2C Sales, GTM Strategy, Key Account Management,
            Channel & Distributor Management, P&L Ownership, Team Leadership (32 people),
            Market Penetration, Revenue Growth, CRM, Agri domain expertise, Rural markets,
            Government & KVK partnerships, Dealer network building, Commission model design

Location: Kanpur, UP (Pan-India open, remote ok, relocation for right role)

Target Roles: Sales Manager, Business Development Manager, GM Sales, Strategy Manager,
              Key Account Manager, GTM Manager, Regional Sales Manager, Agri Sales Manager,
              Rural Sales Manager, Startup Sales Lead, Growth Manager

Target Industries (Priority):
1. AgriTech Startups — BEST FIT (rare IIM MBA + deep agri domain expertise combo)
2. Rural-tech / Input / Micro-irrigation / FPO-linked startups
3. FMCG — especially UP/Bihar/rural market distribution
4. Automotive / EV startups
5. SaaS / B2B startups needing first sales leaders
6. Fintech / Financial Services
Salary: 12-20 LPA (IIM K MBA premium, 19 months experience)
"""

# ─── SEARCH QUERIES ────────────────────────────────────────────────────────
CORE_QUERIES = [
    "Sales+Manager", "Business+Development+Manager",
    "General+Manager+Sales", "Key+Account+Manager",
    "Regional+Sales+Manager", "GTM+Manager",
    "Corporate+Sales+Manager", "Sales+Strategy+India",
]

STARTUP_QUERIES = [
    "Sales+Lead+Startup+India", "Business+Development+Startup",
    "Revenue+Lead+Startup+India", "Growth+Manager+Startup",
    "Head+Sales+Startup+India", "Sales+Manager+Series+A",
    "B2B+Sales+Startup+India", "Market+Expansion+India+Startup",
]

AGRI_QUERIES = [
    "AgriTech+Sales+Manager+India", "Agriculture+Business+Development+India",
    "Rural+Sales+Manager+India", "Agri+Input+Sales+India",
    "Farm+Sales+Manager+India", "Agri+Startup+Sales+India",
    "Micro+Irrigation+Sales+India", "Rural+Business+Development",
    "Agri+Key+Account+Manager", "FPO+Sales+Manager",
]

# 20 AgriTech startups that post regularly on LinkedIn
AGRI_STARTUPS = [
    ("DeHaat",         "DeHaat+Sales+Manager"),
    ("Ninjacart",      "Ninjacart+Business+Development"),
    ("AgroStar",       "AgroStar+Sales+Manager"),
    ("Bighaat",        "Bighaat+Sales"),
    ("FarMart",        "FarMart+Business+Development"),
    ("Jai Kisan",      "Jai+Kisan+Sales"),
    ("Gramophone",     "Gramophone+Agri+Sales"),
    ("BharatAgri",     "BharatAgri+Sales"),
    ("WayCool",        "WayCool+Sales+Manager"),
    ("CropIn",         "CropIn+Business+Development"),
    ("Samunnati",      "Samunnati+Sales"),
    ("Arya.ag",        "Arya+Ag+Sales"),
    ("Fyllo",          "Fyllo+Sales"),
    ("Eruvaka",        "Eruvaka+Sales+Manager"),
    ("Krishify",       "Krishify+Sales"),
    ("Captain Fresh",  "Captain+Fresh+Sales"),
    ("Stellapps",      "Stellapps+Business+Development"),
    ("KhetiBadi",      "KhetiBadi+Sales"),
    ("Absolute",       "Absolute+AgriTech+Sales"),
    ("Country Delight","Country+Delight+Sales"),
]

# 15 growth startups (Series A-C) with active sales hiring
GROWTH_STARTUPS = [
    ("Razorpay",       "Razorpay+Sales+Manager"),
    ("OfBusiness",     "OfBusiness+Sales"),
    ("Udaan",          "Udaan+Sales+Manager"),
    ("Meesho",         "Meesho+Business+Development"),
    ("Zetwerk",        "Zetwerk+Sales"),
    ("Infra.Market",   "Infra+Market+Sales"),
    ("Juspay",         "Juspay+Sales"),
    ("Licious",        "Licious+Sales+Manager"),
    ("Milkbasket",     "Milkbasket+Sales"),
    ("MediBuddy",      "MediBuddy+Business+Development"),
    ("Daalchini",      "Daalchini+Sales"),
    ("Bijak",          "Bijak+Agri+Sales"),
    ("Ninjacart",      "Ninjacart+Sales+Manager"),
    ("Waycool",        "Waycool+Growth"),
    ("Animall",        "Animall+Sales"),
]

OUTPUT_FILE   = "jobs.json"
MAX_PER_QUERY = 10
MAX_TOTAL     = 130

# ─── FETCHERS ──────────────────────────────────────────────────────────────
def fetch_rss(url, source, tag="general", timeout=15):
    jobs = []
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 JobBot/2.0"})
        with urlopen(req, timeout=timeout) as r:
            content = r.read()
        root    = ET.fromstring(content)
        channel = root.find("channel") or root
        for item in channel.findall("item")[:MAX_PER_QUERY]:
            title = (item.findtext("title") or "").strip()
            link  = (item.findtext("link")  or "").strip()
            desc  = re.sub(r"<[^>]+>", " ", item.findtext("description") or "")
            desc  = re.sub(r"\s+", " ", desc).strip()[:400]
            pub   = (item.findtext("pubDate") or datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")).strip()
            if title and link:
                jobs.append({
                    "id":          hashlib.md5(link.encode()).hexdigest()[:10],
                    "title":       title,
                    "link":        link,
                    "description": desc,
                    "published":   pub,
                    "source":      source,
                    "tag":         tag,
                    "score":       0,
                    "reason":      "",
                    "company":     _company(title, desc),
                    "location":    _location(title, desc),
                    "is_startup":  tag in ("startup","agritech"),
                    "is_agri":     tag == "agritech",
                })
    except Exception as e:
        print(f"    [skip] {source}: {e}")
    return jobs


def _company(title, desc):
    m = re.search(r"(?:at|@|-|–|by)\s+([A-Z][A-Za-z0-9\s&.,]+?)(?:\s*[-|,\n]|$)", title)
    if m: return m.group(1).strip()[:60]
    m = re.search(r"Company[:\s]+([A-Z][A-Za-z0-9\s&.,]+?)(?:\s*[\n|,]|$)", desc)
    if m: return m.group(1).strip()[:60]
    return "N/A"


def _location(title, desc):
    combined = (title+" "+desc).lower()
    for c in ["Mumbai","Delhi","Bangalore","Bengaluru","Hyderabad","Pune","Chennai",
               "Kolkata","Kanpur","Lucknow","Noida","Gurgaon","Gurugram","Ahmedabad",
               "Jaipur","Indore","Bhopal","Patna","Remote","Pan-India","Hybrid"]:
        if c.lower() in combined: return c
    return "India"


def li(q, tag="general"):
    url = f"https://www.linkedin.com/jobs/search/?keywords={q}&location=India&f_TPR=r86400&format=rss"
    return fetch_rss(url, "LinkedIn", tag)

def indeed(q, tag="general"):
    return fetch_rss(f"https://in.indeed.com/rss?q={q}&l=India&fromage=1&sort=date", "Indeed", tag)

def instahyre(path, tag="general"):
    return fetch_rss(f"https://www.instahyre.com/jobs/{path}/rss/", "Instahyre", tag)

def cutshort(path, tag="general"):
    return fetch_rss(f"https://cutshort.io/jobs/{path}/rss", "Cutshort", tag)

def wellfound():
    jobs = []
    for path, tag in [("sales-manager","startup"),("business-development","startup"),("sales","startup")]:
        jobs += fetch_rss(f"https://wellfound.com/role/r/{path}/india/rss", "Wellfound", tag)
    return jobs

def iimjobs():
    jobs = []
    for q in ["Sales+Manager","Business+Development","General+Manager+Sales"]:
        jobs += fetch_rss(f"https://www.iimjobs.com/jobs/search/?q={q}&format=rss", "IIMJobs", "premium")
    return jobs

def yc():
    j = fetch_rss("https://news.ycombinator.com/jobs.rss", "YC Jobs", "startup")
    return [x for x in j if any(k in (x["title"]+x["description"]).lower()
                                  for k in ["india","remote","sales","business dev","gtm"])]

def shine():
    jobs = []
    for cat in ["sales-and-marketing","business-development"]:
        jobs += fetch_rss(f"https://www.shine.com/rss/category/{cat}", "Shine", "general")
    return jobs

# ─── MAIN FETCH ────────────────────────────────────────────────────────────
def fetch_all():
    pool, seen = [], set()

    def add(jobs):
        for j in jobs:
            if j["id"] not in seen:
                seen.add(j["id"])
                pool.append(j)

    print("📡 LinkedIn — core roles...")
    for q in CORE_QUERIES[:5]:
        add(li(q, "general")); print(f"   {q}: done"); time.sleep(1.2)

    print("📡 LinkedIn — startup queries...")
    for q in STARTUP_QUERIES[:4]:
        add(li(q, "startup")); print(f"   {q}: done"); time.sleep(1.2)

    print("🌾 LinkedIn — agri queries...")
    for q in AGRI_QUERIES[:4]:
        add(li(q, "agritech")); print(f"   {q}: done"); time.sleep(1.2)

    print("📡 Indeed — core roles...")
    for q in CORE_QUERIES:
        add(indeed(q, "general")); time.sleep(0.5)

    print("🚀 Indeed — startup queries...")
    for q in STARTUP_QUERIES:
        add(indeed(q, "startup")); time.sleep(0.5)

    print("🌾 Indeed — agri queries...")
    for q in AGRI_QUERIES:
        add(indeed(q, "agritech")); time.sleep(0.5)

    print("🌾 AgriTech startups (individual company search)...")
    for company, query in AGRI_STARTUPS:
        j = indeed(query, "agritech")
        for x in j:
            if x["company"] == "N/A": x["company"] = company
        add(j); print(f"   {company}: {len(j)} jobs"); time.sleep(0.4)

    print("🚀 Growth startups (individual company search)...")
    for company, query in GROWTH_STARTUPS:
        j = indeed(query, "startup")
        for x in j:
            if x["company"] == "N/A": x["company"] = company
        add(j); time.sleep(0.3)

    print("📡 Instahyre...")
    for path, tag in [("sales-manager","general"),("business-development","startup"),("agri","agritech")]:
        add(instahyre(path, tag))

    print("📡 Cutshort (startup-heavy)...")
    for path in ["sales","business-development","agri"]:
        add(cutshort(path, "startup"))

    print("📡 Wellfound / AngelList...")
    add(wellfound())

    print("📡 IIMJobs (MBA premium)...")
    add(iimjobs())

    print("📡 YC Jobs...")
    add(yc())

    print("📡 Shine...")
    add(shine())

    print(f"\n✅ Total unique: {len(pool)}")
    return pool[:MAX_TOTAL]


# ─── AI SCORING ────────────────────────────────────────────────────────────
def score(jobs):
    """Score jobs using Google Gemini 1.5 Flash (FREE — 1500 req/day free tier)."""
    if not GEMINI_API_KEY:
        print("[WARN] No GEMINI_API_KEY — using keyword scoring")
        print("[INFO] Get free key at: aistudio.google.com/apikey")
        return kw_score_all(jobs)

    import urllib.request, json as _j
    # Gemini 1.5 Flash endpoint — fastest, cheapest, free tier
    GEMINI_URL = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    )
    scored  = []
    batches = [jobs[i:i+10] for i in range(0, len(jobs), 10)]

    for i, batch in enumerate(batches):
        print(f"  Batch {i+1}/{len(batches)} — Gemini Flash scoring...")
        jtext = "\n".join([
            f"JOB_{n+1}: {j['title']} | {j['company']} | {j['location']} | {j['source']} | agri={j['is_agri']}\n"
            f"DESC: {j['description'][:250]}"
            for n, j in enumerate(batch)
        ])

        prompt = f"""You are a senior recruiter specialising in MBA sales hires in India.
Score each job for the following candidate. Be realistic — 19 months exp is early career.

CANDIDATE:
{CANDIDATE_PROFILE}

SCORING RULES:
- AgriTech startup + sales/BD role = 9-10 (rare IIM MBA + deep agri combo, highest priority)
- Rural/Farm-input/FPO/Micro-irrigation startup sales = 8.5-9.5
- FMCG sales (UP/Bihar/rural focus) = 7.5-9
- General startup sales lead (Series A-C) = 7-8.5
- Large corporate junior sales role = 5-7 (may be underleveled for IIM K MBA)
- Role requires 5+ years experience = 3-5 (realistic mismatch, flag it)
- AgriTech domain expertise is a KEY differentiator for this candidate — reward strongly

JOBS TO SCORE:
{jtext}

Respond ONLY with a valid JSON array — no markdown, no extra text:
[{{"job":"JOB_1","score":8.5,"reason":"Specific reason: company type, role fit, agri/startup relevance"}},...]"""

        try:
            payload = _j.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,          # low temp = consistent scoring
                    "maxOutputTokens": 1200,
                    "responseMimeType": "application/json"   # forces clean JSON output
                }
            }).encode()

            req = urllib.request.Request(
                GEMINI_URL, data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=40) as r:
                result   = _j.loads(r.read())
                # Gemini response structure
                text     = result["candidates"][0]["content"]["parts"][0]["text"]
                # Strip any accidental markdown fences
                text     = re.sub(r"```json|```", "", text).strip()
                m        = re.search(r'\[.*\]', text, re.DOTALL)
                if m:
                    scores = _j.loads(m.group())
                    for s in scores:
                        num = re.search(r'\d+', s.get("job","0"))
                        if num:
                            idx = int(num.group()) - 1
                            if 0 <= idx < len(batch):
                                batch[idx]["score"]  = float(s.get("score", 5))
                                batch[idx]["reason"] = s.get("reason", "")

        except Exception as e:
            print(f"  [WARN] Gemini error: {e} — keyword fallback for this batch")
            for j in batch:
                j["score"]  = kw_score(j)
                j["reason"] = "Keyword scoring (Gemini unavailable)"

        scored += batch
        time.sleep(1.0)   # Gemini Flash rate limit: 15 req/min on free tier

    return scored


def kw_score(j):
    text  = (j["title"]+" "+j["description"]+" "+j.get("tag","")).lower()
    s     = 3.0
    for kw in ["agritech","agri","rural sales","farm","agricultural","agro","startup",
                "series a","series b","sales manager","business development","key account",
                "general manager","gtm","regional sales","iim"]:
        if kw in text: s += 0.8
    for kw in ["sales","bd","account","revenue","b2b","b2c","fmcg","growth"]:
        if kw in text: s += 0.3
    if j.get("is_agri"):    s += 1.8
    if j.get("is_startup"): s += 0.6
    return min(round(s,1), 10.0)


def kw_score_all(jobs):
    for j in jobs:
        j["score"]  = kw_score(j)
        j["reason"] = "Keyword scoring (set GEMINI_API_KEY for free AI scoring)"
    return jobs


# ─── SAVE ──────────────────────────────────────────────────────────────────
def save(jobs):
    jobs.sort(key=lambda j: j["score"], reverse=True)
    top = jobs[:60]
    sources = {}
    agri = startup = 0
    for j in top:
        sources[j["source"]] = sources.get(j["source"],0)+1
        if j.get("is_agri"):    agri    += 1
        if j.get("is_startup"): startup += 1

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
    print(f"✅ {len(top)} jobs saved  |  🌾 Agri: {agri}  🚀 Startup: {startup}")
    print("🏆 Top 8:")
    for j in top[:8]:
        icon = "🌾" if j.get("is_agri") else ("🚀" if j.get("is_startup") else "🏢")
        print(f"  {icon} [{j['score']}] {j['title']} @ {j['company']} ({j['source']})")
    print('='*55)


# ─── RUN ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{'='*55}")
    print(f"  Job Bot v2.0 — Soham Katiyar | IIM K MBA")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Focus: AgriTech Startups + Sales/BD Roles")
    print(f"{'='*55}\n")
    jobs = fetch_all()
    print(f"\n🤖 AI scoring {len(jobs)} jobs...")
    jobs = score(jobs)
    save(jobs)
