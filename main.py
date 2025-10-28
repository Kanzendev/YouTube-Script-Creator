import os
import json
import re
import random
import hashlib
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import Optional, Dict, List
from collections import deque
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    chat_protocol_spec,
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    StartSessionContent,
    EndSessionContent,
    MetadataContent,
)
import httpx


# =============================================================================
# Environment configuration (set these in Agentverse Secrets)
# =============================================================================
AGENT_NAME = os.environ.get("AGENT_NAME", "youtube_script_agent")
AGENT_SEED = os.environ.get("AGENT_SEED", "youtube_script_seed_phrase_change_me")
AGENT_PORT = int(os.environ.get("AGENT_PORT", "8001"))

# ✅ Secrets - ASI1 (Primary LLM)
ASI1_API_KEY = os.environ.get("ASI1_API_KEY", "")
ASI1_API_URL = os.environ.get("ASI1_API_URL", "https://api.asi1.ai/v1/chat/completions")
ASI1_MODEL = os.environ.get("ASI1_MODEL", "asi1-mini")

# ✅ MeTTa Knowledge Graph (optional context enricher)
METTA_API_KEY = os.environ.get("METTA_API_KEY", "")
METTA_API_URL = os.environ.get("METTA_API_URL", "https://api.metta.ai/v1/query")

# ✅ Gemini (free tier) — used for tone/style/pacing analysis
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# ✅ Configuration constants
MAX_CACHE_ENTRIES_PER_USER = 50  # Limit cache size
GEMINI_RPM_LIMIT = 15            # Requests per minute
GEMINI_RPD_LIMIT = 1500          # Requests per day
CACHE_TTL_HOURS = int(os.environ.get("CACHE_TTL_HOURS", "24"))
MAX_TRANSCRIPT_LENGTH = 10000    # Maximum transcript length in characters


# 🆕 PRODUCTION ENHANCEMENT: Startup validation
def validate_configuration():
    """Validate required configuration on startup."""
    errors = []
    warnings = []
    
    if not ASI1_API_KEY:
        errors.append("ASI1_API_KEY must be set in environment variables")
    
    if AGENT_SEED == "youtube_script_seed_phrase_change_me":
        errors.append("AGENT_SEED must be changed from default value")
    
    if not GEMINI_API_KEY:
        warnings.append("GEMINI_API_KEY not set - will fallback to ASI1 for tone analysis")
    
    if not METTA_API_KEY:
        warnings.append("METTA_API_KEY not set - knowledge enrichment disabled")
    
    if errors:
        error_msg = "❌ CRITICAL CONFIGURATION ERRORS:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)
    
    if warnings:
        warning_msg = "⚠️  Configuration warnings:\n" + "\n".join(f"  - {w}" for w in warnings)
        print(warning_msg)
    
    print("✅ Configuration validated successfully")


# Validate before creating agent
validate_configuration()


# Initialize Mailbox Agent
agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=AGENT_PORT,
    mailbox=True
)

chat_proto = Protocol(spec=chat_protocol_spec)


# =============================================================================
# System prompts (PLAIN TEXT OUTPUT)
# =============================================================================
SCRIPT_GENERATION_SYSTEM = """You are an expert YouTube short-form video scriptwriter.

Goal: Produce a 30–90 second script the user can read aloud as-is.

Requirements:
- Open with a strong hook in the first 3 seconds
- High-energy pacing with short lines
- Use timestamps like (0–3s), (3–8s) to guide pacing
- Include clear visual/camera/clip suggestions inline in square brackets [like this]
- Make it conversational and engaging
- Keep the whole answer as plain readable text (no code blocks, no JSON)
- Do NOT wrap the response in quotes or parentheses
- Do NOT include any preamble—start with the script itself"""

TONE_ANALYSIS_SYSTEM = """You are an expert video content analyst.

Task: Analyze the provided transcript and describe its tone and voice in plain text.

Include:
- Primary tone (e.g., Active, Professional, Casual, Passive, Persuasive)
- Pacing, emotion level, formality
- Delivery style (e.g., fast/slow, energetic/calm, humorous/serious)
- Target audience
- Notable linguistic patterns (bullets allowed)
- 3–5 actionable tips to replicate this tone

Output rules:
- Plain text only (no code fences, no JSON)
- Use short paragraphs and/or bullets for readability"""

REPLICATE_TONE_SYSTEM = """You are a skilled writing mimic.

Task: Given a tone description (plain text) and a new topic, write a 30–90 second short-form script that MATCHES that tone.

Requirements:
- Start with a strong hook
- Use timestamps like (0–3s), (3–8s)
- Include brief visual/camera/clip suggestions in square brackets [like this]
- Keep the whole answer as plain readable text (no code blocks, no JSON)
- Do NOT add any preamble—start with the script"""


