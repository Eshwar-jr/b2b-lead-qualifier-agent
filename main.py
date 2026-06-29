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
import time

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

def _gemini_generate(contents: str, config):
    """Generate Gemini content with automatic retries on 503 errors."""
    max_retries = 3
    delay = 1
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=MODEL, contents=contents, config=config
            )
        except Exception as exc:
            # Retry on service unavailable / 503 errors
            if attempt < max_retries - 1 and ("503" in str(exc) or "ServiceUnavailable" in str(exc)):
                time.sleep(delay)
                delay *= 2
                continue
            raise


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
def research_company(company: str, website: str, industry: str, employee_count) -> str:
    """Call Research Agent. Returns a clean text summary using detailed prompt."""
    research_prompt = f"""
Research the following company.

Company Name: {company}
Website: {website}
Industry: {industry}
Employee Count: {employee_count}

Return JSON in this format:
{{
    "summary": "A concise business summary mentioning the company name."
}}

Do not use placeholders.
"""
    response = _gemini_generate(research_prompt, RESEARCH_CONFIG)
    try:
        data = json.loads(response.text)
        return data.get("summary", response.text)
    except (json.JSONDecodeError, AttributeError):
        return response.text or ""


def write_outreach_email(row: pd.Series, summary: str) -> str:
    """Call Email Agent. Returns a ready-to-send cold email string using detailed prompt and safety instruction."""
    email_prompt = f"""
You are an expert B2B sales copywriter.

Write a professional cold outreach email using the information below.

Company Name: {row.get('Company Name', '')}
Contact Person: {row.get('Target Contact Name', '')}
Industry: {row.get('Industry', '')}
Employee Count: {row.get('Employee Count', '')}

Research Summary:
{summary}

Instructions:
- Address the recipient by their actual name.
- Mention the company name naturally.
- Mention one relevant insight from the research summary.
- Keep the email to 3 short paragraphs.
- Keep the tone friendly and professional.
- Do NOT use placeholders like [Company Name], [Contact Name], or [Industry].
- Return only the email text.

If any information is unavailable, write naturally.
Never invent placeholders.
"""
    response = _gemini_generate(email_prompt, EMAIL_CONFIG)
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
            summary = research_company(company, row.get('Website', ''), row["Industry"], row["Employee Count"])
            email   = write_outreach_email(row, summary)
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
