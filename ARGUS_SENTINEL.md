# Argus Sentinel
### AI-Powered Cybersecurity Reasoning Engine

**Version:** 1.0 — Vision Lock  
**Status:** Planning Complete · Architecture Defined · Development Phase Beginning  
**Repository:** https://github.com/Ayaan1911/Argus-Sentinel

---

## The One Question

> **"What should I care about, why does it matter, and what should I do next?"**

Every feature, every decision, every line of code in Argus Sentinel exists to answer this question.

Most cybersecurity tools are excellent at finding things. They are terrible at explaining them. A user can run Nmap, Nuclei, Subfinder, and Httpx and receive thousands of results — ports, subdomains, vulnerabilities, technologies — and still have no idea what any of it means or where to begin.

The problem is not collection. The problem is understanding.

Argus Sentinel solves this.

---

## What Argus Is

Argus Sentinel is an **AI-powered Cybersecurity Copilot and Reasoning Engine**.

It discovers security findings, reasons about their significance, explains them in plain language, and guides users toward the most important actions to take next.

**The scanners are inputs. The intelligence layer is the product.**

This distinction matters. Any developer can wrap Nmap in a web UI. What Argus builds — the knowledge base, the reasoning engine, the correlation logic, the audience-aware guidance — is what makes it genuinely different and genuinely harder to replace.

---

## The Problem Statement

Modern security tools generate enormous amounts of raw data:

- Open ports and running services
- Discovered subdomains and live hosts
- Technologies and frameworks
- Vulnerabilities and misconfigurations
- SSL issues and exposed panels

The data is not the problem. The challenge is answering:

- What does this finding actually mean?
- Is this normal or dangerous?
- How serious is it relative to everything else?
- What should I look at first?
- How do I fix it?
- What should I learn next?

Existing tools rarely answer these questions. They produce data and leave the user alone with it. Argus does not.

---

## Core Philosophy

Most tools answer: **"What did you find?"**

Argus answers: **"What does it mean?"**

And eventually: **"What should you do next?"**

Those are fundamentally harder questions. And they are the questions that actually matter to every person who runs a security scan — whether they are a student, a bug bounty hunter, a developer, or a professional.

---

## Who Argus Helps

Argus is built for four personas. Version 1 serves all four simultaneously through audience-aware guidance.

### Cybersecurity Students
**Problem:** Found something. Don't understand it. Don't know where to start or what to learn.  
**Argus provides:** Plain-language explanations, concept breakdowns, learning resources, beginner-friendly guidance.

### Bug Bounty Hunters
**Problem:** Recon generates too much data. Hard to know what's worth investigating.  
**Argus provides:** Prioritized findings, interesting target identification, attack surface insights, areas most likely to yield results.

### Developers
**Problem:** Security scan returned findings. Don't know if they're serious or what to do about them.  
**Argus provides:** Risk explanations in non-technical language, business impact context, specific remediation steps relevant to their stack.

### Security Professionals
**Problem:** Noise, repetition, information overload, too much time spent on basic analysis.  
**Argus provides:** Fast context, correlation across findings, prioritized recommendations, reduced time-to-decision.

---

## Core Architecture — The Five Layers

Argus processes every finding through five sequential layers. Each layer adds value that the previous one cannot provide.

```
Discovery → Intelligence → Reasoning → Guidance → Learning
```

### Layer 1: Discovery
**Purpose:** Collect raw information.

Argus uses existing best-in-class tools as inputs:
- **Subfinder** — subdomain enumeration
- **Httpx** — live host detection
- **Nmap** — port scanning and service detection
- **Nuclei** — vulnerability scanning

Output: raw facts. Ports, services, technologies, vulnerabilities, assets.

This layer is deliberately not the product. It is infrastructure.

---

### Layer 2: Intelligence
**Purpose:** Transform raw findings into structured knowledge.

Raw output:
```
Port 22 Open
OpenSSH 8.4
```

After Intelligence Layer:
```
Service: SSH
Purpose: Remote Administration
Exposure: Internet Facing
Context: Known attack surface for brute force and credential attacks
```

The **Argus Intelligence Library** powers this layer. It is the brain of the system — a structured, versioned, human-authored knowledge base covering services, technologies, and vulnerability classes.

---

### Layer 3: Reasoning
**Purpose:** Determine significance through deterministic logic — not AI guessing.

Example reasoning chain:
```
SSH Detected
↓ Internet Facing (+2)
↓ Password Authentication Enabled (+3)
↓ Outdated Version Detected (+2)
↓ No IP Restrictions (+1)
= Risk Score: 8/10 → HIGH
```

This layer converts facts into conclusions. Every conclusion is explainable. No black boxes. No LLM-generated risk scores that change between runs.

---

### Layer 4: Guidance
**Purpose:** Always answer "What should I do next?"

Every finding produces a prioritized action list. Not generic advice — specific, ordered, actionable steps based on what was actually found.

Example for SSH:
1. Disable password authentication — use key-based login only
2. Set `PermitRootLogin no` in sshd_config
3. Restrict port 22 access by IP via firewall
4. Verify OpenSSH version against current CVEs
5. Enable fail2ban or equivalent brute-force protection

