import json
import os
import sys
from pathlib import Path

# Ensure emoji and Unicode print correctly on Windows terminals
sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ── Constants ────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
CSV_PATH        = BASE_DIR / "data" / "lead.csv"
OUTPUT_PATH     = BASE_DIR / "outputs" / "results.csv"
MODEL           = "gemini-2.5-flash"
SCORE_THRESHOLD = 5

# ── Gemini configs (built once, reused every iteration) ──────────────────────
RESEARCH_CONFIG = types.GenerateContentConfig(
    system_instruction=(
        "You are a corporate researcher. Return a valid JSON with a 2-sentence "
        "corporate summary. Format: {\"summary\": \"...\"}"
    ),
    response_mime_type="application/json",
)

EMAIL_CONFIG = types.GenerateContentConfig(
    system_instruction=(
        "You are an elite B2B copywriter. Write a 3-sentence casual email. "
        "Avoid AI clichés like 'delve' or 'hope this finds you well'."
    ),
)

# ── Setup ────────────────────────────────────────────────────────────────────
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("⚠️ GEMINI_API_KEY not found! Please check your .env file.")

client = genai.Client(api_key=api_key)


# ── Lead Scoring (Deterministic Gate) ────────────────────────────────────────
def score_lead(row: pd.Series) -> dict:
    """Apply firmographic scoring rules. Returns score, qualification flag, and reasons."""
    score = 0
    reasons: list[str] = []

    if "manufacturing" in str(row.get("Industry", "")).strip().lower():
        score += 5
        reasons.append("Manufacturing Sector (+5)")

    try:
        employees = int(row.get("Employee Count", 0))
        if employees > 200:
            score += 5
            reasons.append("Enterprise Headcount > 200 (+5)")
        elif employees > 50:
            score += 3
            reasons.append("Mid-Market Headcount > 50 (+3)")
    except (ValueError, TypeError):
        pass

    return {
        "score": score,
        "is_qualified": score >= SCORE_THRESHOLD,
        "reasons": ", ".join(reasons),
    }


# ── Gemini Agent Calls ────────────────────────────────────────────────────────
def research_company(industry: str, employee_count) -> str:
    """Call Research Agent. Returns a clean text summary."""
    prompt = f"Analyze a {industry} company with {employee_count} employees."
    response = client.models.generate_content(
        model=MODEL, contents=prompt, config=RESEARCH_CONFIG
    )
    try:
        data = json.loads(response.text)
        return data.get("summary", response.text)
    except (json.JSONDecodeError, AttributeError):
        return response.text or ""


def write_outreach_email(contact: str, company: str, summary: str) -> str:
    """Call Email Agent. Returns a ready-to-send cold email string."""
    prompt = (
        f"Write an outbound email to {contact} at {company} "
        f"using this company summary: {summary}"
    )
    response = client.models.generate_content(
        model=MODEL, contents=prompt, config=EMAIL_CONFIG
    )
    return response.text.strip() if response.text else ""


# ── Main Pipeline Orchestrator ────────────────────────────────────────────────
def run_b2b_agent_pipeline() -> None:
    print("🚀 Starting B2B Lead Qualification Agent Workflow...")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)  # auto-create outputs/

    df = pd.read_csv(CSV_PATH)

    # Pre-score all leads; keep only qualified ones — no wasted loop iterations
    df["_eval"] = df.apply(score_lead, axis=1)
    qualified = df[df["_eval"].apply(lambda e: e["is_qualified"])].copy()
    skipped   = len(df) - len(qualified)

    if skipped:
        print(f"⏭️  {skipped} lead(s) skipped below score threshold of {SCORE_THRESHOLD}.")

    processed_leads: list[dict] = []

    for _, row in qualified.iterrows():
        company = row["Company Name"]
        evaluation = row["_eval"]
        print(f"\n✅ Evaluating: {company} | Score: {evaluation['score']} | Activating Gemini Agents...")

        try:
            summary = research_company(row["Industry"], row["Employee Count"])
            email   = write_outreach_email(row["Target Contact Name"], company, summary)
        except Exception as exc:
            print(f"  ⚠️  Gemini API error for {company}: {exc}. Skipping.")
            continue

        processed_leads.append({
            "Company Name":           company,
            "Contact Person":         row["Target Contact Name"],
            "Score Reasons":          evaluation["reasons"],
            "Gemini Research Summary": summary,       # Much cleaner in Excel/CSV!
            "Generated Outreach Email": email,
        })

    if processed_leads:
        pd.DataFrame(processed_leads).to_csv(OUTPUT_PATH, index=False)
        print(f"\n🏁 Workflow complete! Results written to: {OUTPUT_PATH}")
    else:
        print(f"\n🏁 Workflow complete, but no leads met the qualification threshold score of {SCORE_THRESHOLD}.")


if __name__ == "__main__":
    run_b2b_agent_pipeline()
