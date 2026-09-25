"""Refresh the auto-generated parts of the profile: the "recently active"
block in README.md and the stats card at assets/stats.svg.

Runs in GitHub Actions on a schedule. Reads public repo metadata only;
it never writes to any repository other than this profile repo.
"""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone

USER = "inslot2525-ctrl"
ROOT = os.path.join(os.path.dirname(__file__), "..")
README = os.path.join(ROOT, "README.md")
STATS_SVG = os.path.join(ROOT, "assets", "stats.svg")
START, END = "<!--RECENT:START-->", "<!--RECENT:END-->"
LIMIT = 6

# Used when a repo has no GitHub description set.
FALLBACK = {
    "AI-Operational-Error-Assistant": "AURA-Lite: RAG + OCR troubleshooting copilot grounded in SOPs",
    "IICWMS": "Multi-agent IT workflow monitoring & anomaly detection",
    "LLM--HARNESS": "LLM red-team harness: attack variants, scoring, hardening",
    "Tokeniser": "TokenWise: agentic prompt optimizer that cuts 40-60% tokens",
    "ORCA-Marine-system": "8-agent marine intelligence platform (SIH 2025, ISRO)",
    "FRECTION": "Fraud-ring detection with GNNs + graph analytics",
    "EyesUp": "On-device voice copilot for gig drivers (iQOO Hackathon 2026)",
    "Rivalyze": "Competitive-intel agent: 8 parallel searches into one brief",
    "STATMIND-AI": "Upload a CSV, get stats, ML models and AI insights",
    "SABOT": "RAG sales-intelligence assistant with lead capture",
    "Servician-": "RAG service bot that answers from your docs",
    "MeetFlow": "Meeting transcripts to structured tasks with DeBERTa",
    "LANGGRAPH_AGENTS": "LangGraph agent experiments & patterns",
    "NIFTY_FIFTY_LOG_REG": "NIFTY 50 direction prediction with logistic regression",
    "cpu-scheduling-food-simulator": "CPU scheduling algorithms explained with a restaurant kitchen",
}


def fetch(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def ago(ts):
    delta = datetime.now(timezone.utc) - datetime.fromisoformat(ts.replace("Z", "+00:00"))
    days = delta.days
    if days == 0:
        hours = delta.seconds // 3600
        return "just now" if hours == 0 else f"{hours}h ago"
    if days < 30:
        return f"{days}d ago"
    if days < 365:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


def render(repos):
    rows = ["| project | what it is | stack | last push |", "|---|---|---|---|"]
    for r in repos:
        desc = r["description"] or FALLBACK.get(r["name"], "")
        lang = f"`{r['language']}`" if r["language"] else ""
        rows.append(f"| [**{r['name']}**]({r['html_url']}) | {desc} | {lang} | {ago(r['pushed_at'])} |")
    return "\n".join(rows)


LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "Jupyter Notebook": "#DA5B0B", "CSS": "#663399", "HTML": "#e34c26",
    "Shell": "#89e051", "PowerShell": "#012456",
}


def language_shares(repos):
    # Each repo counts equally (its byte fractions sum to 1), so one repo with
    # a vendored folder can't drown out the rest.
    totals = {}
    for r in repos:
        langs = fetch(r["languages_url"])
        size = sum(langs.values())
        for name, n in langs.items():
            totals[name] = totals.get(name, 0) + n / size
    total = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    return [(name, share / total) for name, share in ranked]


def render_stats(user, repos, langs):
    stars = sum(r["stargazers_count"] for r in repos)
    tiles = [
        ("repos shipped", len(repos)),
        ("stars earned", stars),
        ("followers", user["followers"]),
        ("languages used", len(langs)),
    ]
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="820" height="210" viewBox="0 0 820 210">',
        "<style>",
        ".t{font:600 13px 'Segoe UI',Ubuntu,Arial,sans-serif;fill:#8b949e;letter-spacing:1px}",
        ".n{font:800 30px 'Segoe UI',Ubuntu,Arial,sans-serif;fill:#e6edf3}",
        ".h{font:700 15px 'Segoe UI',Ubuntu,Arial,sans-serif;fill:#22d3ee;letter-spacing:2px}",
        ".l{font:500 12px 'Segoe UI',Ubuntu,Arial,sans-serif;fill:#c9d1d9}",
        ".tile{animation:up .8s ease-out both}",
        ".bar{animation:grow 1.4s ease-out both;transform-box:fill-box;transform-origin:left}",
        "@keyframes up{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}",
        "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}",
        "</style>",
        '<rect width="820" height="210" rx="14" fill="#0d1117" stroke="#21262d"/>',
        '<text class="h" x="28" y="36">GITHUB PULSE</text>',
    ]
    for i, (label, value) in enumerate(tiles):
        x = 28 + i * 196
        out.append(
            f'<g class="tile" style="animation-delay:{i * 0.12:.2f}s">'
            f'<rect x="{x}" y="52" width="180" height="70" rx="10" fill="#161b22"/>'
            f'<text class="n" x="{x + 16}" y="90">{value}</text>'
            f'<text class="t" x="{x + 16}" y="110">{label.upper()}</text></g>'
        )
    out.append('<text class="t" x="28" y="150">LANGUAGES ACROSS PROJECTS</text>')
    x = 28.0
    langs = langs[:6]
    for i, (name, share) in enumerate(langs):
        w = 764 * share
        color = LANG_COLORS.get(name, "#8b949e")
        out.append(
            f'<rect class="bar" style="animation-delay:{0.3 + i * 0.1:.2f}s" x="{x:.1f}" y="160" '
            f'width="{max(w - 2, 1):.1f}" height="10" rx="3" fill="{color}"/>'
        )
        x += w
    lx = 28
    for name, share in langs:
        color = LANG_COLORS.get(name, "#8b949e")
        label = f"{name} {share * 100:.0f}%"
        out.append(f'<circle cx="{lx + 5}" cy="189" r="5" fill="{color}"/>'
                   f'<text class="l" x="{lx + 15}" y="193">{label}</text>')
        lx += 22 + len(label) * 7
    out.append("</svg>")
    return "\n".join(out)


def main():
    repos = fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed")
    repos = [r for r in repos if not r["fork"] and not r["archived"] and r["name"] != USER]
    repos.sort(key=lambda r: r["pushed_at"], reverse=True)

    user = fetch(f"https://api.github.com/users/{USER}")
    with open(STATS_SVG, "w", encoding="utf-8") as f:
        f.write(render_stats(user, repos, language_shares(repos)))

    with open(README, encoding="utf-8") as f:
        content = f.read()
    block = f"{START}\n{render(repos[:LIMIT])}\n{END}"
    updated = re.sub(f"{re.escape(START)}.*?{re.escape(END)}", lambda _: block, content, flags=re.S)
    with open(README, "w", encoding="utf-8") as f:
        f.write(updated)


if __name__ == "__main__":
    main()
