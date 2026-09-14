# Contributing an Intelligence Library Entry

Thanks for expanding the library. This is the practical, short version — for the full field-by-field reference (what's required, what's optional, and exactly how each field gets used), see [SCHEMA.md](SCHEMA.md).

## 1. Pick the right folder

| Folder | For | Your filename must be |
|---|---|---|
| `services/` | Things nmap identifies by port/service name (databases, mail, file-sharing, message brokers, raw network protocols) | The exact lowercase string nmap reports as the service name (e.g. nmap reports `redis` → file is `redis.json`) |
| `technologies/` | Web apps/frameworks/libraries httpx fingerprints (CMSs, JS frameworks, dev tools with a web UI) | The exact lowercase name httpx's tech-detect reports (preferred), or the exact lowercase page `<title>` as a fallback |
| `vulnerabilities/` | A vulnerability *class* nuclei's templates commonly flag (not tied to one product) | Anything descriptive — matching here is by `nuclei_tags`/`title_keywords` fields inside the file, not the filename |

If you're not sure what string nmap/httpx will actually report, that's fine — worst case your entry sits in the library unmatched until the string is confirmed. It won't break anything (see step 3).

## 2. Required and recommended fields

**Required by `schema.json`** (every entry, all 3 folders): `description`, `audience_guidance` (all 5 keys: `student`, `developer`, `bug_bounty_hunter`, `pentester`, `security_team`), `learning_resources`, `version`, `last_updated`, `reviewed_by`, and a real `risk_level` (`services`/`technologies`) or `severity` (`vulnerabilities`) — one of the two is mandatory, not optional. **`vulnerabilities/` entries additionally require at least one non-empty `nuclei_tags` or `title_keywords` array** — the validator rejects a vulnerability entry with neither, because without one it can never be matched to a real finding. This is enforced by `schema.json`, not just a style guideline: `python scripts/validate_intelligence.py` fails loudly on any entry missing these, so a "name + description, no real content" placeholder can no longer merge — see the 2026-09 audit in the project's `notes.md` for why this rule exists.

**Strongly recommended, or your entry is technically valid but contributes little beyond guidance text** — see SCHEMA.md for exactly why each of these matters:
- `services/` and `technologies/`: `risk_weight` (0–10), `recommended_actions`, `attack_patterns`, `related_findings`, `correlation_rules` (`amplifies`/`requires`/`mitigates`), `port`, `protocol`.
- `vulnerabilities/`: `recommended_actions`, `attack_patterns`, `affected_technologies` if it's a technology-specific issue.

**Only add `min_secure_version` if you're genuinely confident in the specific floor** (a well-documented CVE fix version, not a guess). It doesn't do anything by itself:
- For an nmap-detected server product, you also need to add an entry to `PRODUCT_KB_MAP` in `backend/app/scanners/nmap.py` — the one place in this project where adding library data *does* require a small Python change.
- For an httpx tech-detect-fingerprinted client-side library, no Python change is needed — just make sure your `technologies/<name>.json` filename matches what httpx's tech-detect calls it.

If you're not confident in a specific version number, skip `min_secure_version` entirely rather than guessing — an entry without it is still useful for everything else (guidance, correlation, matching).

## 3. Validate locally

```bash
python scripts/validate_intelligence.py
```

Fix whatever it points at — it names the exact file and field. This also runs automatically as part of the backend test suite (`cd backend && pytest`), so a bad entry fails CI, not just your local check.

## 4. Worked example: adding a vulnerability entry end to end

Say nuclei has a template category you want covered: exposed `.htpasswd` files.

**a. Create `argus-intelligence/vulnerabilities/exposed_htpasswd.json`:**

```json
{
  "vulnerability_class": "Exposed .htpasswd File",
  "description": "The web server serves the .htpasswd file directly, exposing hashed (and sometimes crackable) HTTP Basic Auth credentials.",
  "severity": "High",
  "recommended_actions": [
    "Block web-server access to .htpasswd and other dotfiles at the config level.",
    "Move authentication files outside the web root entirely."
  ],
  "attack_patterns": [
    "Download the file and attempt to crack any weakly-hashed credentials offline"
  ],
  "audience_guidance": {
    "student": ".htpasswd stores usernames and password hashes for a simple built-in web server login. If it's servable directly, an attacker can download it and try to crack the hashes offline.",
    "developer": "Keep .htpasswd outside the web root, and add an explicit deny rule for it at the server config level as defense in depth.",
    "bug_bounty_hunter": "Check /.htpasswd directly — a low-effort, occasionally high-value find if the hashes are crackable.",
    "pentester": "Download and attempt to crack the hashes offline; report which accounts were recoverable as concrete impact.",
    "security_team": "Scan externally-facing hosts for exposed .htpasswd/.htaccess files as a routine check."
  },
  "learning_resources": [
    "https://owasp.org/www-project-web-security-testing-guide/"
  ],
  "affected_technologies": [],
  "nuclei_tags": ["exposure", "htpasswd"],
  "title_keywords": [".htpasswd", "htpasswd"],
  "version": "1.0",
  "last_updated": "2026-09-11",
  "reviewed_by": "your-name-or-handle"
}
```

**b. Validate it:**

```bash
python scripts/validate_intelligence.py
# Intelligence library validation passed — 52 entries across services, technologies, vulnerabilities.
```

**c. That's it — no Python or React changes needed.** The next time a nuclei finding carries the tag `htpasswd` (or its title contains ".htpasswd"), `processor.py`'s data-driven matching will find this entry automatically, and it'll show up in the Intelligence Library browser in the frontend without any further wiring.

**d. Open a PR** with the new file. If you're confident the file's core content is accurate (the vulnerability class is real, the guidance is sound), that's the whole contribution.
