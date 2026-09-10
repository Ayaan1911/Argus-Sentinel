# Intelligence Library — Field Schema & Consumption Reference

This is the source-of-truth for what fields exist in `argus-intelligence/{services,technologies,vulnerabilities}/*.json`, which are actually required, and — critically — which ones any backend code actually reads versus which are documentation-only. It was written by auditing every one of the 57 entries on file plus every place `backend/app/engines/*.py`, `backend/app/scanners/processor.py`, `backend/app/scanners/httpx.py`, and `backend/app/scanners/nmap.py` read from an intelligence entry, not by reverse-engineering intent from field names.

For the machine-checkable version of this, see `schema.json` and `scripts/validate_intelligence.py`. For a worked example of adding a new entry, see `CONTRIBUTING.md`.

## How an entry gets loaded and matched at all

`backend/app/intelligence/loader.py`'s `IntelligenceLoader` globs every `*.json` file under each of the three category directories and keys it by **the filename without its extension, lowercased** — `services/ssh.json` becomes `loader.data["services"]["ssh"]`. There is no `name`/`id` field inside the JSON that determines this; the filename *is* the key. A malformed file is silently skipped with a logged warning, not a crash — which is exactly why `scripts/validate_intelligence.py` exists as a pytest-wired check, so a bad file fails CI loudly instead of silently vanishing from the library at runtime.

