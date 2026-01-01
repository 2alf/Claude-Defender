# Security Policy


## Reporting Vulnerabilities

Open a PR request with apporpriate title `"[Bug/Vulnerability/Issue]"`

Include: 
- summary/description
- steps to reproduce
- impact/attack chain
- suggested fix (or implemented fix)

Valid reports will be credited in our [hall of fame](https://github.com/2alf/Claude-Defender/blob/main/hallfoffame.md).

---

## Scope

**IMPORTANT:** Please provide POC and/or argument for each vulnerability.

**In Scope:**
- Realistic and well documented evasion techniques
- Silent bypass of change detection
- Remote code execution (Excecuted by Claude Defender)
- Realistic trojanisation of Claude Defender
- XSS (Please check you tested on a `release` binary before reporting)

**Out of Scope:**
- Social engineering (user sees all changes before approval)
- Autostart behavior (that's the feature)
- DoS via crashes (no impact)
- Automated scanner results (without PoC)

---

## Known Issues

We accept fixes or implementations for these.
<br>
Please mind that we do NOT prioritise fixing informative bugs.

| Issue | Triage | Status |
|-------|----------|--------|
| MD5 collision | Low | Planned v1.2 |
| No snapshot integrity checks | Medium | Planned v1.3 |
| TOCTOU race conditions | Informative | Accepted risk |
| Path traversal via Social eng | Informative | Accepted risk |

---

## Threat Model

**Designed to detect:**
- Unauthorized config changes
- Malicious MCP server modifications

**NOT designed to prevent:**
- Attackers with admin/root access
- Physical access attacks
- Supply chain compromises (althought we are open to discussing these and fix them if reasonable)

---

*Last Updated: 1st January 2026*
