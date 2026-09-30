# ConstructIQ

**AI-assisted blueprint review and construction material takeoff.** ConstructIQ extracts structured information from architectural drawings, applies configurable material rules and prices, and compares estimated quantities with site-log consumption.

> ConstructIQ is an early-stage prototype. AI-extracted measurements and all estimates must be reviewed by a qualified construction professional before being used for procurement, engineering, or financial decisions.

**Live demo:** Not deployed yet.

## What It Does

- Accepts blueprint PDFs and images, or a structured JSON extraction.
- Uses Google Gemini to extract rooms, visible dimensions, doors, windows, and supported building elements from PDFs and images.
- Validates structured extraction data with Pydantic.
- Calculates material takeoffs and wastage using deterministic Python rules.
- Loads material prices from CSV and calculates estimated costs.
- Parses simple text construction logs and compares actual material use with planned quantities.
- Displays results in Streamlit and exports JSON or Excel reports.

AI interprets documents; Python performs the quantity, wastage, costing, and variance calculations. Gemini extraction requires a valid API key. Structured JSON input can be used without making an AI request.

## Current Scope and Limitations

This is a demonstration MVP, not a complete quantity-surveying platform. Current takeoff rules cover block-wall area and floor area, mapped to example material consumption rates. The included construction-log parser handles simple line-based material records; it is not a general-purpose parser for arbitrary reports or invoices.

Projects are held in Streamlit session state and are not stored in a persistent database. Authentication, multi-user project access, background processing, and permanent document storage are not implemented. AI extraction can be wrong or incomplete, and model results require human review. The example material rates and prices are assumptions, not universal standards or current market quotations.

## Quick Start

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set your local `.env` values:

```dotenv
AI_PROVIDER=gemini
MODEL_NAME=gemini-2.5-flash
GEMINI_FALLBACK_MODEL=gemini-2.5-flash-lite
GEMINI_API_KEY=your_gemini_api_key
```

Do not commit `.env` or share its API key. To start the app:

```powershell
python -m streamlit run app.py
```

Open the URL printed by Streamlit, usually `http://localhost:8501`.

Run the tests with:

```powershell
python -m pytest -q
```

For the full Windows setup and use instructions, see [run.md](run.md).

## Try the App

1. In **Project setup**, enter the project name, currency, wastage, and variance threshold.
2. In **Upload documents**, upload a PDF or image blueprint and click **Process blueprint**. This sends the document to Gemini.
3. Review the extracted fields under **Blueprint analysis** and correct quantities before relying on them.
4. Upload a supported site log and, optionally, a price-book CSV.
5. Check material quantities, costs, variance, and report downloads under **Takeoff and costs**.

For a deterministic test that does not call Gemini, upload a `.json` blueprint matching the example in [run.md](run.md).

### Site-log example

The current parser recognizes simple text in this shape:

```text
Date: 02/09/2026
Activity: Blockwork
Workers: 12
Cement - 8 bags
Blocks - 650 pcs
Sand - 3 m3
```

### Price-book CSV example

```csv
material,unit,unit_price,currency
blocks,pcs,750,NGN
cement,bag,12000,NGN
sand,m3,85000,NGN
tiles,m2,8500,NGN
```

## Configuration and Privacy

For local development, store Gemini credentials in `.env`. For Streamlit Community Cloud, add the same settings through the app's **Secrets** configuration rather than committing `.env`:

```toml
AI_PROVIDER = "gemini"
MODEL_NAME = "gemini-2.5-flash"
GEMINI_FALLBACK_MODEL = "gemini-2.5-flash-lite"
GEMINI_API_KEY = "your_gemini_api_key"
```

If the primary model is temporarily overloaded, ConstructIQ retries the request and then tries the configured fallback model. The fallback setting is optional; it defaults to `gemini-2.5-flash-lite`.

Uploaded blueprint PDFs and images are sent to Google's Gemini API for extraction. Do not upload confidential or sensitive drawings unless you are authorized to share them with that service. Review Google's applicable terms and data handling policies before using real project documents.

## Project Layout

```text
ConstructIQ/
├── app.py                 # Streamlit interface
├── app/                   # Models, extraction, calculations, and reporting
├── tests/                 # Automated tests
├── data/                  # Local sample and processing directories
├── requirements.txt
├── run.md                 # Detailed run instructions
└── technical_overview.md  # Original product and architecture specification
```

The original long-form product and architecture specification is preserved in [technical_overview.md](technical_overview.md).