How a real finding gets matched to an entry (`backend/app/scanners/processor.py`'s `FindingProcessor.process`) differs by category, and this matters enormously for whether a new entry you add will ever actually be used:

- **`services/`** — matched directly and only by `raw_data["service"]` (nmap's own reported service name, lowercased) against the loader dict. **Your filename must equal the exact string nmap reports as the service name** for your entry to ever match a real port finding. There is a `generic_port` fallback entry for anything nmap can't identify (`tcpwrapped`, etc.) — that fallback always fires when there's no exact match.
- **`technologies/`** — matched two ways, tried in order: (1) each item in httpx's `-tech-detect` output list (e.g. `"jQuery:3.4.1"` — the library name before the colon, lowercased) against the loader dict; (2) if nothing in the tech list matched, the raw HTML `<title>` httpx captured, lowercased, as an exact match. Falls back to the generic `live_host` entry if neither matches. **The tech-detect list is the more reliable path** — it's Wappalyzer-style fingerprinting of actual software, whereas the page `<title>` is usually a site's own branding (e.g. "OWASP Juice Shop"), not the underlying technology's name, so title-based matching only really works for tools whose default/unconfigured install has a title equal to the product name (Kibana does; most CMS installs don't).
- **`vulnerabilities/`** — matched via each entry's own `nuclei_tags` and `title_keywords` fields (see below) against the nuclei finding's tags and title. This is fully data-driven — **no code change is needed to make a new vulnerability entry matchable**, unlike services/technologies where your filename or the scanner's detected string has to line up.
- **`subdomain`-type findings** always match the single `services/subdomain.json` entry — there's no per-finding matching logic for this type.

## Fields present in every one of the 57 entries (universal, and required by `schema.json`)

| Field | Type | Consumed by |
|---|---|---|
| `description` | string | `processor.py` → `kb_entry.get("description")` becomes the finding's `technical_impact` |
| `audience_guidance` | object, exactly the 5 keys `student`/`developer`/`bug_bounty_hunter`/`pentester`/`security_team` | `processor.py` → copied wholesale into the finding's `audience_guidance`, which is what `FindingDetail.jsx`'s persona switcher reads |
| `learning_resources` | array of URL strings | `processor.py` → finding's `learning_resources` |
| `version` | string, e.g. `"1.0"` | not read by any engine — entry's own schema-version marker, for humans |
| `last_updated` | string, `YYYY-MM-DD` | not read by any engine — for humans/future staleness tooling |
| `reviewed_by` | string, always `"argus-team"` on file today | not read by any engine — for humans |

`schema.json` only requires these six fields, on purpose — see "Two shapes exist" below for why.

## `services/` — the one consistently-shaped category

All 25 files use the same full shape, with these fields present on every one:

`service`, `port` (int), `protocol` (string), `purpose`, `risk_level` (enum: `Informational`/`Low`/`Medium`/`High`/`Critical`), `common_risks` (string array), `misconfigurations` (string array), `attack_patterns` (string array), `real_world_incidents` (string array), `recommended_actions` (string array), `correlation_rules` (object: `amplifies`/`requires`/`mitigates` string arrays), `related_findings` (string array), `mitre_attack` (string array of ATT&CK technique IDs like `"T1110"`), `risk_weight` (number 0–10).

Consumption:
- `risk_weight` → `reasoning.py`'s `calculate_risk()` uses this as the **base score** for `port`/`service`-type findings (`base_score = intelligence_entry.get("risk_weight", 0.0)`). This is the only field from the KB entry that `reasoning.py` reads directly for these types — every other modifier on a port finding (`internet_facing`, `password_auth_enabled`, `outdated_version`, etc.) comes from the scanner's own `raw_data`, not from the KB entry.
- `recommended_actions`, `attack_patterns`, `related_findings`, `audience_guidance`, `description`, `learning_resources` → copied into the finding by `processor.py` as documented above.
- `correlation_rules`, `common_risks`, `misconfigurations`, `real_world_incidents`, `purpose`, `protocol`, `port` → **not read by any backend engine.** `port`/`protocol` are shown in the Intelligence Library browser UI (`Intelligence.jsx`) as a badge next to the entry name; the rest are documentation-only today, visible only if you read the raw JSON or an eventual UI surfaces them. Still worth filling in accurately — they're not dead weight in the sense of being wrong to have, just not yet wired to a scoring decision.
- `mitre_attack` → not read by any engine; documentation for humans, validated by `schema.json` to look like a real technique ID (`T####` or `T####.###`) so at least it can't be garbage.

**Optional**: `min_secure_version` (string, e.g. `"7.4"`) — present on 6 of 25 files. Only consumed by `nmap.py`'s `_is_outdated()`, which checks a **hardcoded** `PRODUCT_KB_MAP` dict mapping an nmap-reported *product* substring (e.g. `"openssh"`) to a `(category, kb_key)` pair. **Adding `min_secure_version` to a new services/ entry does nothing on its own** — `nmap.py`'s `PRODUCT_KB_MAP` must also gain an entry pointing at it, which is a genuine, unavoidable Python change (see CONTRIBUTING.md). This is why this session's new services/ entries (`docker`, `amqp`, `minio`, `memcached`, `smtp`, `imap`, `nfs`, `rsync`) deliberately don't carry `min_secure_version` — none of them represent a single well-documented version floor the way OpenSSH/Apache/MySQL do; they're exposure/misconfiguration risks, not version risks.

## `technologies/` — two shapes exist; this is a real, pre-existing inconsistency

18 files, split across two incompatible shapes from different generation batches. This was discovered during this session's audit and is documented rather than silently retrofitted, since fixing 6 pre-existing files wasn't in scope and `schema.json` had to stay permissive enough not to fail CI on day one.

**Full shape** (11 of 18: `apache`, `nginx`, `tomcat`, `wordpress`, `live_host`, plus this session's `jquery`, `bootstrap`, `kibana`, `jenkins`, `gitlab`, `express`) — identical to the `services/` shape above (`service`, `port`, `protocol`, `risk_level`, `attack_patterns`, `recommended_actions`, `correlation_rules`, `related_findings`, `mitre_attack`, `risk_weight`, etc.), because a `technologies/` entry is matched and consumed by `processor.py` exactly like a `services/` one is (`type == "technology"` reads the same fields as `type in ["port","service"]`, minus `risk_weight` — see below).

**Sparse shape** (7 of 18: `django`, `docker`, `iis`, `kubernetes`, `nodejs`, `php`, plus this session's `laravel`) — only carries `technology`, `type`, `purpose`, `description`, `common_risks`, `mitigations`, `audience_guidance`, `learning_resources`, `version`, `last_updated`, `reviewed_by`. **`mitigations` here is never read by any code** — `processor.py` reads `recommended_actions`, not `mitigations`, so every finding matched to one of these 7 entries gets an empty `recommended_actions` list in the UI even though the entry clearly has equivalent content sitting in `mitigations` under a different key. Same for `attack_patterns`/`related_findings` — absent, so always empty for these matches.

**If you're adding a new technology entry, use the full shape**, even though `schema.json` doesn't strictly require it — the sparse shape is a known gap, not a template to copy.

Reasoning-engine specifics for `type == "technology"` findings: `reasoning.py`'s base score is **hardcoded to `3.0`**, regardless of the KB entry's `risk_weight` — technology findings are the one type where the KB entry's `risk_weight` is *not* read at all for scoring (it's read for `port`/`service` only). The actual modifiers applied (`outdated_version` +2.0, `known_vulnerabilities` +1.5, `admin_panel_exposed` +1.0, `waf_detected` −1.0) all come from `raw_data` flags set by the scanners, not from the KB entry directly.

**Optional**: `min_secure_version` — present on 3 of 18 (`apache`, `nginx`, `php`, plus this session's `jquery`, `bootstrap`). Two *separate* consumers exist for this field depending on how the technology is detected:
1. **Server products fingerprinted by nmap** (Apache, Nginx, MySQL, etc.) — same `nmap.py` `PRODUCT_KB_MAP` mechanism as services/, described above.
2. **Client-side libraries fingerprinted by httpx's tech-detect** (jQuery, Bootstrap) — a *different*, newer mechanism added this session: `httpx.py`'s `_detect_outdated_tech()` parses the version embedded in httpx's own tech-detect string (e.g. `"jQuery:3.4.1"` → name `jquery`, version `3.4.1`) and compares it directly against `loader.data["technologies"][name]["min_secure_version"]` — **no hardcoded map needed for this path**, since httpx's tech list already carries the technology name that matches the filename convention. This is genuinely lower-friction than the nmap path: add `min_secure_version` to a technologies/ entry whose filename matches what httpx's tech-detect calls it, and it's live immediately.

## `vulnerabilities/` — also two historical shapes, now unified by the new matching fields

14 files. Two legacy shapes existed (one with `vulnerability_class`/`severity`/`impact`/`remediation`, one copy-pasted from the services/ template with `service`/`port`/`protocol`/`risk_level` — fields that don't really make conceptual sense for a vulnerability *class* like XSS, a leftover of mechanical generation). Neither `severity`, `impact`, `remediation`, `vulnerability_class`, nor the copy-pasted `port`/`protocol`/`service`/`purpose` fields are read by any scoring engine — a finding's actual severity always comes from the scanner's own `raw_data`, never from the KB entry, for `type == "vulnerability"`. `vulnerability_class` **is** read by the frontend (`Intelligence.jsx`) as the entry's display name, and by the search endpoint (`GET /intelligence/search`) as a searchable field — both fixed this session (previously only checked `service`/`technology`, so half the vulnerability entries showed no name in the UI). The 5 entries that only had `remediation` (not `recommended_actions`) had that content copied into `recommended_actions` too this session, since `remediation` itself is never read by `processor.py` — `remediation` is kept alongside it for backward compatibility/human readability, but `recommended_actions` is what actually reaches a finding.

**What every entry should have, and what actually matters functionally:**

| Field | Type | Consumed by |
|---|---|---|
| `nuclei_tags` | string array | `processor.py`'s `_match_vuln_entry()` — the primary matching signal. The entry with the **most overlapping tags** against the finding's own nuclei tags wins, so a generic shared tag like `"exposure"` (present on 7+ entries) doesn't cause ambiguous matches when a finding also carries a more specific tag. |
| `title_keywords` | string array | Same function, second-pass fallback — substring match against the finding's title if no tag overlap was found at all. |
| `affected_technologies` | string array of lowercase tech names | `httpx.py`'s `_detect_known_vulnerabilities()` — checked generically against httpx's detected tech list on **every** vulnerability entry (not just the one that matched via tags/keywords) to set the `known_vulnerabilities` flag on `technology`-type findings. This is the one vulnerabilities/ field that's fully wired with zero per-entry code. |
| `recommended_actions` | string array | `processor.py` → finding's `recommended_actions` |
| `attack_patterns` | string array | `processor.py` → finding's `attack_patterns`, and a small confidence boost in `confidence.py` if `raw_data["attack_pattern"]` (singular — not currently ever set by any scanner) matches an entry in this list |
| `related_findings` | string array | `processor.py` → finding's `related_findings` |

`nuclei_tags`/`title_keywords` were **added to all 10 pre-existing vulnerability entries this session** (not just the 4 new ones) as part of replacing `processor.py`'s old hardcoded tag-map with this data-driven lookup — five of those ten (`directory_listing`, `exposed_admin_panel`, `exposed_api_docs`, `info_disclosure_debug`, `missing_security_headers`) had no matching logic pointing at them *at all* before this session, despite having full JSON content; real juice-shop scans were repeatedly hitting nuclei findings like "HTTP Missing Security Headers" and "Public Swagger API - Detect" that should have matched these entries and never did. This is now fixed and covered by `backend/tests/test_processor_vuln_matching.py`.

## Enums

- `risk_level` / `severity`: `Informational` | `Low` | `Medium` | `High` | `Critical` — matches the 5-tier scale used everywhere else in the app (`reasoning.py`'s `_get_risk_level()`, `SeverityBadge.jsx`), not a 4-tier one.
- `correlation_rules`: always exactly the 3 keys `amplifies`/`requires`/`mitigates`, each a string array. Note: `requires` is present on every entry that has `correlation_rules` at all but nothing in `correlation.py` currently reads it — it's aspirational/documentation today, same status as `misconfigurations`/`common_risks` above.

## What's genuinely optional versus what should always be filled in

`schema.json` only *requires* the 6 universal fields, because that's the actual common denominator across all 57 existing files and making it stricter would fail validation on the pre-existing sparse-shape files without retrofitting them (out of scope for this session — see above). But "passes the schema" and "is a useful, non-padding entry" are different bars. Per `CONTRIBUTING.md`: a new entry should always include `recommended_actions`, `attack_patterns`/`nuclei_tags`+`title_keywords` (as applicable to its category), and `risk_weight` — omitting these doesn't fail validation, but it does mean the entry behaves like the 6 sparse legacy files above: present in the library, browsable in the UI, but functionally inert for scoring/matching.