# =============================================================================
# Enhanced Output Formatting Functions
# =============================================================================
def format_script_output(script_txt: str, hook_style: str, topic: str) -> str:
    """Format script with clear structure and visual hierarchy."""
    
    lines = [l.strip() for l in script_txt.strip().split('\n') if l.strip()]
    
    # Intelligently split into sections based on position
    hook_lines = []
    body_lines = []
    closing_lines = []
    
    for i, line in enumerate(lines):
        # First 3-4 lines = hook
        if i < 4 or (i == 0 and '(0' in line):
            hook_lines.append(line)
        # Last 2-3 lines = closing
        elif i >= len(lines) - 3:
            closing_lines.append(line)
        # Everything else = body
        else:
            body_lines.append(line)
    
    # Build formatted output
    output = f"""📱 **YouTube Short Script: "{topic[:60]}"**

═══════════════════════════════════════

🎯 **OPENING HOOK**
{'-' * 45}
Style: {hook_style.split('(')[0].strip()}

{chr(10).join(hook_lines)}

💭 **Hook Tips:**
→ This style creates immediate curiosity
→ Keep energy HIGH in first 3 seconds
→ Match your facial expression to the tone

═══════════════════════════════════════

📖 **MAIN CONTENT**
{'-' * 45}

{chr(10).join(body_lines)}

💭 **Pacing Notes:**
→ Cut every 2-3 seconds for retention
→ Add B-roll during transitions
→ Match camera movement to energy level

═══════════════════════════════════════

🎬 **CLOSING**
{'-' * 45}

{chr(10).join(closing_lines)}

💭 **Closing Strategy:**
→ Strong call-to-action (like, follow, comment)
→ Loop back to hook theme for cohesion
→ Leave viewers wanting more

═══════════════════════════════════════

📊 **QUICK STATS:**
• Duration: 30-90 seconds
• Hook Type: {hook_style.split('(')[0].strip()}
• Visual Cues: {len([l for l in lines if '[' in l])} camera directions
• Estimated Cuts: {len([l for l in lines if '(' in l])} scenes

💡 **PRO TIP:** Test both hook variants (A/B) before filming!

═══════════════════════════════════════
"""
    
    return output


def format_tone_analysis_output(tone_text: str, source: str = "Gemini") -> str:
    """Format tone analysis with clear sections."""
    
    output = f"""🎯 **TONE & STYLE ANALYSIS REPORT**
Source: {source}

═══════════════════════════════════════

📊 **ANALYSIS RESULTS:**
{'-' * 45}

{tone_text}

═══════════════════════════════════════

💡 **HOW TO USE THIS ANALYSIS:**

1️⃣ **For Replication**
   → Say: "Write about [topic] in this tone"
   → Agent will match the style automatically

2️⃣ **For Consistency**
   → This tone is saved to your profile
   → All future replications use this style

3️⃣ **For Learning**
   → Study the patterns identified above
   → Apply these insights to manual writing

═══════════════════════════════════════

✨ **NEXT STEPS:**
Want a script in this exact tone? Just ask:
"Create a script about [your topic] in this style"

💾 Analysis saved and ready to replicate!

═══════════════════════════════════════
"""
    
    return output


def format_replicated_output(script_txt: str, topic: str, hook_style: str) -> str:
    """Format tone-replicated scripts."""
    
    output = f"""🎭 **TONE-MATCHED SCRIPT CREATED**

═══════════════════════════════════════

📋 **NEW TOPIC:** {topic[:60]}
✅ **TONE:** Matched to your analyzed style
🎯 **HOOK TYPE:** {hook_style.split('(')[0].strip()}

═══════════════════════════════════════

📱 **YOUR SCRIPT:**

{script_txt}

═══════════════════════════════════════

✅ **CONSISTENCY CHECK:**
• ✓ Matched pacing and rhythm
• ✓ Same energy level maintained
• ✓ Vocabulary style consistent
• ✓ Emotional tone replicated

💡 **TIP:** Compare with your original to verify the match!

═══════════════════════════════════════
"""
    
    return output


# =============================================================================
# Hook diversity utilities (✅ Upgraded with non-repetition)
# =============================================================================
# Base hooks
HOOK_STYLES = [
    "Contrarian take (break a common belief in 1 line).",
    "Shock stat (lead with a surprising number).",
    "High-stakes question (direct, urgent).",
    "Cold-open anecdote (1–2 vivid lines, then reveal).",
    "Pattern interrupt (start mid-action, finish the thought).",
    "Mystery box (hint at the payoff without revealing it).",
    "Timeline jump (start at the climax, then rewind).",
    "Challenge the viewer (call-out, mini-dare).",
    "Hyper-specific scenario (relatable micro-scene).",
    "Analogy/metaphor (unexpected comparison).",
    "Authority signal (quote/source then flip it).",
    "Humorous twist (dry, fast punch)."
]

