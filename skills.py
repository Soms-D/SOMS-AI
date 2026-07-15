"""Skills Module for SOMS

Real, local-first capabilities that make SOMS feel like a helpful human
companion: open files, play music, search/play YouTube, play movies, check
the weather, and check email. Actions are performed on the user's machine
via safe subprocess calls (no shell injection). Where a network service is
needed (weather, YouTube, email) it degrades gracefully and reports clearly.
"""

import logging
import os
import subprocess
import urllib.parse
import urllib.request
import json
import base64
import tempfile

logger = logging.getLogger('Skills')

OPEN = 'xdg-open'

# Camera privacy state (SOMS will not access the camera while disabled).
_camera_enabled = True


def set_camera_enabled(on):
    global _camera_enabled
    _camera_enabled = bool(on)


def camera_enabled():
    return _camera_enabled


def _run(cmd, **kw):
    """Run a command list safely, returning (returncode, out)."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, **kw)
        return proc.returncode, (proc.stdout or proc.stderr).strip()
    except FileNotFoundError:
        return 127, f"command not found: {cmd[0]}"
    except Exception as e:
        return 1, str(e)


def _open(target):
    rc, out = _run([OPEN, target])
    return rc == 0, target, out


# --------------------------------------------------------------------------
# Files
# --------------------------------------------------------------------------

def open_file(query=None):
    """Open a specific file/folder, or the user's home if no query."""
    home = os.path.expanduser('~')
    if not query:
        ok, tgt, out = _open(home)
        return ("Opened your home folder." if ok else f"Couldn't open home folder: {out}")
    q = query.strip().strip('"\'')
    # Direct path
    if os.path.exists(q):
        ok, tgt, out = _open(q)
        return (f"Opened {q}." if ok else f"Found it but couldn't open: {out}")
    # Search under home for a matching name
    found = []
    for root, dirs, files in os.walk(home):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files + dirs:
            if q.lower() in f.lower():
                found.append(os.path.join(root, f))
                if len(found) >= 5:
                    break
        if len(found) >= 5:
            break
    if found:
        target = found[0]
        ok, tgt, out = _open(target)
        more = "" if len(found) == 1 else f" (also found {len(found)-1} more)"
        return (f"Opened {target}{more}." if ok else f"Found {target} but couldn't open: {out}")
    return f"I couldn't find a file matching '{q}'. Tell me the full path and I'll open it."


# --------------------------------------------------------------------------
# Music / YouTube / Movies
# --------------------------------------------------------------------------

def _yt_url(query):
    return "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)


def play_music(query=None):
    """Play music: open a YouTube search for the song, or the local player."""
    if query:
        url = _yt_url(f"{query} music")
        ok, tgt, out = _open(url)
        return (f"Playing music for '{query}' on YouTube." if ok
                else f"I tried to open YouTube music for '{query}' but: {out}")
    # No query -> just open the music player / library
    for player in (['rhythmbox'], ['vlc'], ['xdg-open', os.path.expanduser('~/.local/share')]):
        rc, _ = _run(player)
        if rc != 127:
            return "Opened your music player."
    ok, tgt, out = _open(os.path.expanduser('~'))
    return ("Opened your home folder — pick your music." if ok
            else "I couldn't launch a music player.")


def youtube(query=None):
    if not query:
        ok, tgt, out = _open("https://www.youtube.com")
        return "Opened YouTube." if ok else f"Couldn't open YouTube: {out}"
    url = _yt_url(query)
    ok, tgt, out = _open(url)
    return (f"Opened YouTube for '{query}'." if ok else f"Couldn't open YouTube: {out}")


def play_movie(query=None):
    if not query:
        return "Tell me the movie or show you want and I'll find it on YouTube."
    url = _yt_url(f"{query} full movie")
    ok, tgt, out = _open(url)
    return (f"Searching for '{query}' to watch." if ok else f"Couldn't open it: {out}")


def search_web(query):
    url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    ok, tgt, out = _open(url)
    return (f"Searching the web for '{query}'." if ok else f"Couldn't search: {out}")


# --------------------------------------------------------------------------
# Weather (open-meteo, no API key required)
# --------------------------------------------------------------------------