---

### Layer 5: Learning
**Purpose:** Teach users while they work.

The same finding is explained differently depending on the selected audience:

| Audience | SSH Explanation |
|---|---|
| Student | "SSH is like a secure tunnel into a computer. If open to the internet with weak settings, attackers can try thousands of passwords per second." |
| Developer | "Set PasswordAuthentication no in /etc/ssh/sshd_config. Use SSH keys. Restrict port 22 to your IP in your security group." |
| Bug Bounty Hunter | "Check OpenSSH version against recent CVEs. Note if password auth is enabled. Look for username enumeration on older versions." |
| Security Professional | "Enforce key-based auth via config management. Monitor auth.log for repeated failures. Alert on logins from unexpected IPs." |

One finding. Four perspectives. Same underlying knowledge.

---

## The Argus Intelligence Library

The Intelligence Library is the core intellectual asset of Argus Sentinel. It is not code. It is **knowledge** — structured, versioned, human-authored, and continuously maintained.

Unlike LLM outputs that vary between runs, the Intelligence Library is consistent, auditable, and ownable. It is what separates Argus from a scanner with a UI.

### Version 1 Scope

**Services**
- SSH (port 22)
- HTTP (port 80)
- HTTPS (port 443)
- MySQL (port 3306)
- Redis (port 6379)

**Technologies**
- Apache
- Nginx
- Tomcat
- WordPress

**Vulnerability Classes**
- SQL Injection
- Cross-Site Scripting (XSS)
- Server-Side Request Forgery (SSRF)
- Insecure Direct Object Reference (IDOR)
- Remote Code Execution (RCE)

### Intelligence Entry Structure

Every entry in the library follows this schema:

```json
{
  "service": "",
  "port": 0,
  "protocol": "",
  "purpose": "",
  "risk_level": "",
  "description": "",
  "common_risks": [],
  "misconfigurations": [],
  "attack_patterns": [],
  "real_world_incidents": [],
  "recommended_actions": [],
  "audience_guidance": {
    "student": "",
    "developer": "",
    "bug_bounty_hunter": "",
    "pentester": "",
    "security_team": ""
  },
  "correlation_rules": {
    "amplifies": [],
    "requires": [],
    "mitigates": []
  },
  "learning_resources": [],
  "related_findings": [],
  "mitre_attack": [],
  "risk_weight": 0,
  "version": "1.0",
  "last_updated": "",
  "reviewed_by": "argus-team"
}
```

**Note on versioning:** The Intelligence Library is living knowledge. Security changes — CVEs are discovered, best practices evolve, attack patterns shift. Every entry carries version metadata so staleness is visible and reviewable.

---

## Universal Finding Schema

Every finding Argus produces — regardless of source — follows the same structure. This schema is the foundation that makes every other feature possible.

```json
{
  "id": "",
  "type": "",
  "title": "",
  "raw_data": {},
  "severity": "",
  "confidence": "",
  "technical_impact": "",
  "business_impact": "",
  "attack_patterns": [],
  "recommended_actions": [],
  "learning_resources": [],
  "related_findings": [],
  "audience_guidance": {},
  "reasoning_breakdown": [],
  "version": "1.0"
}
```

This schema powers: UI cards, reports, AI explanations, filtering, prioritization, exports, and every future feature.

If a feature cannot be built on top of this schema, it probably should not be built.

---

## The Engines

### Confidence Engine

Confidence measures **certainty that a finding exists** — not how dangerous it is.

| Example | Confidence |
|---|---|
| Port 22 open (directly observed by Nmap) | 95% |
| Possible admin panel (heuristic detection) | 70% |
| Potential IDOR endpoint (pattern match) | 40% |

Confidence formula:
```
Scanner Reliability + Evidence Count + Knowledge Base Match = Confidence Score
```

Confidence and severity are completely separate concepts. A finding can be high-confidence and low-severity, or low-confidence and critical.

---

### Risk Engine

Risk is **deterministic**. It is never generated by AI. It is calculated by logic.

```
Base Risk
+ Exposure Modifier
+ Misconfiguration Modifier  
+ Known Vulnerability Modifier
+ Correlation Modifier
= Final Risk Score
```

Risk levels: `Informational` · `Low` · `Medium` · `High` · `Critical`

Every risk score is explainable. Users always see the breakdown, not just the label.

---

### Correlation Engine

Findings influence each other. Argus evaluates findings both individually and collectively.

Example:
```
Redis Open         → High (alone)
No Authentication  → High (alone)
Internet Facing    → Medium (alone)

Combined:          → CRITICAL
```

Each Intelligence Library entry defines correlation rules:

```json
{
  "correlation_rules": {
    "amplifies": ["no_authentication", "internet_facing"],
    "requires": [],
    "mitigates": ["firewall_restricted"]
  }
}
```

This is where Argus goes beyond a list of findings and starts reasoning about attack paths.

---

### Explainability Rule

**Every Argus conclusion must show its reasoning.**