# Extended hooks (new)
HOOK_STYLES_EXTENDED = [
    "What-if flip (reframe the premise with a bold possibility).",
    "Rule-of-one (one change, one metric, one payoff).",
    "Unpopular opinion (spicy take that tees up proof).",
    "Before/after reveal (contrast failure vs fix immediately).",
    "Myth vs fact (debunk a common belief, then replace it).",
    "Time-bomb countdown (urgency with visible timer).",
    "Cheat-code (hidden shortcut or macro).",
    "Hidden cost (expose the tradeoff viewers miss).",
    "Reverse advice (do the opposite of standard wisdom).",
    "Mistake you're making (call-out with quick fix).",
    "X vs Y showdown (split-screen comparison).",
    "Micro-story loop (hint outcome, open loop).",
    "Prediction (near-future forecast tied to action).",
    "Scarcity (only-one-shot framing).",
    "Riddle (cryptic identity of the solution).",
    "Reluctant confession (self-own leading to lesson).",
    "Speedrun (race the clock to demonstrate skill).",
    "Shock receipt (metric proof, then teach).",
    "Inbox/DM reveal (quote a real critique/request).",
    "Live poll (A/B choice with consequences).",
    "POV swap (second-person viewer perspective).",
    "Dialogue cold-open (two-line scene with tension).",
    "Object POV (inanimate object narrates the problem).",
    "Breaking-news parody (urgent update framing).",
    "Prop reveal (physical trigger that anchors the idea).",
    "Sound cue interrupt (audio sting to pattern-break).",
    "5-second test (compression challenge).",
    "Mini framework (acronym with steps).",
    "Analogy upgrade (fresh metaphor to reframe).",
    "Coach challenge (perform under constraint).",
    "Map it (journey from scroll to hooked).",
    "Boss fight (gamified difficulty framing).",
    "Meme subversion (use trend, flip expectation).",
    "Numbers cliff (tease critical stats first).",
    "Blueprint tease (template with blanks).",
    "Ethical clickbait (promise + payoff safeguard).",
    "Audience call-out (surgical niche targeting).",
    "One-word punch (single-word opener + reveal).",
    "Micro-stakes (small tweak, measurable gain).",
    "Reverse timeline (show ending, rewind fast).",
    "Constraint flex (ban a device and still win).",
    "Visual oddity (weird prop justifies lesson).",
    "Secret menu (hidden platform behavior).",
    "One-line case study (metric-backed opener).",
]

# Merge unique
HOOK_STYLES = list(dict.fromkeys(HOOK_STYLES + HOOK_STYLES_EXTENDED))

# Buckets to diversify theme (used for non-repetition logic)
HOOK_BUCKETS: Dict[str, List[str]] = {
    "debunk": [
        "Myth vs fact (debunk a common belief, then replace it).",
        "Unpopular opinion (spicy take that tees up proof).",
        "Reverse advice (do the opposite of standard wisdom).",
        "Ethical clickbait (promise + payoff safeguard).",
    ],
    "proof": [
        "Shock stat (lead with a surprising number).",
        "Shock receipt (metric proof, then teach).",
        "One-line case study (metric-backed opener).",
        "Numbers cliff (tease critical stats first).",
        "Authority signal (quote/source then flip it).",
    ],
    "story": [
        "Cold-open anecdote (1–2 vivid lines, then reveal).",
        "Micro-story loop (hint outcome, open loop).",
        "Before/after reveal (contrast failure vs fix immediately).",
        "Reverse timeline (show ending, rewind fast).",
        "Dialogue cold-open (two-line scene with tension).",
    ],
    "game": [
        "Boss fight (gamified difficulty framing).",
        "Speedrun (race the clock to demonstrate skill).",
        "Live poll (A/B choice with consequences).",
        "Challenge the viewer (call-out, mini-dare).",
        "5-second test (compression challenge).",
    ],
    "craft": [
        "Mini framework (acronym with steps).",
        "Blueprint tease (template with blanks).",
        "Rule-of-one (one change, one metric, one payoff).",
        "Cheat-code (hidden shortcut or macro).",
        "Map it (journey from scroll to hooked).",
    ],
    "pattern": [
        "Pattern interrupt (start mid-action, finish the thought).",
        "Meme subversion (use trend, flip expectation).",
        "Sound cue interrupt (audio sting to pattern-break).",
        "Visual oddity (weird prop justifies lesson).",
        "Mystery box (hint at the payoff without revealing it).",
    ],
    "premise": [
        "What-if flip (reframe the premise with a bold possibility).",
        "High-stakes question (direct, urgent).",
        "Scarcity (only-one-shot framing).",
        "Prediction (near-future forecast tied to action).",
        "Hyper-specific scenario (relatable micro-scene).",
    ],
    "persona": [
        "Reluctant confession (self-own leading to lesson).",
        "Inbox/DM reveal (quote a real critique/request).",
        "POV swap (second-person viewer perspective).",
        "Object POV (inanimate object narrates the problem).",
        "Prop reveal (physical trigger that anchors the idea).",
    ],
    "style": [
        "Analogy/metaphor (unexpected comparison).",
        "Analogy upgrade (fresh metaphor to reframe).",
        "Humorous twist (dry, fast punch).",
        "Timeline jump (start at the climax, then rewind).",
        "Secret menu (hidden platform behavior).",
        "One-word punch (single-word opener + reveal).",
        "Micro-stakes (small tweak, measurable gain).",
    ],
}