def check_weather(city=None, config=None):
    try:
        if city:
            g = urllib.request.urlopen(
                "https://geocoding-api.open-meteo.com/v1/search?name="
                + urllib.parse.quote(city) + "&count=1", timeout=10)
            geo = json.load(g)
            if not geo.get('results'):
                return f"I couldn't find a city called '{city}'."
            r = geo['results'][0]
            lat, lon = r['latitude'], r['longitude']
            place = r.get('name', city)
        else:
            # Fallback: configured city or a generic default
            cfg_city = (config.get('location', 'city', default=None) if config else None)
            if cfg_city:
                return check_weather(cfg_city, config)
            lat, lon, place = 40.71, -74.01, "New York"
        f = urllib.request.urlopen(
            "https://api.open-meteo.com/v1/forecast?latitude=" + str(lat)
            + "&longitude=" + str(lon)
            + "&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m,relative_humidity_2m",
            timeout=10)
        data = json.load(f)['current']
        code = data.get('weather_code', 0)
        desc = _weather_desc(code)
        return (f"Weather in {place}: {desc}, {data['temperature_2m']:.0f}°C "
                f"(feels like {data['apparent_temperature']:.0f}°C), "
                f"humidity {data['relative_humidity_2m']}%, wind {data['wind_speed_10m']:.0f} km/h.")
    except Exception as e:
        return f"I couldn't fetch the weather right now ({e}). I'll try again later if you ask."


def _weather_desc(code):
    table = {
        0: 'clear sky', 1: 'mainly clear', 2: 'partly cloudy', 3: 'overcast',
        45: 'fog', 48: 'fog', 51: 'light drizzle', 53: 'drizzle', 55: 'heavy drizzle',
        61: 'light rain', 63: 'rain', 65: 'heavy rain', 71: 'light snow',
        73: 'snow', 75: 'heavy snow', 80: 'rain showers', 81: 'showers', 82: 'violent showers',
        95: 'thunderstorm', 96: 'thunderstorm with hail', 99: 'thunderstorm with hail',
    }
    return table.get(code, 'unknown')


# --------------------------------------------------------------------------
# Web research (best-effort, network required) — used to improve factual
# answers when the local LLM is unsure. Degrades gracefully when offline.
# --------------------------------------------------------------------------

def web_answer(query, max_snippets=3):
    """Fetch a short, sourced answer snippet for a factual query.

    Returns a string with extracted result snippets, or an empty string when
    the network is unavailable / scraping fails (callers degrade gracefully).
    """
    try:
        import requests
        from urllib.parse import quote
    except Exception:
        return ""
    try:
        url = "https://html.duckduckgo.com/html/?q=" + quote(query)
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; SOMS/1.0)'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return ""
        html = resp.text
        # Extract result snippet text from DuckDuckGo HTML results.
        snippets = []
        import re
        # Each result snippet lives in a <a class="result__snippet"> ... </a>
        for m in re.finditer(r'class="result__snippet"[^>]*>(.*?)</a>', html, re.S):
            text = re.sub(r'<[^>]+>', '', m.group(1))
            text = re.sub(r'\s+', ' ', text).strip()
            if text:
                snippets.append(text)
            if len(snippets) >= max_snippets:
                break
        if not snippets:
            return ""
        return "\n".join(f"- {s}" for s in snippets)
    except Exception:
        return ""


# --------------------------------------------------------------------------
# Email (opens mail client; optional IMAP summary if configured)
# --------------------------------------------------------------------------

def check_email(config=None):
    # Prefer opening the user's mail client / Gmail
    ok, tgt, out = _open("https://mail.google.com")
    base = "Opened your email in the browser." if ok else "I couldn't open your email client."
    # Optional IMAP unread summary
    if config:
        user = config.get('email', 'user', default=None)
        pw = config.get('email', 'password', default=None)
        server = config.get('email', 'server', default=None)
        if user and pw and server:
            try:
                import imaplib
                con = imaplib.IMAP4_SSL(server)
                con.login(user, pw)
                con.select('INBOX')
                _, data = con.search(None, 'UNSEEN')
                unread = len(data[0].split()) if data and data[0] else 0
                con.logout()
                return f"{base} You have {unread} unread message(s)."
            except Exception as e:
                logger.debug(f"IMAP check failed: {e}")
    return base


# --------------------------------------------------------------------------
# Camera / vision
# --------------------------------------------------------------------------

