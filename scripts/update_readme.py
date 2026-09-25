"""Refresh the auto-generated "recently active" block in README.md.

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


def main():
    repos = fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed")
    repos = [r for r in repos if not r["fork"] and not r["archived"] and r["name"] != USER]
    repos.sort(key=lambda r: r["pushed_at"], reverse=True)

    with open(README, encoding="utf-8") as f:
        content = f.read()
    block = f"{START}\n{render(repos[:LIMIT])}\n{END}"
    updated = re.sub(f"{re.escape(START)}.*?{re.escape(END)}", lambda _: block, content, flags=re.S)
    with open(README, "w", encoding="utf-8") as f:
        f.write(updated)


if __name__ == "__main__":
    main()