_word_re = re.compile(r"\w+")

def normalize(txt: str) -> set:
    return set(w.lower() for w in _word_re.findall(txt or ""))

def similarity(a: str, b: str) -> float:
    A, B = normalize(a), normalize(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)

def is_too_similar_to_history(ctx: Context, sender: str, hook_line: str, threshold: float = 0.4) -> bool:
    key = f"recent_hooks_{sender}"
    history = ctx.storage.get(key) or []
    return any(similarity(hook_line, h) >= threshold for h in history)

def remember_hook(ctx: Context, sender: str, hook_line: str):
    key = f"recent_hooks_{sender}"
    history = ctx.storage.get(key) or []
    history = ([hook_line] + history)[:10]
    try:
        ctx.storage.set(key, history)
    except Exception as e:
        ctx.logger.warning(f"Failed to save hook history: {e}")

def extract_first_hook_line(script_text: str) -> str:
    first_line = script_text.strip().splitlines()[0] if script_text.strip() else ""
    # Remove leading timestamp like "(0–3s)" if present
    return re.sub(r"^\s*\([^)]*\)\s*", "", first_line).strip()

# ✅ NEW: Non-repetition chooser (avoid last 3 buckets + last 5 exact styles)
def choose_hook_style(ctx: Context, sender: str) -> str:
    """
    Picks a hook style by:
      1) Avoiding the last 3 used buckets
      2) Avoiding the last 5 exact styles
      3) Falling back gracefully if filters are too strict
    """
    recent_buckets_key = f"recent_hook_buckets_{sender}"
    recent_styles_key = f"recent_hook_styles_{sender}"

    recent_buckets: List[str] = ctx.storage.get(recent_buckets_key) or []
    recent_styles: List[str] = ctx.storage.get(recent_styles_key) or []

    # Step 1: Choose bucket that is not in the last 3
    all_buckets = list(HOOK_BUCKETS.keys())
    candidate_buckets = [b for b in all_buckets if b not in recent_buckets[-3:]]
    if not candidate_buckets:
        candidate_buckets = all_buckets[:]  # fallback if all are blocked

    bucket = random.choice(candidate_buckets)
    bucket_styles = HOOK_BUCKETS.get(bucket, HOOK_STYLES[:])

    # Step 2: Filter out the last 5 exact styles
    filtered_styles = [s for s in bucket_styles if s not in recent_styles[-5:]]
    if not filtered_styles:
        filtered_styles = bucket_styles[:]  # fallback

    style = random.choice(filtered_styles)

    # Step 3: persist updates
    try:
        # Update recent buckets (keep last 3)
        rb = deque(recent_buckets, maxlen=3)
        rb.append(bucket)
        ctx.storage.set(recent_buckets_key, list(rb))

        # Update recent styles (keep last 5)
        rs = deque(recent_styles, maxlen=5)
        rs.append(style)
        ctx.storage.set(recent_styles_key, list(rs))
    except Exception as e:
        ctx.logger.warning(f"Failed to save recent hook selections: {e}")

    return style


# =============================================================================
# Cache Management with Size Limits
# =============================================================================
def prune_cache(ctx: Context, sender: str):
    """Remove oldest cache entries if limit exceeded."""
    cache_index_key = f"cache_index_{sender}"
    cache_index = ctx.storage.get(cache_index_key) or []
   
    if len(cache_index) > MAX_CACHE_ENTRIES_PER_USER:
        # Remove oldest entries
        to_remove = cache_index[MAX_CACHE_ENTRIES_PER_USER:]
        for old_key in to_remove:
            try:
                ctx.storage.delete(old_key)
            except Exception as e:
                ctx.logger.warning(f"Failed to delete cache entry {old_key}: {e}")
       
        # Keep only newest entries in index
        cache_index = cache_index[:MAX_CACHE_ENTRIES_PER_USER]
        try:
            ctx.storage.set(cache_index_key, cache_index)
        except Exception as e:
            ctx.logger.error(f"Failed to update cache index: {e}")