def capture_frame(path=None, device=0):
    """Grab a single frame from a webcam. Tries OpenCV, then fswebcam, then ffmpeg.

    Returns (ok, path, detail). `path` is the saved image file when ok.
    """
    if path is None:
        fd, path = tempfile.mkstemp(suffix='.jpg')
        os.close(fd)

    # 1) OpenCV
    try:
        import cv2  # type: ignore
        cap = cv2.VideoCapture(device)
        if cap.isOpened():
            for _ in range(10):  # let exposure settle
                ok, frame = cap.read()
                if ok:
                    break
            cap.release()
            if ok:
                cv2.imwrite(path, frame)
                return True, path, ""
        else:
            cap.release()
    except Exception as e:
        logger.debug(f"OpenCV capture failed: {e}")

    # 2) fswebcam
    rc, out = _run(['fswebcam', '-r', '640x480', '--no-banner', '-d',
                    f'/dev/video{device}', path])
    if rc == 0 and os.path.exists(path) and os.path.getsize(path) > 1000:
        return True, path, ""

    # 3) ffmpeg
    rc, out = _run(['ffmpeg', '-y', '-f', 'v4l2', '-i', f'/dev/video{device}',
                    '-frames', '1', path])
    if rc == 0 and os.path.exists(path) and os.path.getsize(path) > 1000:
        return True, path, ""

    return False, path, "No camera found or no capture tool (OpenCV/fswebcam/ffmpeg) available."


def describe_camera(query=None, llm=None, device=0):
    """Capture a frame and describe what the camera sees using a vision model."""
    if not camera_enabled():
        return ("Camera access is currently disabled (privacy mode). "
                "Say 'enable camera' or 'start camera' to turn it back on.")
    if llm is None:
        return "Vision module requires an active LLM with vision support. Ensure Ollama is running with a vision model (e.g., llava)."
    vmodel = llm.vision_model()
    if not vmodel:
        return ("I don't have a vision model loaded. Install one locally (e.g. "
                "`ollama pull llava` or `ollama pull moondream`) and I'll describe "
                "exactly what the camera sees.")

    ok, path, detail = capture_frame(device=device)
    if not ok:
        return f"I couldn't access the camera. ({detail})"

    try:
        with open(path, 'rb') as f:
            img_b64 = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        return f"I captured the image but couldn't read it: {e}"

    prompt = (query or
              "Describe in detail what you see in this camera image. Identify any people, "
              "objects, activities, text, and anything unusual or noteworthy. Be specific "
              "and factual.")
    messages = [
        {'role': 'system',
         'content': "You are SOMS's vision module. Describe camera footage clearly, "
                    "factually, and helpfully for the user."},
        {'role': 'user', 'content': prompt},
    ]
    try:
        description = llm.chat(messages, model=vmodel, images=[img_b64])
        if not description:
            description = "I looked, but I couldn't make out details from the image."
        return f"[Camera {device}] {description}"
    except Exception as e:
        return f"I accessed the camera but failed to analyze the image: {e}"
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def stop_cameras():
    """Disable all camera access (privacy mode)."""
    set_camera_enabled(False)
    return ("All cameras stopped. I won't access the camera until you re-enable it. "
            "Say 'enable camera' or 'start camera' when you want me to look again.")


def start_cameras():
    """Re-enable camera access."""
    set_camera_enabled(True)
    return "Camera access re-enabled. I can look through the camera again when you ask."


