# 🎬 YouTube Script Creator Agent

![Innovation Lab](https://img.shields.io/badge/innovationlab-3D8BD3) ![Hackathon](https://img.shields.io/badge/hackathon-5F43F1) ![Content Creation](https://img.shields.io/badge/domain-content--creation-4CAF50) ![Video AI](https://img.shields.io/badge/domain-video--ai-2196F3)

**An intelligent agent that transforms ideas into viral-ready YouTube Shorts scripts with advanced hook diversity, tone analysis, and style replication — discoverable on ASI:One via the Chat Protocol.**

---

## 🎯 What It Does

This agent helps content creators craft **high-retention YouTube Shorts and TikTok scripts** (30–90 seconds) that balance pacing, emotion, and visual storytelling. It combines multiple AI systems to deliver professional, trend-aware scripts with unique, non-repetitive hooks.

### **Three Core Capabilities:**

🔥 **Dynamic Script Generation** — Creates short-form scripts with timestamps, camera directions, and 50+ unique hook styles
🎯 **Tone & Voice Analysis** — Analyzes any transcript to identify tone, pacing, and delivery patterns
🎭 **Style Replication** — Generates new scripts that match your analyzed tone perfectly

---

## ✨ Key Features

### 🎪 **Advanced Hook System**

* **50+ hook archetypes** organized into 8 thematic buckets
* **Non-repetition engine** tracks last 3 bucket themes + last 5 exact styles
* **Auto-similarity check** regenerates if hook is too similar to recent ones
* **Dual hook variants** (A/B) for each script to enable quick testing

**Hook Categories:**

* 💥 **Debunk** — Myth-busting, unpopular opinions, reverse advice
* 📊 **Proof** — Shock stats, metric reveals, case studies
* 📖 **Story** — Anecdotes, before/after, micro-narratives
* 🎮 **Game** — Speedruns, challenges, live polls
* 🛠️ **Craft** — Frameworks, blueprints, cheat codes
* 🔀 **Pattern** — Meme subversion, interrupts, mystery boxes
* 💭 **Premise** — What-if scenarios, predictions, high-stakes questions
* 🎭 **Persona** — POV swaps, confessions, DM reveals

### 🧠 **Intelligent Context Layer**

* **MeTTa Knowledge Graph** enrichment for trend-aware facts
* Injects up to 3 topical insights into every script
* Keeps content grounded and culturally relevant

### ⚡ **Performance Optimized**

* **Smart caching** with 24-hour TTL for repeated analyses
* **Rate limiting** protects API quotas
* **Startup validation** catches configuration issues early
* **Usage metrics** for operational visibility

---

## 💬 How to Use

### **Generate a Script**

```
Create a YouTube short about why coffee makes you tired
```

### **Analyze Tone**

```
Analyze this transcript: [paste your video transcript]
```

### **Replicate Style**

```
Write a script about productivity in the same tone
```

---

## 🎬 Example Output

```
✅ YouTube Script Generated

(0–3s) You've been drinking coffee wrong your entire life.
[Close-up of empty coffee cup]

(3–8s) That afternoon crash? It's not caffeine wearing off...
[B-roll: tired person at desk]

(8–15s) It's adenosine buildup your brain was hiding.
[Animation: brain chemistry]

(15–22s) Here's the fix nobody tells you about.
[Cut to solution reveal]
```

**Visual Cues Included:**

* Timestamps for pacing `(0–3s)`
* Camera directions `[Close-up]`, `[B-roll]`, `[Cut]`
* Scene suggestions `[Animation]`, `[Zoom]`

---

## 🏗️ Architecture

| Component            | Technology                                                                       |
| -------------------- | -------------------------------------------------------------------------------- |
| **Framework**        | uAgents v0.22.9                                                                  |
| **Protocol**         | **ASI:One Chat Protocol** (sends `ChatAcknowledgement` on every inbound message) |
| **Primary LLM**      | ASI1 (script generation; fallback for tone analysis)                             |
| **Analysis LLM**     | Gemini 1.5 Flash (tone analysis with caching)                                    |
| **Knowledge Source** | MeTTa Knowledge Graph (nested + recursive queries)                               |
| **Hook Engine**      | 50+ archetypes, bucket-aware rotation                                            |
| **Storage**          | Context storage for tone memory & hook history                                   |
| **Manifest**         | Published on Agentverse with description; **Category = Innovation Lab**          |

---

## ⚙️ Configuration

### **Required Secrets** (Set in Agentverse)

```
ASI1_API_KEY = your_asi1_key
AGENT_SEED  = your_unique_seed_phrase
```

### **Optional but Recommended**

```
GEMINI_API_KEY = your_gemini_key
METTA_API_KEY  = your_metta_key
```

### **Optional Customization**

```
CACHE_TTL_HOURS = 24
AGENT_NAME = youtube_script_agent
AGENT_PORT = 8001
```

> **Deployment Notes (Agentverse UI):** Enable **Chat Protocol**, **Publish Manifest** (add a short description), and set **Category = Innovation Lab**. If faucet funding fails, fund the agent address manually.

---

## 🎓 Use Cases

### **Content Creators**

* Generate 5–10 script variations in minutes
* Test different hook styles before filming
* Maintain consistent brand voice across videos

### **Marketing Teams**

* Scale short-form content production
* A/B test hooks systematically
* Adapt tone for different platforms

### **Educators**

* Teach scriptwriting mechanics
* Demonstrate hook psychology
* Show AI-assisted creative workflows

---

## 🔥 What Makes This Special

### **1. Anti-Repetition Intelligence**

Most AI scriptwriters repeat themselves. This agent:

* Tracks your last 10 hooks
* Avoids your last 3 thematic buckets
* Checks token-level similarity
* Auto-regenerates if too similar

### **2. Professional Output Format**

Scripts come ready to use:

* Plain text (no JSON clutter)
* Precise timestamps for editing
* Camera/visual suggestions inline
* Two hook variants per script

### **3. Tone Persistence**

Analyze once, replicate forever:

* Stores tone analysis per user
* Applies same energy to new topics
* Maintains brand consistency
* Works across sessions

### **4. Knowledge-Enhanced**

Scripts aren't just creative—they're informed:

* Structured context from MeTTa
* Factual grounding for credibility
* Cultural relevance built-in

---

## 📊 Output Formats

### ✅ **Script Generation**

```
Plain text with timestamps + visual cues
• Hook variants A & B
• 30–90 second duration
• Camera directions included
• Pacing timestamps
```

### 🎯 **Tone Analysis**

```
• Primary tone (Active/Casual/Professional/etc.)
• Pacing + emotion level + formality
• Delivery style breakdown
• 3–5 actionable replication tips
```

### 🎭 **Style Replication**

```
New script matching analyzed tone
• Same energy and pacing
• Fresh hook style (non-repeating)
• Consistent voice maintained
```

---

## ⚡ Performance Features

✅ **Smart Caching** — 24-hour TTL reduces redundant API calls
✅ **Rate Limiting** — Protects quotas, prevents overuse
✅ **Startup Validation** — Catches missing API keys immediately
✅ **Usage Metrics** — Track scripts generated, cache hit rate, etc.
✅ **Graceful Fallbacks** — ASI1 backup if Gemini unavailable
✅ **Efficient Storage** — Deque-based history tracking

---

## 🚫 Limitations

**What It Does:**

* ✅ 30–90 second short-form scripts
* ✅ Tone analysis & replication
* ✅ Visual/camera suggestions
* ✅ Hook diversity & anti-repetition
* ✅ Knowledge graph context

**What It Doesn't Do:**

* ❌ Long-form video scripts (2+ minutes)
* ❌ Direct social media posting
* ❌ Video editing or thumbnail creation
* ❌ Real-time analytics scraping

---

## 🧩 Advanced Features

| Feature                 | Description                           |
| ----------------------- | ------------------------------------- |
| **Hook Memory**         | Remembers last 10 hooks per user      |
| **Bucket Rotation**     | Prevents thematic repetition          |
| **Similarity Check**    | Auto-detects near-duplicate openings  |
| **Multi-Provider**      | ASI1 + Gemini architecture            |
| **Knowledge Injection** | MeTTa graph context in prompts        |
| **Tone Persistence**    | Reuses analysis across sessions       |
| **Configurable Cache**  | Adjustable TTL for speed vs freshness |
| **Dual Hooks**          | A/B variants for every script         |

---

## 💡 Pro Tips

**For Best Results:**

1. Analyze 2–3 top-performing scripts from your channel
2. Use “replicate tone” to maintain brand consistency
3. Generate 5 scripts, pick the strongest hook
4. Test different buckets for different content types
5. Cache tone analysis for your signature style

**Hook Selection Strategy:**

* **Debunk** hooks → myth-busting, hot takes
* **Proof** hooks → data-driven, authority content
* **Story** hooks → emotional, narrative content
* **Game** hooks → interactive, challenge content
* **Craft** hooks → educational, how-to content

---

## 🎯 Success Metrics

After deploying, track:

* **Scripts generated** — Total output volume
* **Tone analyses** — Brand voice captures
* **Cache hit rate** — Efficiency metric
* **Hook diversity** — Repetition avoidance

Access via: “Show me usage metrics”

---

## 🔮 Roadmap

**Planned Enhancements:**

* 🎨 Title & thumbnail suggestion engine
* 📈 Hook performance tracking (which styles convert)
* 🌍 Multilingual script support
* 🎯 Platform-specific presets (YouTube vs TikTok vs Instagram)
* 🔗 Multi-agent workflows for end-to-end production
* 📊 SEO-optimized descriptions

---

## 🏷️ Tags

`youtube` `tiktok` `content-creation` `video-scripts` `ai-writing` `tone-analysis` `style-replication` `short-form-video` `hooks` `scriptwriting` `creative-ai` `metta` `asi1` `gemini` `uagents`

---

## 👤 Creator

**Ehonor Joshua**
Built for the **Innovation Lab Hackathon**
Created with ❤️ using **uAgents**, **ASI1**, **Gemini**, and **MeTTa Knowledge Graph**

---

## 🚀 Get Started

**Agent Address:**
`agent1qfyjjwkks2tywvdmdlt07fv3qml252z659fcazyc0zer9kje62huu3w0s0e`

**Try it now:**

1. Send: “Create a YouTube short about [your topic]”
2. Send: “Analyze this transcript: [paste text]”
3. Send: “Write about [new topic] in the same tone”

> **Demo Video (3–5 min):** *http://www.loom.com/share/a63d92c5756b492ab61b7c21c2e6e124*
> **Source Code (GitHub):** *http://github.com/Kanzendev/YouTube-Script-Creator/tree/main*

**Ready to create viral content? Start chatting! 🎬✨**

---

## 📄 License

MIT License — Free to use, modify, and distribute.

---

## 🔗 Resources

* **Agentverse:** [https://agentverse.ai](https://agentverse.ai)
* **uAgents Docs:** [https://docs.fetch.ai](https://docs.fetch.ai)
* **uAgents GitHub:** [https://github.com/fetchai/uAgents](https://github.com/fetchai/uAgents)
* **Fetch.ai:** [https://fetch.ai](https://fetch.ai)
* **MeTTa Quick Examples (in repo):** `agents/research_metta/kg.metta`, `agents/research_metta/queries.metta`
* **Deployment Tip:** On Agentverse, **Enable Chat Protocol → Publish Manifest → Set Category = Innovation Lab**.