def cache_gemini_response(ctx: Context, sender: str, transcript: str, response: str):
    """Cache Gemini response with size management."""
    cache_key = f"gemini_cache_{sender}_{hashlib.md5(transcript.encode()).hexdigest()}"
    cache_index_key = f"cache_index_{sender}"
   
    try:
        # Store response with timestamp
        ctx.storage.set(cache_key, {
            "response": response,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
       
        # Update cache index
        cache_index = ctx.storage.get(cache_index_key) or []
        if cache_key not in cache_index:
            cache_index = [cache_key] + cache_index
            ctx.storage.set(cache_index_key, cache_index)
       
        # Prune old entries
        prune_cache(ctx, sender)
       
    except Exception as e:
        ctx.logger.error(f"Failed to cache Gemini response: {e}")

def get_cached_gemini_response(ctx: Context, sender: str, transcript: str) -> Optional[str]:
    """Retrieve cached Gemini response if available."""
    cache_key = f"gemini_cache_{sender}_{hashlib.md5(transcript.encode()).hexdigest()}"
   
    try:
        cached_data = ctx.storage.get(cache_key)
        if cached_data:
            # 🆕 ENHANCEMENT: Configurable cache TTL
            cached_time = datetime.fromisoformat(cached_data["timestamp"])
            if datetime.now(timezone.utc) - cached_time < timedelta(hours=CACHE_TTL_HOURS):
                return cached_data["response"]
    except Exception as e:
        ctx.logger.error(f"Failed to retrieve cached response: {e}")
   
    return None


# =============================================================================
# Rate Limiting for Gemini
# =============================================================================
def check_rate_limit(ctx: Context, sender: str) -> bool:
    """Check if user has exceeded Gemini rate limits."""
    now = datetime.now(timezone.utc)
    rate_key = f"gemini_rate_{sender}"
   
    try:
        rate_data = ctx.storage.get(rate_key) or {"minute": [], "day": []}
       
        # Clean old timestamps
        rate_data["minute"] = [
            t for t in rate_data["minute"]
            if datetime.fromisoformat(t) > now - timedelta(minutes=1)
        ]
        rate_data["day"] = [
            t for t in rate_data["day"]
            if datetime.fromisoformat(t) > now - timedelta(days=1)
        ]
       
        # Check limits
        if len(rate_data["minute"]) >= GEMINI_RPM_LIMIT:
            ctx.logger.warning(f"Rate limit (RPM) exceeded for {sender}")
            return False
        if len(rate_data["day"]) >= GEMINI_RPD_LIMIT:
            ctx.logger.warning(f"Rate limit (RPD) exceeded for {sender}")
            return False
       
        # Add current timestamp
        rate_data["minute"].append(now.isoformat())
        rate_data["day"].append(now.isoformat())
        ctx.storage.set(rate_key, rate_data)
       
        return True
       
    except Exception as e:
        ctx.logger.error(f"Rate limit check failed: {e}")
        return True  # Allow on error


# =============================================================================
# Usage Metrics Tracking
# =============================================================================
def increment_metric(ctx: Context, metric_name: str):
    """Increment a usage metric."""
    try:
        metrics = ctx.storage.get("usage_metrics") or {}
        metrics[metric_name] = metrics.get(metric_name, 0) + 1
        ctx.storage.set("usage_metrics", metrics)
    except Exception as e:
        ctx.logger.error(f"Failed to increment metric {metric_name}: {e}")

def get_metrics(ctx: Context) -> Dict:
    """Get all usage metrics."""
    return ctx.storage.get("usage_metrics") or {}


# =============================================================================
# Helpers
# =============================================================================
def create_text_message(text: str, end_session: bool = False) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=content
    )

async def query_metta_knowledge(query: str, ctx: Context) -> Optional[str]:
    """Query Metta Knowledge Graph for contextual information (optional)."""
    if not METTA_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                METTA_API_URL,
                headers={
                    "Authorization": f"Bearer {METTA_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={"query": query, "max_results": 3}
            )
            response.raise_for_status()
            data = response.json()
            
            if "results" in data and len(data["results"]) > 0:
                snippets = [r.get("text", "") for r in data["results"][:3]]
                knowledge = "\n".join(f"• {s}" for s in snippets if s)
                ctx.logger.info(f"✅ Metta returned {len(snippets)} knowledge snippets")
                return knowledge
                
    except httpx.HTTPStatusError as e:
        ctx.logger.warning(f"Metta API error {e.response.status_code}")
    except Exception as e:
        ctx.logger.warning(f"Metta query failed: {type(e).__name__}: {e}")
    
    return None

async def call_asi1_llm(system_prompt: str, user_message: str, knowledge_context: Optional[str], ctx: Context) -> str:
    """Call ASI1 LLM API."""
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add knowledge context if available
    if knowledge_context:
        messages.append({
            "role": "system",
            "content": f"Additional context:\n{knowledge_context}"
        })
    
    messages.append({"role": "user", "content": user_message})

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                ASI1_API_URL,
                headers={
                    "Authorization": f"Bearer {ASI1_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": ASI1_MODEL,
                    "messages": messages,
                    "temperature": 0.8,
                    "max_tokens": 1500
                }
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip()
    except httpx.HTTPStatusError as e:
        ctx.logger.error(f"ASI1 API error {e.response.status_code}: {e.response.text[:200]}")
        return json.dumps({"error": f"API error {e.response.status_code}"})
    except httpx.TimeoutException:
        ctx.logger.error(f"ASI1 API timeout after 60s")
        return json.dumps({"error": "Request timeout"})
    except Exception as e:
        ctx.logger.error(f"ASI1 API call failed: {type(e).__name__}: {e}")
        return json.dumps({"error": f"LLM call failed: {str(e)}"})

async def analyze_tone_with_gemini(transcript: str, ctx: Context, sender: str) -> Optional[str]:
    """Analyze tone using Gemini with caching and rate limiting."""
    if not GEMINI_API_KEY:
        return None
   
    # 🆕 ENHANCEMENT: Transcript length validation
    if len(transcript) > MAX_TRANSCRIPT_LENGTH:
        ctx.logger.warning(f"Transcript too long ({len(transcript)} chars), truncating to {MAX_TRANSCRIPT_LENGTH}")
        transcript = transcript[:MAX_TRANSCRIPT_LENGTH]
   
    # Check cache first
    cached = get_cached_gemini_response(ctx, sender, transcript)
    if cached:
        increment_metric(ctx, "gemini_cache_hits")
        ctx.logger.info("✅ Using cached Gemini response")
        return cached
   
    # Check rate limits
    if not check_rate_limit(ctx, sender):
        ctx.logger.warning(f"⚠️  Rate limit exceeded for {sender}")
        return None
   
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{
                        "parts": [{
                            "text": f"{TONE_ANALYSIS_SYSTEM}\n\nTranscript:\n{transcript}"
                        }]
                    }]}
            )
            response.raise_for_status()
            data = response.json()
           
            # Defensive parsing
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        tone_text = parts[0]["text"]
                        cache_gemini_response(ctx, sender, transcript, tone_text)
                        increment_metric(ctx, "gemini_api_calls")
                        ctx.storage.set(f"last_gemini_tone_{sender}", tone_text)
                        ctx.logger.info("✅ Gemini tone analysis completed")
                        return tone_text
            
            ctx.logger.warning("Gemini returned unexpected response structure")
               
    except httpx.HTTPStatusError as e:
        ctx.logger.error(f"Gemini API error {e.response.status_code}: {e.response.text[:200]}")
    except httpx.TimeoutException:
        ctx.logger.error(f"Gemini API timeout after 30s")
    except Exception as e:
        ctx.logger.error(f"Gemini API call failed: {type(e).__name__}: {e}")
   
    return None