❌ Bad:
```
Risk: High
```

✅ Good:
```
Risk: High (7/10)

Reasoning:
  +2  Internet Facing
  +2  Service Exposure  
  +3  Weak Authentication Enabled
  ─────────────────────────────
  7   Total Score
```

Users must always understand why Argus reached a conclusion. This is non-negotiable. Black-box outputs destroy trust.

---

## AI Strategy

AI is a **communicator**, not a decision-maker.

```
Finding
  ↓
Intelligence Library  (owns knowledge)
  ↓
Reasoning Engine      (owns decisions)
  ↓
AI Layer              (owns communication)
  ↓
User
```

The Intelligence Library and Reasoning Engine are deterministic, consistent, and auditable. The AI layer formats and communicates conclusions in natural language — it does not generate them.

**On training a custom model:** Not in V1. The data to train on does not exist yet. After Argus accumulates thousands of findings, reasoning decisions, and user interactions, fine-tuning becomes worth considering. Building AI before building knowledge is building backwards.

Effort allocation:
```
Intelligence Library    40%
Reasoning Engine        30%
User Experience         20%
AI Layer                10%
```

---

## Audience System

Users select their role on first use. Argus adapts all explanations, guidance, and recommendations accordingly.

**V1 Options:**
- Student
- Developer  
- Pentester
- Security Professional

Role inference is deliberately excluded from V1. Users switch contexts constantly — a student today is a bug bounty hunter tomorrow. Let the user decide.

---

## Version 1 Scope

### Included
- Subfinder integration
- Httpx integration
- Nmap integration
- Nuclei integration
- Universal Finding Schema
- Intelligence Library (5 services, 4 technologies, 5 vulnerability classes)
- Reasoning Engine
- Confidence Engine
- Risk Engine
- Correlation Engine
- Explainability on all conclusions
- Audience-aware guidance (4 personas)
- Intelligence Cards UI
- Learning Mode

### Explicitly Excluded
- Threat intelligence feeds
- Dark web intelligence
- Graph relationships
- Asset monitoring / historical scans
- CVE enrichment APIs
- Custom AI models
- Team workspaces

---

## Version 2 Scope

After V1 is proven and used:

- CVE intelligence enrichment (NVD, vendor advisories)
- Relationship graphs
- Asset tracking and historical comparison
- Threat intelligence integration
- Knowledge library expansion
- Team workspaces
- Advanced reporting and exports (STIX, PDF, CSV)
- Security trend analysis across scans

---

## What Argus Will Never Become

This is as important as what Argus will become.

Argus is not:
- ❌ A dark web crawler
- ❌ A malware sandbox
- ❌ A SIEM or EDR
- ❌ A threat actor tracker
- ❌ An exploit framework
- ❌ A Metasploit replacement
- ❌ Another scanner dashboard

Every proposed feature must pass this test:

> Does it help users **Discover → Reason → Understand → Act → Learn?**
>
> If yes → consider it.  
> If no → reject it.

---

## Product Principles

1. **Understanding over Data** — a user who understands one finding is better served than a user who receives a hundred they cannot interpret.

2. **Guidance over Information** — always answer "what next", not just "what was found."

3. **Explainability over Black Boxes** — every conclusion shows its reasoning. Always.

4. **Knowledge over Hype** — the Intelligence Library beats a prompt every time for consistency and trust.

5. **Reasoning over Raw AI** — deterministic logic owns decisions. AI owns communication.

6. **Learning While Doing** — every scan is also a learning opportunity. Never waste it.

7. **Every Finding Must Answer Three Questions:**
   - What is it?
   - Why does it matter?
   - What should I do next?

---

## Success Metric

A successful Argus user finishes a scan and immediately knows:

- What was discovered
- Why each finding matters
- What to prioritize
- What to do next
- What to learn next

**No confusion. No raw data dumps. No unanswered questions.**

Argus turns raw findings into understanding, understanding into decisions, and decisions into action.

---

## Development Roadmap

### Now — Sprint 1
- [ ] Design `argus-intelligence/services/ssh.json` — first Intelligence Library entry
- [ ] Validate entry structure against all four persona guidance fields
- [ ] Write entries for remaining 4 V1 services (HTTP, HTTPS, MySQL, Redis)

### Sprint 2
- [ ] Implement Universal Finding Schema in backend
- [ ] Build Reasoning Engine with deterministic risk scoring
- [ ] Build Confidence Engine

### Sprint 3
- [ ] Build Intelligence Card UI component
- [ ] Implement Explainability breakdown display
- [ ] Build Audience selector and guidance rendering

### Sprint 4
- [ ] Build Correlation Engine
- [ ] Connect all findings through correlation rules
- [ ] End-to-end test: scan → intelligence card → guidance

### Sprint 5+
- [ ] Add Technology entries to Intelligence Library
- [ ] Add Vulnerability class entries
- [ ] Nuclei findings → Universal Finding Schema mapping

---

*Argus Sentinel — Version 1.0 Vision Lock*  
*Planning: Complete. Architecture: Defined. Building: Beginning.*
