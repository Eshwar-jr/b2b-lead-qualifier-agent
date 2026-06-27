# 🤖 B2B Lead Qualifier — AI-Powered Sales Automation Agent

> **Automatically score, research, and write personalized cold outreach emails for high-value B2B leads using Google Gemini 2.5 Flash.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-orange?logo=google)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)]()

---

## 📌 Overview

The **B2B Lead Qualifier** is an agentic AI pipeline that eliminates hours of manual sales prospecting. It takes a raw CSV of company leads, applies a deterministic firmographic scoring engine to filter out low-quality prospects, and then unleashes two specialized Gemini AI agents — one to research each company and one to write a tailored outbound email — all in a single automated workflow.

**The result:** A clean, enriched CSV containing only your best leads, complete with AI-generated research summaries and ready-to-send cold emails.

---

## 🎯 Problem Statement

B2B sales teams waste enormous time manually:
1. Sifting through hundreds of raw leads to find qualified prospects
2. Researching each company's profile before outreach
3. Writing personalized cold emails from scratch for every contact

This project solves all three bottlenecks with a single Python script powered by Google's Gemini API.

---

## 🏗️ Architecture & Agent Pipeline

The system follows a **3-stage agentic pipeline**:

```
📥 Input CSV (leads)
       │
       ▼
┌─────────────────────────────┐
│  Stage 1: Scoring Gate      │  ← Deterministic Python logic
│  (Firmographic Filter)      │    Industry + Employee Count scoring
└──────────────┬──────────────┘
               │ Score ≥ 5 only
               ▼
┌─────────────────────────────┐
│  Stage 2: Research Agent    │  ← Gemini 2.5 Flash
│  (Corporate Intelligence)   │    Structured JSON output
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  Stage 3: Email Agent       │  ← Gemini 2.5 Flash
│  (Outreach Copywriter)      │    Personalized cold email
└──────────────┬──────────────┘
               │
               ▼
📤 Output CSV (enriched, qualified leads)
```

### Scoring Logic

| Signal | Points |
|---|---|
| Manufacturing industry | +5 |
| Employee count > 200 (Enterprise) | +5 |
| Employee count > 50 (Mid-Market) | +3 |
| **Qualification threshold** | **≥ 5** |

---

## ✨ Features

- **🔍 Smart Lead Filtering** — Deterministic firmographic scoring gates prevent wasting AI tokens on unqualified leads.
- **🧠 AI Research Agent** — Gemini synthesizes a concise corporate profile for each qualified lead, returned as structured JSON.
- **✉️ AI Email Copywriter** — Generates conversion-focused, 3-sentence personalized cold emails. No AI clichés.
- **📊 Structured Output** — Clean CSV export ready for Excel, CRM import, or further automation.
- **🔐 Secure API Key Handling** — Credentials loaded from `.env` file; never hardcoded.

---

## 🗂️ Project Structure

```
B2B-lead-qualifier/
├── 📄 main.py              # Core agent pipeline
├── 📁 data/
│   └── lead.csv            # Input: raw leads CSV
├── 📁 outputs/
│   └── results.csv         # Output: enriched qualified leads
├── 📄 requirements.txt     # Python dependencies
├── 📄 SKILLS.MD            # Agent capability manifest
├── 📄 .env                 # API key (not committed to git)
└── 📄 README.md
```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/B2B-lead-qualifier.git
cd B2B-lead-qualifier
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Your API Key

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

> **Get your free API key:** [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### 4. Prepare Your Leads CSV

Add your leads to `data/lead.csv` with the following columns:

| Column | Description | Example |
|---|---|---|
| `Company Name` | Company name | `Acme Corp` |
| `Website URL` | Company website | `https://acme.com` |
| `Industry` | Industry sector | `manufacturing` |
| `Employee Count` | Number of employees | `250` |
| `Target Contact Name` | Person to email | `Jane Smith` |

**Sample `data/lead.csv`:**

```csv
Company Name,Website URL,Industry,Employee Count,Target Contact Name
Aa manufacturing,https://aamanufacturing.com,manufacturing,100,Tyler
lmt tech,https://lmttech.com,IT services,14,Tom
GT catering,https://gtcatering.com,FMCG,245,Liya
```

### 5. Run the Pipeline

```bash
python main.py
```

---

## 📤 Sample Output

After running, check `outputs/results.csv`:

| Company Name | Contact Person | Score Reasons | Gemini Research Summary | Generated Outreach Email |
|---|---|---|---|---|
| Aa manufacturing | Tyler | Manufacturing Sector (+5), Mid-Market Headcount > 50 (+3) | *AI-generated summary...* | *AI-generated email...* |

> ℹ️ Leads that don't meet the score threshold (e.g., lmt tech with only 14 employees in IT services) are **automatically skipped**, saving API calls.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.9+** | Core runtime |
| **Google Gemini 2.5 Flash** | AI research & copywriting agents |
| **`google-genai` SDK** | Official Gemini API client |
| **Pandas** | CSV ingestion & structured output |
| **python-dotenv** | Secure environment variable management |

---

## 🧠 Key AI/ML Concepts Demonstrated

- **Agentic AI Pipelines** — Chaining multiple AI calls in a structured workflow
- **Prompt Engineering** — System instructions to enforce output format and tone
- **Structured Output** — `response_mime_type="application/json"` for reliable JSON responses
- **Hybrid AI Architecture** — Deterministic pre-filtering + generative AI for efficiency
- **Token Efficiency** — Gate checks prevent unnecessary LLM calls on low-quality leads

---

## ⚠️ Important Notes

- **Hardcoded paths in `main.py`:** The CSV input/output paths currently use absolute Windows paths. Before sharing or running on another machine, update lines 48–49 in `main.py` to use relative paths or environment variables.
- **API Rate Limits:** The free tier of Gemini API has rate limits. Add `time.sleep()` between iterations if processing large datasets.
- **Cost:** Gemini 2.5 Flash is extremely cost-efficient; each lead typically costs a fraction of a cent.

---

## 📈 Potential Extensions

- [ ] Add LinkedIn/Crunchbase enrichment via web scraping
- [ ] Integrate with CRM APIs (HubSpot, Salesforce) for direct lead import
- [ ] Add email validation before outreach generation
- [ ] Build a Streamlit dashboard for non-technical users
- [ ] Support batch processing with async API calls for large datasets

---

## 🙏 Acknowledgements

- Built using the [Google Gemini Developer API](https://ai.google.dev/)
- Inspired by real-world B2B sales automation challenges

---

## 📄 License

This project is open source under the [MIT License](LICENSE).

---

*Made with ❤️ and Gemini AI*