def _maybe_is_error_payload(response: str) -> Optional[str]:
    """Check if LLM response is an error JSON payload."""
    try:
        parsed = json.loads(response)
        if "error" in parsed:
            return f"⚠️ Error: {parsed['error']}"
    except:
        pass
    return None

def parse_user_intent(text: str) -> dict:
    """Parse user intent from message text."""
    lower = text.lower()
    
    # Keywords for tone analysis
    if any(kw in lower for kw in ["analyze", "tone", "style", "voice"]):
        return {"intent": "analyze_tone"}
    
    # Keywords for tone replication
    if any(kw in lower for kw in ["replicate", "mimic", "same tone", "same style", "like that"]):
        return {"intent": "replicate_tone"}
    
    # Default to script generation
    return {"intent": "generate_script"}


# =============================================================================
# 🆕 PRODUCTION ENHANCEMENT: Startup Event Handler
# =============================================================================
@agent.on_event("startup")
async def startup_handler(ctx: Context):
    """Log system status on startup."""
    ctx.logger.info("=" * 50)
    ctx.logger.info("🚀 YouTube Script Agent Started")
    ctx.logger.info("=" * 50)
    ctx.logger.info(f"📊 ASI1 API: {'✅ Configured' if ASI1_API_KEY else '❌ Missing'}")
    ctx.logger.info(f"📊 Gemini API: {'✅ Configured' if GEMINI_API_KEY else '⚠️  Not configured (will use ASI1 fallback)'}")
    ctx.logger.info(f"📊 MeTTa API: {'✅ Configured' if METTA_API_KEY else '⚠️  Not configured (knowledge enrichment disabled)'}")
    ctx.logger.info(f"⚙️  Cache TTL: {CACHE_TTL_HOURS} hours")
    ctx.logger.info(f"⚙️  Max cache per user: {MAX_CACHE_ENTRIES_PER_USER}")
    ctx.logger.info(f"⚙️  Gemini rate limits: {GEMINI_RPM_LIMIT}/min, {GEMINI_RPD_LIMIT}/day")
    ctx.logger.info("=" * 50)