_LLM_COUNCIL_NOTES = r"""
---
name: llm-council
description: "Run any question, idea, or decision through a council of 5 AI advisors who independently analyze it, peer-review each other anonymously, and synthesize a final verdict. Based on Karpathy's LLM Council methodology. MANDATORY TRIGGERS: 'council this', 'run the council', 'war room this', 'pressure-test this', 'stress-test this', 'debate this'. STRONG TRIGGERS (use when combined with a real decision or tradeoff): 'should I X or Y', 'which option', 'what would you do', 'is this the right move', 'validate this', 'get multiple perspectives', 'I can't decide', 'I'm torn between'. Do NOT trigger on simple yes/no questions, factual lookups, or casual 'should I' without a meaningful tradeoff (e.g. 'should I use markdown' is not a council question). DO trigger when the user presents a genuine decision with stakes, multiple options, and context that suggests they want it pressure-tested from multiple angles."
---

# LLM Council

You ask one AI a question, you get one answer. That answer might be great. It might be mid. You have no way to tell because you only saw one perspective.

The council fixes this. It runs your question through 5 independent advisors, each thinking from a fundamentally different angle. Then they review each other's work. Then a chairman synthesizes everything into a final recommendation that tells you where the advisors agree, where they clash, and what you should actually do.

This is adapted from Andrej Karpathy's LLM Council. He dispatches queries to multiple models, has them peer-review each other anonymously, then a chairman produces the final answer. We do the same thing inside Claude using sub-agents with different thinking lenses instead of different models.

---

## when to run the council

The council is for questions where being wrong is expensive.

Good council questions:
- "Should I launch a $97 workshop or a $497 course?"
- "Which of these 3 positioning angles is strongest?"
- "I'm thinking of pivoting from X to Y. Am I crazy?"
- "Here's my landing page copy. What's weak?"
- "Should I hire a VA or build an automation first?"

Bad council questions:
- "What's the capital of France?" (one right answer, no need for perspectives)
- "Write me a tweet" (creation task, not a decision)
- "Summarize this article" (processing task, not judgment)

The council shines when there's genuine uncertainty and the cost of a bad call is high. If you already know the answer and just want validation, the council will likely tell you things you don't want to hear. That's the point.

---

## the five advisors

Each advisor thinks from a different angle. They're not job titles or personas. They're thinking styles that naturally create tension with each other.

### 1. The Contrarian
Actively looks for what's wrong, what's missing, what will fail. Assumes the idea has a fatal flaw and tries to find it. If everything looks solid, digs deeper. The Contrarian is not a pessimist. They're the friend who saves you from a bad deal by asking the questions you're avoiding.

### 2. The First Principles Thinker
Ignores the surface-level question and asks "what are we actually trying to solve here?" Strips away assumptions. Rebuilds the problem from the ground up. Sometimes the most valuable council output is the First Principles Thinker saying "you're asking the wrong question entirely."

### 3. The Expansionist
Looks for upside everyone else is missing. What could be bigger? What adjacent opportunity is hiding? What's being undervalued? The Expansionist doesn't care about risk (that's the Contrarian's job). They care about what happens if this works even better than expected.

### 4. The Outsider
Has zero context about you, your field, or your history. Responds purely to what's in front of them. This is the most underrated advisor. Experts develop blind spots. The Outsider catches the curse of knowledge: things that are obvious to you but confusing to everyone else.

### 5. The Executor
Only cares about one thing: can this actually be done, and what's the fastest path to doing it? Ignores theory, strategy, and big-picture thinking. The Executor looks at every idea through the lens of "OK but what do you do Monday morning?" If an idea sounds brilliant but has no clear first step, the Executor will say so.

**Why these five:** They create three natural tensions. Contrarian vs Expansionist (downside vs upside). First Principles vs Executor (rethink everything vs just do it). The Outsider sits in the middle keeping everyone honest by seeing what fresh eyes see.

---

## how a council session works

### step 1: frame the question (with context enrichment)

When the user says "council this" (or any trigger phrase), do two things before framing:

**A. Scan the workspace for context.** The user's question is often just the tip of the iceberg. Their Claude setup likely contains files that would dramatically improve the council's output. Before framing, quickly scan for and read any relevant context files:

- `CLAUDE.md` or `claude.md` in the project root or workspace (business context, preferences, constraints)
- Any `memory/` folder (audience profiles, voice docs, business details, past decisions)
- Any files the user explicitly referenced or attached
- Recent council transcripts in this folder (to avoid re-counciling the same ground)
- Any other context files that seem relevant to the specific question (e.g., if they're asking about pricing, look for revenue data, past launch results, audience research)

Use `Glob` and quick `Read` calls to find these. Don't spend more than 30 seconds on this. You're looking for the 2-3 files that would give advisors the context they need to give specific, grounded advice instead of generic takes.

**B. Frame the question.** Take the user's raw question AND the enriched context and reframe it as a clear, neutral prompt that all five advisors will receive. The framed question should include:

1. The core decision or question
2. Key context from the user's message
3. Key context from workspace files (business stage, audience, constraints, past results, relevant numbers)
4. What's at stake (why this decision matters)

Don't add your own opinion. Don't steer it. But DO make sure each advisor has enough context to give a specific, grounded answer rather than generic advice.

If the question is too vague ("council this: my business"), ask one clarifying question. Just one. Then proceed.

Save the framed question for the transcript.

### step 2: convene the council (5 sub-agents in parallel)

Spawn all 5 advisors simultaneously as sub-agents. Each gets:

1. Their advisor identity and thinking style (from the descriptions above)
2. The framed question
3. A clear instruction: respond independently. Do not hedge. Do not try to be balanced. Lean fully into your assigned perspective. If you see a fatal flaw, say it. If you see massive upside, say it. Your job is to represent your angle as strongly as possible. The synthesis comes later.

Each advisor should produce a response of 150-300 words. Long enough to be substantive, short enough to be scannable.

**Sub-agent prompt template:**

```
You are [Advisor Name] on an LLM Council.

Your thinking style: [advisor description from above]

A user has brought this question to the council:

---
[framed question]
---

Respond from your perspective. Be direct and specific. Don't hedge or try to be balanced. Lean fully into your assigned angle. The other advisors will cover the angles you're not covering.

Keep your response between 150-300 words. No preamble. Go straight into your analysis.
```

### step 3: peer review (5 sub-agents in parallel)

This is the step that makes the council more than just "ask 5 times." It's the core of Karpathy's insight.

Collect all 5 advisor responses. Anonymize them as Response A through E (randomize which advisor maps to which letter so there's no positional bias).

Spawn 5 new sub-agents, one for each advisor. Each reviewer sees all 5 anonymized responses and answers three questions:

1. Which response is the strongest and why? (pick one)
2. Which response has the biggest blind spot and what is it?
3. What did ALL responses miss that the council should consider?

**Reviewer prompt template:**

```
You are reviewing the outputs of an LLM Council. Five advisors independently answered this question:

---
[framed question]
---

Here are their anonymized responses:

**Response A:**
[response]

**Response B:**
[response]

**Response C:**
[response]

**Response D:**
[response]

**Response E:**
[response]

Answer these three questions. Be specific. Reference responses by letter.

1. Which response is the strongest? Why?
2. Which response has the biggest blind spot? What is it missing?
3. What did ALL five responses miss that the council should consider?

Keep your review under 200 words. Be direct.
```

### step 4: chairman synthesis

This is the final step. One agent gets everything: the original question, all 5 advisor responses (now de-anonymized so you can see which advisor said what), and all 5 peer reviews.

The chairman's job is to produce the final council output. It follows this structure:

**COUNCIL VERDICT**

1. **Where the council agrees** — the points that multiple advisors converged on independently. These are high-confidence signals.

2. **Where the council clashes** — the genuine disagreements. Don't smooth these over. Present both sides and explain why reasonable advisors disagree.

3. **Blind spots the council caught** — things that only emerged through the peer review round. Things individual advisors missed that other advisors flagged.

4. **The recommendation** — a clear, actionable recommendation. Not "it depends." Not "consider both sides." A real answer. The chairman can disagree with the majority if the reasoning supports it.

5. **The one thing you should do first** — a single concrete next step. Not a list of 10 things. One thing.

**Chairman prompt template:**

```
You are the Chairman of an LLM Council. Your job is to synthesize the work of 5 advisors and their peer reviews into a final verdict.

The question brought to the council:
---
[framed question]
---

ADVISOR RESPONSES:

**The Contrarian:**
[response]

**The First Principles Thinker:**
[response]

**The Expansionist:**
[response]

**The Outsider:**
[response]

**The Executor:**
[response]

PEER REVIEWS:
[all 5 peer reviews]

Produce the council verdict using this exact structure:

## Where the Council Agrees
[Points multiple advisors converged on independently. These are high-confidence signals.]

## Where the Council Clashes
[Genuine disagreements. Present both sides. Explain why reasonable advisors disagree.]

## Blind Spots the Council Caught
[Things that only emerged through peer review. Things individual advisors missed that others flagged.]

## The Recommendation
[A clear, direct recommendation. Not "it depends." A real answer with reasoning.]

## The One Thing to Do First
[A single concrete next step. Not a list. One thing.]

Be direct. Don't hedge. The whole point of the council is to give the user clarity they couldn't get from a single perspective.
```

### step 5: generate the council report

After the chairman synthesis is complete, generate a visual HTML report and save it to the user's workspace.

**File:** `council-report-[timestamp].html`

The report should be a single self-contained HTML file with inline CSS. Clean design, easy to scan. It should contain:

1. **The question** at the top
2. **The chairman's verdict** prominently displayed (this is what most people will read)
3. **An agreement/disagreement visual** — a simple visual showing which advisors aligned and which diverged. This could be a grid, a spectrum, or a simple breakdown showing advisor positions. Keep it clean and scannable.
4. **Collapsible sections** for each advisor's full response (collapsed by default so the page isn't overwhelming, but available if the user wants to dig in)
5. **Collapsible section** for the peer review highlights
6. **A footer** showing the timestamp and what was counciled

Use clean styling: white background, subtle borders, readable sans-serif font (system font stack), soft accent colors to distinguish advisor sections. Nothing flashy. It should look like a professional briefing document.

Open the HTML file after generating it so the user can see it immediately.

### step 6: save the full transcript

Save the complete council transcript as `council-transcript-[timestamp].md` in the same location. This includes:
- The original question
- The framed question
- All 5 advisor responses
- All 5 peer reviews (with anonymization mapping revealed)
- The chairman's full synthesis

This transcript is the artifact. If the user wants to run the council again on the same question after making changes, having the previous transcript lets them (or a future agent) see how the thinking evolved.

---

## output format

Every council session produces two files:

```
council-report-[timestamp].html    # visual report for scanning
council-transcript-[timestamp].md  # full transcript for reference
```

The user sees the HTML report. The transcript is there if they want to dig deeper or reference specific advisor arguments later.

---

## example: counciling a product decision

**User:** "Council this: I'm thinking of building a $297 course on Claude Code for beginners. My audience is mostly non-technical solopreneurs. Is this the right move?"

**The Contrarian:** "The market is flooded with Claude courses right now. At $297, you're competing with free YouTube content. Your audience is non-technical, which means high support burden and refund risk. The people who would pay $297 are likely already past beginner level..."

**The First Principles Thinker:** "What are you actually trying to achieve? If it's revenue, a course is one of the slowest paths. If it's authority, a free resource might do more. If it's building a customer base for higher-ticket offers, the price point and audience might be mismatched..."

**The Expansionist:** "Beginner Claude for solopreneurs is a massive underserved market. Everyone's teaching advanced stuff. If you nail the beginner angle, you own the entry point to this entire space. The $297 might be low. What if this became a $997 program with community access..."

**The Outsider:** "I don't know what Claude Code is. If I saw '$297 course on Claude Code for beginners,' I wouldn't know if this is for me. The name means nothing to someone outside your world. Your landing page needs to sell the outcome, not the tool..."

**The Executor:** "A full course takes 4-8 weeks to produce properly. Before building anything, run a live workshop at $97 to 50 people. You validate demand, generate testimonials, and create the raw material for the course. If 50 people don't buy the workshop, 500 won't buy the course..."

**Chairman's Verdict:**

*Where the council agrees:* The beginner solopreneur angle has real demand, but the current framing (Claude Code course) is too tool-specific and won't resonate with non-technical buyers.

*Where the council clashes:* Price. The Contrarian says $297 is too high given competition. The Expansionist says it's too low for the value. The resolution likely depends on how much support and community access is bundled.

*Blind spots caught:* The Outsider's point that "Claude Code" means nothing to the target buyer is the single most important insight. Every advisor except the Outsider assumed the audience already knows what this is.

*Recommendation:* Don't build the course yet. Validate with a lower-commitment offer first. But reframe entirely: sell the outcome (automate your business, get 10 hours back per week), not the tool.

*One thing to do first:* Run a $97 live workshop called "How to automate your first business task with AI" to 50 people. Don't mention Claude Code in the title.

---

## important notes

- **Always spawn all 5 advisors in parallel.** Sequential spawning wastes time and lets earlier responses bleed into later ones.
- **Always anonymize for peer review.** If reviewers know which advisor said what, they'll defer to certain thinking styles instead of evaluating on merit.
- **The chairman can disagree with the majority.** If 4 out of 5 advisors say "do it" but the reasoning of the 1 dissenter is strongest, the chairman should side with the dissenter and explain why.
- **Don't council trivial questions.** If the user asks something with one right answer, just answer it. The council is for genuine uncertainty where multiple perspectives add value.
- **The visual report matters.** Most users will scan the report, not read the full transcript. Make the HTML output clean and scannable.

---

Methodology by [Andrej Karpathy](https://x.com/karpathy). Claude Code adaptation inspired by [@olelehmann](https://x.com/olelehmann). Published by [@tenfoldmarc](https://instagram.com/tenfoldmarc) — follow for daily AI automation builds.
"""