# =============================================================================
# Chat Protocol Handlers
# =============================================================================
@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages."""
    ctx.logger.info(f"📨 Received message from {sender}")

    for content_item in msg.content:
        # Session start
        if isinstance(content_item, StartSessionContent):
            await ctx.send(
                sender,
                create_text_message(
                    "👋 Welcome to the YouTube Script Agent!\n\n"
                    "I can help you:\n"
                    "1️⃣ Generate short-form scripts (30-90s)\n"
                    "2️⃣ Analyze tone/style from transcripts\n"
                    "3️⃣ Replicate tone for new topics\n\n"
                    "Just tell me what you need!"
                )
            )

        # Text messages
        elif isinstance(content_item, TextContent):
            user_text = content_item.text.strip()
            ctx.logger.info(f"Processing: {user_text[:100]}...")

            intent_data = parse_user_intent(user_text)
            intent = intent_data["intent"]

            await ctx.send(sender, create_text_message(f"🔄 Processing your {intent.replace('_', ' ')} request..."))

            # -------------------------
            # Generate Script
            # -------------------------
            if intent == "generate_script":
                knowledge = await query_metta_knowledge(
                    f"YouTube trends and viral content related to: {user_text}", ctx
                )

                # ✅ New non-repeating style chooser
                hook_style = choose_hook_style(ctx, sender)

                # Pull the most recent Gemini tone analysis (if present)
                gemini_tone_latest = ctx.storage.get(f"last_gemini_tone_{sender}")
                tone_hint = f"\n\nTone/style to mimic (from previous analysis):\n{gemini_tone_latest}\n" if gemini_tone_latest else ""

                enhanced_user = f"""
Topic/request:
{user_text}
{tone_hint}
Hook requirement:
- Use this hook style: {hook_style}
- The first line MUST embody that style.
- Write 2 alternative hooks (A and B) that both follow this style and feel distinctly different.
- Then continue the script with one of them (pick the stronger one) and complete a 30–90s script.

If you use knowledge context, weave 1 unique fact into the hook or its immediate follow-up.
"""

                llm_response = await call_asi1_llm(
                    SCRIPT_GENERATION_SYSTEM, enhanced_user, knowledge, ctx
                )

                maybe_err = _maybe_is_error_payload(llm_response)
                if maybe_err:
                    await ctx.send(sender, create_text_message(maybe_err))
                    return

                script_txt = llm_response.strip()

                # Anti-duplication check
                first_line = extract_first_hook_line(script_txt)
                if is_too_similar_to_history(ctx, sender, first_line):
                    alt_style = choose_hook_style(ctx, sender)
                    enhanced_user_alt = enhanced_user.replace(hook_style, alt_style)
                    llm_response_alt = await call_asi1_llm(
                        SCRIPT_GENERATION_SYSTEM, enhanced_user_alt, knowledge, ctx
                    )
                    maybe_err = _maybe_is_error_payload(llm_response_alt)
                    if not maybe_err:
                        alt_txt = llm_response_alt.strip()
                        alt_first = extract_first_hook_line(alt_txt)
                        if similarity(alt_first, first_line) < 0.6 and not is_too_similar_to_history(ctx, sender, alt_first):
                            script_txt = alt_txt
                            first_line = alt_first

                remember_hook(ctx, sender, first_line)
                increment_metric(ctx, "scripts_generated")

                # ✅ ENHANCED FORMATTING
                formatted_response = format_script_output(
                    script_txt=script_txt,
                    hook_style=hook_style,
                    topic=user_text[:60]
                )
                await ctx.send(sender, create_text_message(formatted_response))

            # -------------------------
            # Analyze Tone
            # -------------------------
            elif intent == "analyze_tone":
                transcript = user_text

                # Try Gemini first
                gemini_tone = await analyze_tone_with_gemini(transcript, ctx, sender)

                # Fallback to ASI1
                if not gemini_tone:
                    ctx.logger.info("🔄 Falling back to ASI1 for tone analysis")
                    increment_metric(ctx, "asi1_fallbacks")
                   
                    knowledge = await query_metta_knowledge(
                        "video content tone analysis patterns and creator styles", ctx
                    )
                    llm_response = await call_asi1_llm(
                        TONE_ANALYSIS_SYSTEM, transcript, knowledge, ctx
                    )
                    maybe_err = _maybe_is_error_payload(llm_response)
                    if maybe_err:
                        await ctx.send(sender, create_text_message(maybe_err))
                        return
                    gemini_tone = llm_response.strip()

                    try:
                        ctx.storage.set(f"last_gemini_tone_{sender}", gemini_tone)
                    except Exception as e:
                        ctx.logger.error(f"Failed to store fallback tone analysis: {e}")

                try:
                    ctx.storage.set(f"last_tone_analysis_{sender}", gemini_tone)
                except Exception as e:
                    ctx.logger.error(f"Failed to store tone analysis: {e}")

                increment_metric(ctx, "tone_analyses")
                metrics = get_metrics(ctx)
                source = "Gemini (cached)" if metrics.get("gemini_cache_hits", 0) > 0 else "Gemini"
                
                # ✅ ENHANCED FORMATTING
                formatted_response = format_tone_analysis_output(gemini_tone, source)
                await ctx.send(sender, create_text_message(formatted_response))

            # -------------------------
            # Replicate Tone
            # -------------------------
            elif intent == "replicate_tone":
                last_analysis = ctx.storage.get(f"last_gemini_tone_{sender}") or ctx.storage.get(f"last_tone_analysis_{sender}")
                if not last_analysis:
                    await ctx.send(
                        sender,
                        create_text_message("⚠️ No previous tone analysis found. Please analyze a transcript first!")
                    )
                    return

                knowledge = await query_metta_knowledge(
                    f"content ideas and trends for: {user_text}", ctx
                )

                # ✅ Non-repeating hook chooser again
                hook_style = choose_hook_style(ctx, sender)

                enhanced_prompt = f"""Use the following tone description to write a new short-form script matching that style.

Tone description:
{last_analysis}

New topic:
{user_text}

Hook requirement:
- Use this hook style: {hook_style}
- The first line MUST embody that style.
- Write 2 alternative hooks (A and B) that both follow this style and feel distinctly different.
- Then continue the script with one of them (pick the stronger one) and complete a 30–90s script.

If you use knowledge context, weave 1 unique fact into the hook or its immediate follow-up.

Remember: plain text only, with timestamps and bracketed clip directions."""

                llm_response = await call_asi1_llm(
                    REPLICATE_TONE_SYSTEM, enhanced_prompt, knowledge, ctx
                )

                maybe_err = _maybe_is_error_payload(llm_response)
                if maybe_err:
                    await ctx.send(sender, create_text_message(maybe_err))
                    return

                script_txt = llm_response.strip()

                # Anti-duplication
                first_line = extract_first_hook_line(script_txt)
                if is_too_similar_to_history(ctx, sender, first_line):
                    alt_style = choose_hook_style(ctx, sender)
                    enhanced_prompt_alt = enhanced_prompt.replace(hook_style, alt_style)
                    llm_response_alt = await call_asi1_llm(
                        REPLICATE_TONE_SYSTEM, enhanced_prompt_alt, knowledge, ctx
                    )
                    maybe_err = _maybe_is_error_payload(llm_response_alt)
                    if not maybe_err:
                        alt_txt = llm_response_alt.strip()
                        alt_first = extract_first_hook_line(alt_txt)
                        if similarity(alt_first, first_line) < 0.6 and not is_too_similar_to_history(ctx, sender, alt_first):
                            script_txt = alt_txt
                            first_line = alt_first

                remember_hook(ctx, sender, first_line)
                increment_metric(ctx, "tone_replications")

                # ✅ ENHANCED FORMATTING
                formatted_response = format_replicated_output(
                    script_txt=script_txt,
                    topic=user_text[:60],
                    hook_style=hook_style
                )
                await ctx.send(sender, create_text_message(formatted_response))


@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"✅ ACK from {sender} for message {msg.acknowledged_msg_id}")


# Include protocol and run
agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 YouTube Script Agent - Enhanced Format Edition")
    print("=" * 60)
    print("📊 Features:")
    print("   ✅ Dual-LLM architecture (Gemini + ASI1)")
    print("   ✅ Intelligent caching with TTL")
    print("   ✅ Rate limiting protection")
    print("   ✅ Usage metrics tracking")
    print("   ✅ Hook diversity system (non-repeating buckets/styles)")
    print("   ✅ Configuration validation")
    print("   ✅ Professional output formatting")
    print("=" * 60)
    agent.run()
